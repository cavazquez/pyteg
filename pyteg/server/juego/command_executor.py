"""Serialización de comandos TCP y vencimientos de turno del servidor."""

from __future__ import annotations

import queue
import threading
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Protocol, cast

from pyteg.exceptions import EstadoInvalidoError, MensajeNoValidoError
from pyteg.logger import get_logger
from pyteg.server.tasks.manager import ServerTaskManager

if TYPE_CHECKING:
    from pyteg.protocols import IClientProtocol


LOGGER = get_logger(__name__)


class _QueuedEvent(Protocol):
    """Evento interno que selecciona su transición en el ejecutor."""

    def accept(self, executor: GameCommandExecutor) -> None:
        """Selecciona la transición correspondiente al evento."""
        ...


@dataclass(frozen=True)
class _ClientCommand:
    """Comando validado que llegó desde una conexión TCP."""

    client: IClientProtocol
    payload: dict[str, Any]

    def accept(self, executor: GameCommandExecutor) -> None:
        """Inicia la ejecución del comando del cliente."""
        executor._execute_client_command(self)  # noqa: SLF001


@dataclass(frozen=True)
class _TurnExpired:
    """Vencimiento asociado a una generación concreta del turno."""

    generation: int

    def accept(self, executor: GameCommandExecutor) -> None:
        """Inicia el tratamiento del vencimiento del turno."""
        executor._execute_turn_expired(self)  # noqa: SLF001


@dataclass(frozen=True)
class _ClientDisconnected:
    """Desconexión que debe mutar el juego dentro del hilo serializador."""

    user_id: int

    def accept(self, executor: GameCommandExecutor) -> None:
        """Inicia el tratamiento de la desconexión del cliente."""
        executor._execute_client_disconnected(self)  # noqa: SLF001


@dataclass(frozen=True)
class _ReopenEmptyLobby:
    """Reabre una partida terminada cuando ya no queda ningún cliente."""

    completed: threading.Event | None = None

    def accept(self, executor: GameCommandExecutor) -> None:
        """Procesa la reapertura y despierta al hilo de conexiones."""
        try:
            executor._execute_reopen_empty_lobby()  # noqa: SLF001
        finally:
            if self.completed is not None:
                self.completed.set()


_STOP = object()
_NON_MUTATING_COMMANDS = frozenset({
    "chat",
    "hello",
    "solicitar_snapshot",
    "solicitar_tarjetas",
})


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

    def enqueue_reopen_empty_lobby(self) -> None:
        """Programa la limpieza de una partida terminada y sin conexiones."""
        with self._state_lock:
            if self._accepting:
                self._queue.put(_ReopenEmptyLobby())

    def wait_for_empty_lobby(self) -> bool:
        """Espera a que el ejecutor reabra la sala, si está vacía.

        Returns:
            ``True`` si terminó en estado de lobby.

        """
        completed = threading.Event()
        with self._state_lock:
            if not self._accepting:
                return False
            self._queue.put(_ReopenEmptyLobby(completed))
        reopened = completed.wait(timeout=5.0)
        return reopened and self._server.estado.es_esperando_jugadores()

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
                cast("_QueuedEvent", item).accept(self)
            except Exception:
                LOGGER.exception("Error al ejecutar transición de juego")
            finally:
                self._refresh_turn_snapshot()
                self._queue.task_done()

    def _execute_client_command(self, command: _ClientCommand) -> None:
        """Construye y ejecuta una tarea del servidor dentro del serializador."""
        command_name = command.payload.get("mensaje")
        command_id = command.payload.get("command_id")
        if self._requires_command_id(command_name, command_id):
            self._reject_missing_command_id(command.client)
            return
        cached = self._cached_command_result(command)
        if cached is not None:
            self._replay_or_reject_conflict(command, cached)
            return
        revision_getter = getattr(self._server, "state_revision", None)
        revision_before = revision_getter() if callable(revision_getter) else None
        accepted, error_code = self._run_task(command)

        if accepted and command_name not in _NON_MUTATING_COMMANDS:
            self._publish_revision_if_needed(revision_before)
        self._send_command_result(
            command,
            accepted=accepted,
            error_code=error_code,
        )

    def _run_task(self, command: _ClientCommand) -> tuple[bool, str | None]:
        """Construye y ejecuta la tarea, traduciendo sus errores de protocolo.

        Returns:
            Tupla ``(aceptado, código_de_error)`` de la ejecución.

        """
        accepted = True
        error_code: str | None = None
        try:
            task = ServerTaskManager.msg_to_task(command.payload)
            accepted = bool(task.run(command.client))
        except MensajeNoValidoError:
            accepted = False
            error_code = "invalid_message"
            LOGGER.exception(
                "Mensaje no válido del cliente %s", command.client.userid()
            )
        except EstadoInvalidoError as error:
            accepted = False
            error_code = "invalid_state"
            LOGGER.warning(
                "Error de estado del cliente %s: %s", command.client.userid(), error
            )
            command.client.transmisor.enviar_error("invalid_state", str(error))
        except Exception:
            accepted = False
            error_code = "internal_error"
            LOGGER.exception("Fallo ejecutando comando del cliente")
        return accepted, error_code

    def _send_command_result(
        self,
        command: _ClientCommand,
        *,
        accepted: bool,
        error_code: str | None,
    ) -> None:
        """Cachea y transmite el resultado correlacionado de una mutación."""
        command_id = command.payload.get("command_id")
        if not isinstance(command_id, str):
            return
        result = {
            "command_id": command_id,
            "accepted": accepted,
            "revision": self._server.state_revision(),
        }
        if not accepted:
            result["error_code"] = error_code or "rejected"
        remember = getattr(command.client, "remember_command_result", None)
        command_name = command.payload.get("mensaje")
        if callable(remember) and command_name not in _NON_MUTATING_COMMANDS:
            try:
                remember(command_id, result, command.payload)
            except TypeError:
                remember(command_id, result)
        command.client.transmisor.enviar_resultado_comando(**result)

    @staticmethod
    def _requires_command_id(command_name: object, command_id: object) -> bool:
        """Indica si una mutación carece de un identificador válido.

        Returns:
            ``True`` si el comando es mutante y el ID falta o está vacío.

        """
        return command_name not in _NON_MUTATING_COMMANDS and (
            not isinstance(command_id, str) or not command_id.strip()
        )

    @staticmethod
    def _cached_command_result(
        command: _ClientCommand,
    ) -> dict[str, Any] | None:
        """Obtiene el resultado previo de una mutación, si existe.

        Returns:
            Resultado cacheado o ``None`` para un comando nuevo/no mutante.

        """
        command_name = command.payload.get("mensaje")
        command_id = command.payload.get("command_id")
        if (
            command_name in _NON_MUTATING_COMMANDS
            or not isinstance(command_id, str)
            or not command_id.strip()
        ):
            return None
        get_result = getattr(command.client, "command_result", None)
        if not callable(get_result):
            return None
        return cast("dict[str, Any] | None", get_result(command_id))

    def _reject_missing_command_id(self, client: IClientProtocol) -> None:
        """Rechaza una mutación sin correlación antes de construir la tarea."""
        transmisor = getattr(client, "transmisor", None)
        enviar_error = getattr(transmisor, "enviar_error", None)
        if callable(enviar_error):
            enviar_error(
                "command_id_required",
                "Las mutaciones requieren un command_id no vacío.",
            )

    def _replay_or_reject_conflict(
        self, command: _ClientCommand, cached: dict[str, Any]
    ) -> None:
        """Reproduce un resultado o rechaza la reutilización con otro payload."""
        command_id = command.payload["command_id"]
        get_payload = getattr(command.client, "command_payload", None)
        cached_payload = get_payload(command_id) if callable(get_payload) else None
        current_payload = {
            key: value for key, value in command.payload.items() if key != "command_id"
        }
        if cached_payload is not None and cached_payload != current_payload:
            result = {
                "command_id": command_id,
                "accepted": False,
                "revision": self._server.state_revision(),
                "error_code": "command_id_conflict",
            }
            command.client.transmisor.enviar_resultado_comando(**result)
            return
        command.client.transmisor.enviar_resultado_comando(**cached)

    def _publish_revision_if_needed(self, revision_before: int | None) -> None:
        """Publica una única revisión para una mutación aceptada.

        Algunas transiciones complejas publican dentro de su coordinador (por
        ejemplo, iniciar, finalizar o reabrir una partida). Si ya cambiaron la
        revisión, el ejecutor reutiliza ese snapshot y no genera un segundo.
        """
        revision_getter = getattr(self._server, "state_revision", None)
        revision_after = revision_getter() if callable(revision_getter) else None
        if revision_before is not None and revision_after != revision_before:
            return
        bump = getattr(self._server, "bump_state_revision", None)
        snapshot = getattr(self._server, "enviar_snapshot", None)
        if callable(bump):
            bump()
        if callable(snapshot):
            snapshot()

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
        bump = getattr(self._server, "bump_state_revision", None)
        snapshot = getattr(self._server, "enviar_snapshot", None)
        if callable(bump):
            bump()
        if callable(snapshot):
            snapshot()

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
            bump = getattr(self._server, "bump_state_revision", None)
            snapshot = getattr(self._server, "enviar_snapshot", None)
            if callable(bump):
                bump()
            if callable(snapshot):
                snapshot()

    def _execute_reopen_empty_lobby(self) -> None:
        """Limpia la partida sólo si sigue finalizada y nadie se reconectó."""
        if self._server.estado.es_finalizado() and self._server.cant_clients() == 0:
            self._server.volver_al_lobby()

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
