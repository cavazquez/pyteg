"""Regresiones deterministas del serializador de comandos de juego."""

from __future__ import annotations

import threading
import unittest
from typing import TYPE_CHECKING, Any, cast
from unittest.mock import patch

from pyteg.server.juego.command_executor import GameCommandExecutor

if TYPE_CHECKING:
    from pyteg.protocols import IClientProtocol


class _FakeEstado:
    """Estado mínimo de una partida activa."""

    def es_jugando(self) -> bool:
        """Indica que el juego está en curso.

        Returns:
            Siempre ``True`` para esta partida de prueba.

        """
        return True


class _FakeTurno:
    """Turno mínimo con un pool propio de unidades."""

    def __init__(self, jugador: int, unidades: int = 5) -> None:
        """Inicializa el turno del jugador indicado."""
        self._jugador = jugador
        self.unidades = unidades

    def jugador_actual(self) -> int:
        """Devuelve el jugador de este turno.

        Returns:
            Identificador del jugador activo.

        """
        return self._jugador

    def usar_unidad(self) -> None:
        """Consume una unidad del pool de este turno."""
        self.unidades -= 1


class _FakeGame:
    """Juego de dos turnos para probar orden y generación."""

    def __init__(self) -> None:
        """Inicializa dos turnos consecutivos."""
        self.turnos = [_FakeTurno(1), _FakeTurno(2)]
        self.indice = 0
        self.finalizaciones = 0

    def empezo(self) -> bool:
        """Indica que el juego está activo.

        Returns:
            Siempre ``True`` para esta partida de prueba.

        """
        return True

    def turno_actual(self) -> _FakeTurno:
        """Devuelve el turno actual.

        Returns:
            Turno correspondiente al índice activo.

        """
        return self.turnos[self.indice]

    def id_turno_actual(self) -> int:
        """Devuelve el índice del turno actual.

        Returns:
            Índice del turno activo.

        """
        return self.indice

    def num_ronda(self) -> int:
        """Devuelve una ronda fija para el caso de prueba.

        Returns:
            El número de ronda fijo.

        """
        return 1

    def limpiar_elegibilidad_reclamar(self) -> None:
        """No necesita limpieza para esta regresión."""

    def finalizar_turno(self) -> None:
        """Avanza exactamente al siguiente turno disponible."""
        self.finalizaciones += 1
        self.indice = min(self.indice + 1, len(self.turnos) - 1)


class _FakeServer:
    """Servidor mínimo consumido por ``GameCommandExecutor``."""

    def __init__(self) -> None:
        """Inicializa estado, juego y señales de observación."""
        self.estado = _FakeEstado()
        self.game = _FakeGame()
        self.turno_enviado = threading.Event()
        self.mapa_enviado = threading.Event()
        self.revision = 0
        self.snapshots = 0

    def state_revision(self) -> int:
        """Devuelve la revisión pública del doble.

        Returns:
            Revisión pública actual.

        """
        return self.revision

    def bump_state_revision(self) -> int:
        """Avanza la revisión pública del doble.

        Returns:
            Nueva revisión pública.

        """
        self.revision += 1
        return self.revision

    def enviar_snapshot(self) -> None:
        """Cuenta snapshots difundidos por el ejecutor."""
        self.snapshots += 1

    def enviar_turno_actual(self) -> None:
        """Registra la difusión del nuevo turno."""
        self.turno_enviado.set()

    def enviar_mapa(self) -> None:
        """Registra la difusión del mapa actualizado."""
        self.mapa_enviado.set()


class _FakeTransmisor:
    """Transmisor mínimo para observar resultados y errores del executor."""

    def __init__(self) -> None:
        """Inicializa colecciones de mensajes enviados."""
        self.command_results: list[dict[str, Any]] = []
        self.errors: list[tuple[str, str]] = []

    def enviar_resultado_comando(self, **result: Any) -> None:
        """Guarda un resultado de comando enviado."""
        self.command_results.append(dict(result))

    def enviar_error(self, error_type: str, message: str) -> None:
        """Guarda un error de protocolo enviado."""
        self.errors.append((error_type, message))


class _FakeClient:
    """Cliente mínimo para ejecutar la tarea bloqueada."""

    def __init__(self, server: _FakeServer) -> None:
        """Asocia el cliente al servidor de prueba."""
        self.server = server
        self.transmisor = _FakeTransmisor()
        self._command_results: dict[str, dict[str, Any]] = {}
        self._command_payloads: dict[str, dict[str, Any]] = {}

    def userid(self) -> int:
        """Devuelve un id estable usado sólo por el logger.

        Returns:
            Identificador fijo del cliente de prueba.

        """
        return 1

    def command_result(self, command_id: str) -> dict[str, Any] | None:
        """Devuelve una copia del resultado cacheado.

        Returns:
            Resultado cacheado o ``None`` si no existe.

        """
        result = self._command_results.get(command_id)
        return None if result is None else dict(result)

    def command_payload(self, command_id: str) -> dict[str, Any] | None:
        """Devuelve una copia del payload cacheado.

        Returns:
            Payload cacheado o ``None`` si no existe.

        """
        payload = self._command_payloads.get(command_id)
        return None if payload is None else dict(payload)

    def remember_command_result(
        self,
        command_id: str,
        result: dict[str, Any],
        payload: dict[str, Any] | None = None,
    ) -> None:
        """Guarda resultado y payload para simular reintentos."""
        self._command_results[command_id] = dict(result)
        if payload is not None:
            self._command_payloads[command_id] = {
                key: value for key, value in payload.items() if key != "command_id"
            }


class _BlockingPlacementTask:
    """Reproduce una acción pausada después de validar el turno."""

    def __init__(self, validated: threading.Event, release: threading.Event) -> None:
        """Configura las barreras de la carrera reproducida."""
        self._validated = validated
        self._release = release
        self.validated_player: int | None = None

    def run(self, client: _FakeClient) -> bool:
        """Valida, se pausa y consume una unidad del turno que validó.

        Returns:
            ``True`` cuando la tarea consume la unidad validada.

        Raises:
            AssertionError: Si el test no libera la tarea bloqueada.

        """
        turno = client.server.game.turno_actual()
        self.validated_player = turno.jugador_actual()
        self._validated.set()
        if not self._release.wait(timeout=2.0):
            msg = "La tarea bloqueada no fue liberada"
            raise AssertionError(msg)
        turno.usar_unidad()
        return True


class _BarrierTask:
    """Marca que todos los elementos FIFO anteriores ya se procesaron."""

    def __init__(self, completed: threading.Event) -> None:
        """Guarda la señal de finalización."""
        self._completed = completed

    def run(self, _: object) -> bool:
        """Señala que llegó al final de la cola.

        Returns:
            Siempre ``True`` para representar una tarea aceptada.

        """
        self._completed.set()
        return True


class _RejectingTask:
    """Tarea falsa que representa un comando rechazado sin mutación."""

    def run(self, _: object) -> bool:
        """Devuelve rechazo para verificar que no se publica revisión.

        Returns:
            Siempre ``False``.

        """
        return False


class TestGameCommandExecutor(unittest.TestCase):
    """El executor conserva atomicidad y descarta timers vencidos obsoletos."""

    def setUp(self) -> None:
        """Crea un ejecutor activo y lo programa para limpieza."""
        self.server = _FakeServer()
        self.client = _FakeClient(self.server)
        self.executor = GameCommandExecutor(self.server)
        self.executor.start()
        self.addCleanup(self.executor.stop)

    def test_action_and_timeout_cannot_consume_the_next_players_pool(self) -> None:
        """Una expiración espera a la acción que ya validó el turno actual."""
        validated = threading.Event()
        release = threading.Event()
        task = _BlockingPlacementTask(validated, release)

        with patch(
            "pyteg.server.juego.command_executor.ServerTaskManager.msg_to_task",
            return_value=task,
        ):
            self.executor.enqueue_command(
                cast("IClientProtocol", self.client),
                {"mensaje": "agregar_unidad", "command_id": "placement-1"},
            )
            self.assertTrue(validated.wait(timeout=1.0), "La acción no se validó")
            snapshot = self.executor.turn_snapshot()
            self.assertIsNotNone(snapshot, "No se publicó el turno inicial")
            if snapshot is None:
                return

            self.executor.enqueue_turn_expired(snapshot[1])
            release.set()

            self.assertTrue(
                self.server.turno_enviado.wait(timeout=1.0),
                "El vencimiento no se procesó después de la acción",
            )

        self.assertEqual(task.validated_player, 1)
        self.assertEqual(self.server.game.turnos[0].unidades, 4)
        self.assertEqual(self.server.game.turnos[1].unidades, 5)
        self.assertEqual(self.server.game.finalizaciones, 1)

    def test_stale_timeout_is_discarded_after_turn_generation_changes(self) -> None:
        """Un timer viejo no puede avanzar dos veces el mismo estado."""
        snapshot = self.executor.turn_snapshot()
        self.assertIsNotNone(snapshot, "No se publicó el turno inicial")
        if snapshot is None:
            return

        self.executor.enqueue_turn_expired(snapshot[1])
        self.assertTrue(
            self.server.turno_enviado.wait(timeout=1.0),
            "El vencimiento vigente no avanzó el turno",
        )
        self.server.turno_enviado.clear()

        completed = threading.Event()
        with patch(
            "pyteg.server.juego.command_executor.ServerTaskManager.msg_to_task",
            return_value=_BarrierTask(completed),
        ):
            self.executor.enqueue_turn_expired(snapshot[1])
            self.executor.enqueue_command(
                cast("IClientProtocol", self.client), {"mensaje": "chat", "msg": "x"}
            )
            self.assertTrue(
                completed.wait(timeout=1.0), "La cola no llegó a la barrera"
            )

        self.assertFalse(self.server.turno_enviado.is_set())
        self.assertEqual(self.server.game.finalizaciones, 1)

    def test_accepted_command_with_id_publishes_one_revision(self) -> None:
        """Una mutación identificada publica una única revisión."""
        completed = threading.Event()
        barrier = threading.Event()
        with patch(
            "pyteg.server.juego.command_executor.ServerTaskManager.msg_to_task",
            side_effect=[_BarrierTask(completed), _BarrierTask(barrier)],
        ):
            self.executor.enqueue_command(
                cast("IClientProtocol", self.client),
                {"mensaje": "agregar_unidad", "command_id": "placement-2"},
            )
            self.assertTrue(completed.wait(timeout=1.0))
            self.executor.enqueue_command(
                cast("IClientProtocol", self.client),
                {"mensaje": "chat", "msg": "barrera"},
            )
            self.assertTrue(barrier.wait(timeout=1.0))

        self.assertEqual(self.server.revision, 1)
        self.assertEqual(self.server.snapshots, 1)

    def test_mutation_without_id_is_rejected_before_building_task(self) -> None:
        """Una mutación sin ID no construye tarea ni publica revisión."""
        completed = threading.Event()
        with patch(
            "pyteg.server.juego.command_executor.ServerTaskManager.msg_to_task",
            return_value=_BarrierTask(completed),
        ) as msg_to_task:
            self.executor.enqueue_command(
                cast("IClientProtocol", self.client),
                {"mensaje": "agregar_unidad"},
            )
            self.executor.enqueue_command(
                cast("IClientProtocol", self.client),
                {"mensaje": "chat", "msg": "barrera"},
            )
            self.assertTrue(completed.wait(timeout=1.0))

        self.assertEqual(msg_to_task.call_count, 1)
        self.assertEqual(self.client.transmisor.errors[0][0], "command_id_required")
        self.assertEqual(self.server.revision, 0)
        self.assertEqual(self.server.snapshots, 0)

    def test_rejected_command_does_not_publish_revision(self) -> None:
        """Un rechazo no altera la revisión pública ni difunde snapshot."""
        completed = threading.Event()
        with patch(
            "pyteg.server.juego.command_executor.ServerTaskManager.msg_to_task",
            side_effect=[_RejectingTask(), _BarrierTask(completed)],
        ):
            self.executor.enqueue_command(
                cast("IClientProtocol", self.client),
                {"mensaje": "agregar_unidad", "command_id": "reject-1"},
            )
            self.executor.enqueue_command(
                cast("IClientProtocol", self.client),
                {"mensaje": "chat", "msg": "barrera"},
            )
            self.assertTrue(completed.wait(timeout=1.0))

        self.assertEqual(self.server.revision, 0)
        self.assertEqual(self.server.snapshots, 0)

    def test_duplicate_command_id_replays_without_running_task(self) -> None:
        """Un reintento idéntico devuelve el resultado sin mutar otra vez."""
        first_completed = threading.Event()
        barrier_completed = threading.Event()
        with patch(
            "pyteg.server.juego.command_executor.ServerTaskManager.msg_to_task",
            side_effect=[
                _BarrierTask(first_completed),
                _BarrierTask(barrier_completed),
            ],
        ) as msg_to_task:
            payload = {"mensaje": "agregar_unidad", "command_id": "same-1"}
            self.executor.enqueue_command(cast("IClientProtocol", self.client), payload)
            self.assertTrue(first_completed.wait(timeout=1.0))
            self.executor.enqueue_command(
                cast("IClientProtocol", self.client), dict(payload)
            )
            self.executor.enqueue_command(
                cast("IClientProtocol", self.client),
                {"mensaje": "chat", "msg": "barrera"},
            )
            self.assertTrue(barrier_completed.wait(timeout=1.0))

        self.assertEqual(msg_to_task.call_count, 2)
        self.assertEqual(self.server.revision, 1)
        self.assertEqual(self.server.snapshots, 1)
        self.assertEqual(
            self.client.transmisor.command_results,
            [
                {"command_id": "same-1", "accepted": True, "revision": 1},
                {"command_id": "same-1", "accepted": True, "revision": 1},
            ],
        )

    def test_command_id_conflict_is_rejected_without_mutation(self) -> None:
        """Reutilizar un ID con otro payload no ejecuta la segunda mutación."""
        first_completed = threading.Event()
        barrier_completed = threading.Event()
        with patch(
            "pyteg.server.juego.command_executor.ServerTaskManager.msg_to_task",
            side_effect=[
                _BarrierTask(first_completed),
                _BarrierTask(barrier_completed),
            ],
        ) as msg_to_task:
            self.executor.enqueue_command(
                cast("IClientProtocol", self.client),
                {
                    "mensaje": "agregar_unidad",
                    "command_id": "same-2",
                    "pais": "A",
                },
            )
            self.assertTrue(first_completed.wait(timeout=1.0))
            self.executor.enqueue_command(
                cast("IClientProtocol", self.client),
                {
                    "mensaje": "agregar_unidad",
                    "command_id": "same-2",
                    "pais": "B",
                },
            )
            self.executor.enqueue_command(
                cast("IClientProtocol", self.client),
                {"mensaje": "chat", "msg": "barrera"},
            )
            self.assertTrue(barrier_completed.wait(timeout=1.0))

        self.assertEqual(msg_to_task.call_count, 2)
        self.assertEqual(self.server.revision, 1)
        self.assertEqual(self.server.snapshots, 1)
        self.assertEqual(
            self.client.transmisor.command_results[-1],
            {
                "command_id": "same-2",
                "accepted": False,
                "revision": 1,
                "error_code": "command_id_conflict",
            },
        )
