"""Tareas del servidor: clase base y tarea nula."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

from pyteg.core.partida.context import GameContext
from pyteg.exceptions import (
    GameRuleViolationError,
    MensajeNoValidoError,
    PlayerEliminatedError,
    PyTegError,
)
from pyteg.logger import get_logger
from pyteg.server.juego.state_validator import ServerStateValidator
from pyteg.server.tasks.types import BaseTaskData

LOGGER = get_logger("server.tasks")


@runtime_checkable
class _AdminClientProtocol(Protocol):
    """Capacidad de administrar la configuración de una sala."""

    def es_admin(self) -> bool:
        """Indica si el cliente controla la configuración de la sala."""
        ...


if TYPE_CHECKING:
    from pyteg.protocols import IClientProtocol


class IServerTask[TData: BaseTaskData](ABC):
    """Clase base para todas las tareas del servidor.

    Parametrizada por `TData` (subtipo de `BaseTaskData`) para que cada
    subclase tipi su `data` con el `TypedDict` correspondiente y mypy
    detecte campos mal escritos o no soportados.
    """

    requires_admin = False
    """Si la acción sólo puede ser ejecutada por el administrador de la sala."""

    def __init__(self, data: TData) -> None:
        """Inicializa la tarea del servidor.

        Args:
            data: Datos del mensaje recibido del cliente (tipados por
                la subclase).

        """
        self._data: TData = data
        self._action_name: str | None = None  # Nombre de la acción para validación
        self._validator = ServerStateValidator()

    @abstractmethod
    def _execute(self, client: IClientProtocol, context: GameContext) -> bool | None:
        """Método que implementa la lógica específica de cada tarea.

        Args:
            client: Cliente que ejecuta la tarea.
            context: Contexto de acceso a recursos del juego.

        """

    def run(self, client: IClientProtocol) -> bool:
        """Ejecuta la tarea validando primero el estado del servidor.

        Captura todas las excepciones de tipo GameRuleViolationError y las
        convierte en mensajes de error para el cliente, estandarizando el
        manejo de errores.

        Args:
            client: Cliente que ejecuta la tarea.

        Returns:
            ``True`` si la tarea se ejecutó; ``False`` si fue rechazada.

        Raises:
            PlayerEliminatedError: Si el cliente eliminado intenta una acción
                distinta de chatear.

        """
        try:
            is_admin = isinstance(client, _AdminClientProtocol) and client.es_admin()
            if self.requires_admin and not is_admin:
                client.transmisor.enviar_error(
                    "not_admin",
                    "Solo el administrador puede configurar o iniciar la partida.",
                )
                LOGGER.warning(
                    "Cliente no administrador %s intentó ejecutar %s",
                    client.userid(),
                    self._action_name,
                )
                return False

            # Validar estado usando TaskValidator cuando corresponda
            if self._action_name is not None:
                self._validator.validar_accion(self._action_name, client.server)

            # Crear contexto de acceso a recursos
            context = GameContext(
                client.server.mapa,
                client.server.game,
                client.server,
            )

            if self._jugador_eliminado_no_puede_actuar(context, client):
                raise PlayerEliminatedError

            # Ejecutar la tarea si la validación pasa
            executed = self._execute(client, context)
            return executed is not False  # noqa: TRY300

        except GameRuleViolationError as e:
            # Estandarizar: todas las violaciones de reglas se envían como error de chat
            client.transmisor.enviar_error_chat(e.mensaje)
            LOGGER.debug("Error de regla del juego: %s", e.mensaje)
            return False
        except PyTegError as e:
            # Otras excepciones de PyTeg también se envían como error
            client.transmisor.enviar_error_chat(e.mensaje)
            LOGGER.warning("Error de PyTeg: %s", e.mensaje)
            return False

    def _jugador_eliminado_no_puede_actuar(
        self, context: GameContext, client: IClientProtocol
    ) -> bool:
        """Indica si una acción de juego fue enviada por un eliminado.

        El chat se conserva disponible para todos. La consulta dinámica mantiene
        compatibilidad con los dobles mínimos de tests y con juegos previos que
        aún no exponían el método de eliminación.

        Returns:
            ``True`` si el cliente está eliminado y la acción debe rechazarse.

        """
        if self._action_name in {None, "chat"} or context.game is None:
            return False

        jugador_esta_eliminado = getattr(context.game, "jugador_esta_eliminado", None)
        return callable(jugador_esta_eliminado) and bool(jugador_esta_eliminado(client))


class ServerTaskNull(IServerTask[BaseTaskData]):
    """Tarea nula para mensajes no reconocidos."""

    def __init__(self, data: BaseTaskData) -> None:
        """Inicializa la tarea nula.

        Args:
            data: Datos del mensaje recibido.

        """
        super().__init__(data)
        # No necesita validación de estado

    def _execute(self, _: Any, context: GameContext) -> None:  # noqa: ARG002
        msg = f"{self._data}"
        raise MensajeNoValidoError(msg)
