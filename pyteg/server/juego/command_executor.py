"""Serialización de comandos TCP y vencimientos de turno del servidor."""

from __future__ import annotations

import queue
import threading
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from pyteg.exceptions import EstadoInvalidoError, MensajeNoValidoError
from pyteg.logger import get_logger
from pyteg.server.tasks.manager import ServerTaskManager

if TYPE_CHECKING:
    from pyteg.protocols import IClientProtocol


LOGGER = get_logger(__name__)


@dataclass(frozen=True)
class _ClientCommand:
    """Comando validado que llegó desde una conexión TCP."""

    client: IClientProtocol
    payload: dict[str, Any]


@dataclass(frozen=True)
class _TurnExpired:
    """Vencimiento asociado a una generación concreta del turno."""

    generation: int


@dataclass(frozen=True)
class _ClientDisconnected:
    """Desconexión que debe mutar el juego dentro del hilo serializador."""

    user_id: int


_STOP = object()


class GameCommandExecutor:
    """Aplica cada transición del juego en un único hilo FIFO.

    Los lectores TCP validan el contrato y sólo encolan un ``_ClientCommand``.
    El temporizador hace lo propio con ``_TurnExpired``. Así una transición no
    puede intercalarse entre la validación y la mutación de otra.
    """

    def __init__(self, server: Any) -> None:
        """Inicializa el ejecutor para un único servidor.

        Args:
            server: Servidor dueño del estado de juego.

        """
        self._server = server
        self._queue: queue.Queue[object] = queue.Queue()
        self._state_lock = threading.Lock()
        self._accepting = True
        self._turn_marker: tuple[int, int, int, int] | None = None
        self._turn_generation = 0
        self._turn_snapshot: tuple[int, int] | None = None
        self._thread = threading.Thread(
            target=self._run,
            name="pyteg-game-command-executor",
            daemon=True,
        )

    def start(self) -> None:
        """Arranca el único consumidor de comandos."""
        self._refresh_turn_snapshot()
        self._thread.start()

    def enqueue_command(self, client: IClientProtocol, payload: dict[str, Any]) -> None:
        """Encola un comando TCP ya validado, sin ejecutarlo en el lector."""
        with self._state_lock:
            if not self._accepting:
                return
            self._queue.put(_ClientCommand(client, payload))

    def enqueue_turn_expired(self, generation: int) -> None:
        """Encola el vencimiento del turno si todavía corresponde."""
        with self._state_lock:
            if not self._accepting:
                return
            self._queue.put(_TurnExpired(generation))

    def enqueue_client_disconnected(self, user_id: int) -> None:
        """Encola una desconexión para mutar turnos en forma serializada."""
        with self._state_lock:
            if not self._accepting:
                return
            self._queue.put(_ClientDisconnected(user_id))

    def turn_snapshot(self) -> tuple[int, int] | None:
        """Devuelve ``(jugador_actual, generación)`` de forma atómica.

        Returns:
            El jugador del turno actual y su generación, o ``None`` sin partida.

        """
        with self._state_lock:
            return self._turn_snapshot

    def stop(self) -> None:
        """Deja de aceptar trabajo y espera al ejecutor sin dejar hilos vivos."""
        with self._state_lock:
            if not self._accepting:
                return
            self._accepting = False
        self._queue.put(_STOP)
        if threading.current_thread() is not self._thread:
            self._thread.join(timeout=2.0)

    def _run(self) -> None:
        """Consume comandos y vencimientos en el orden en que llegaron."""
        while True:
            item = self._queue.get()
            try:
                if item is _STOP:
                    return
                if isinstance(item, _ClientCommand):
                    self._execute_client_command(item)
                elif isinstance(item, _TurnExpired):
                    self._execute_turn_expired(item)
                elif isinstance(item, _ClientDisconnected):
                    self._execute_client_disconnected(item)
            except Exception:
                LOGGER.exception("Error al ejecutar transición de juego")
            finally:
                self._refresh_turn_snapshot()
                self._queue.task_done()

    def _execute_client_command(self, command: _ClientCommand) -> None:
        """Construye y ejecuta una tarea del servidor dentro del serializador."""
        task = ServerTaskManager.msg_to_task(command.payload)
        try:
            task.run(command.client)
        except MensajeNoValidoError:
            LOGGER.exception(
                "Mensaje no válido del cliente %s", command.client.userid()
            )
        except EstadoInvalidoError as error:
            LOGGER.warning(
                "Error de estado del cliente %s: %s", command.client.userid(), error
            )
            command.client.transmisor.enviar_error("invalid_state", str(error))

    def _execute_turn_expired(self, expired: _TurnExpired) -> None:
        """Avanza una vez sólo si el timer corresponde al turno vigente."""
        snapshot = self.turn_snapshot()
        if snapshot is None or snapshot[1] != expired.generation:
            LOGGER.debug(
                "Se descartó vencimiento obsoleto de turno %s", expired.generation
            )
            return

        game = self._server.game
        if game is None or not self._server.estado.es_jugando() or not game.empezo():
            return

        player_id, _generation = snapshot
        if int(game.turno_actual().jugador_actual()) != player_id:
            LOGGER.debug("Se descartó vencimiento con jugador de turno obsoleto")
            return

        game.limpiar_elegibilidad_reclamar()
        game.finalizar_turno()
        if self._server.estado.es_jugando():
            self._server.enviar_turno_actual()
            self._server.enviar_mapa()

    def _execute_client_disconnected(self, event: _ClientDisconnected) -> None:
        """Quita una conexión de los turnos sin tocar su ocupación."""
        game = self._server.game
        if game is None or not game.empezo() or not self._server.estado.es_jugando():
            return

        if not game.desconectar_jugador(event.user_id):
            return

        if self._server.estado.es_jugando():
            self._server.enviar_colores_asignados()
            self._server.enviar_turno_actual()

    def _refresh_turn_snapshot(self) -> None:
        """Publica el turno actual y aumenta su generación al cambiarlo."""
        game = self._server.game
        estado = self._server.estado
        if game is None or not estado.es_jugando() or not game.empezo():
            with self._state_lock:
                self._turn_marker = None
                self._turn_snapshot = None
            return

        turno = game.turno_actual()
        player_id = int(turno.jugador_actual())
        marker = (
            id(game),
            int(game.id_turno_actual()),
            int(game.num_ronda()),
            player_id,
        )
        with self._state_lock:
            if marker != self._turn_marker:
                self._turn_marker = marker
                self._turn_generation += 1
            self._turn_snapshot = (player_id, self._turn_generation)
