"""Regresiones deterministas del serializador de comandos de juego."""

from __future__ import annotations

import threading
import unittest
from typing import TYPE_CHECKING, cast
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

    def enviar_turno_actual(self) -> None:
        """Registra la difusión del nuevo turno."""
        self.turno_enviado.set()

    def enviar_mapa(self) -> None:
        """Registra la difusión del mapa actualizado."""
        self.mapa_enviado.set()


class _FakeClient:
    """Cliente mínimo para ejecutar la tarea bloqueada."""

    def __init__(self, server: _FakeServer) -> None:
        """Asocia el cliente al servidor de prueba."""
        self.server = server

    def userid(self) -> int:
        """Devuelve un id estable usado sólo por el logger.

        Returns:
            Identificador fijo del cliente de prueba.

        """
        return 1


class _BlockingPlacementTask:
    """Reproduce una acción pausada después de validar el turno."""

    def __init__(self, validated: threading.Event, release: threading.Event) -> None:
        """Configura las barreras de la carrera reproducida."""
        self._validated = validated
        self._release = release
        self.validated_player: int | None = None

    def run(self, client: _FakeClient) -> None:
        """Valida, se pausa y consume una unidad del turno que validó.

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


class _BarrierTask:
    """Marca que todos los elementos FIFO anteriores ya se procesaron."""

    def __init__(self, completed: threading.Event) -> None:
        """Guarda la señal de finalización."""
        self._completed = completed

    def run(self, _: object) -> None:
        """Señala que llegó al final de la cola."""
        self._completed.set()


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
                cast("IClientProtocol", self.client), {"mensaje": "agregar_unidad"}
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
