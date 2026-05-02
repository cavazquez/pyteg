"""Tareas del servidor: clase base y tarea nula."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

from pyteg.exception import GameRuleViolationError, MensajeNoValidoError, PyTegError
from pyteg.game_context import GameContext
from pyteg.logger import get_logger
from pyteg.server.juego.state_validator import ServerStateValidator

LOGGER = get_logger("server.tasks")

if TYPE_CHECKING:
    from pyteg.protocols import IClientProtocol


class IServerTask(ABC):
    """Clase base para todas las tareas del servidor."""

    def __init__(self, data: dict[str, Any]) -> None:
        """Inicializa la tarea del servidor.

        Args:
            data: Datos del mensaje recibido del cliente.

        """
        self._data = data
        self._action_name: str | None = None  # Nombre de la acción para validación
        self._validator = ServerStateValidator()

    @abstractmethod
    def _execute(self, client: IClientProtocol, context: GameContext) -> None:
        """Método que implementa la lógica específica de cada tarea.

        Args:
            client: Cliente que ejecuta la tarea.
            context: Contexto de acceso a recursos del juego.

        """

    def run(self, client: IClientProtocol) -> None:
        """Ejecuta la tarea validando primero el estado del servidor.

        Captura todas las excepciones de tipo GameRuleViolationError y las
        convierte en mensajes de error para el cliente, estandarizando el
        manejo de errores.

        Args:
            client: Cliente que ejecuta la tarea.

        """
        try:
            # Validar estado usando TaskValidator cuando corresponda
            if self._action_name is not None:
                self._validator.validar_accion(self._action_name, client.server)

            # Crear contexto de acceso a recursos
            context = GameContext(
                client.server.mapa,
                client.server.game,
                client.server,
            )

            # Ejecutar la tarea si la validación pasa
            self._execute(client, context)

        except GameRuleViolationError as e:
            # Estandarizar: todas las violaciones de reglas se envían como error de chat
            client.transmisor.enviar_error_chat(e.mensaje)
            LOGGER.debug("Error de regla del juego: %s", e.mensaje)
        except PyTegError as e:
            # Otras excepciones de PyTeg también se envían como error
            client.transmisor.enviar_error_chat(e.mensaje)
            LOGGER.warning("Error de PyTeg: %s", e.mensaje)


class ServerTaskNull(IServerTask):
    """Tarea nula para mensajes no reconocidos."""

    def __init__(self, data: dict[str, Any]) -> None:
        """Inicializa la tarea nula.

        Args:
            data: Datos del mensaje recibido.

        """
        super().__init__(data)
        # No necesita validación de estado

    def _execute(self, _: Any, context: GameContext) -> None:  # noqa: ARG002
        msg = f"{self._data}"
        raise MensajeNoValidoError(msg)
