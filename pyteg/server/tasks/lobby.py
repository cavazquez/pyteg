"""Tareas del servidor: lobby (chat, partida, usuario, color)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pyteg.server.tasks.base import LOGGER, IServerTask
from pyteg.server.tasks.types import (
    BaseTaskData,
    ChatTaskData,
    EmpezarTaskData,
    SeleccionarColorTaskData,
    SetUsernameTaskData,
)

if TYPE_CHECKING:
    from pyteg.core.partida.context import GameContext
    from pyteg.protocols import IClientProtocol


class ServerTaskChat(IServerTask[ChatTaskData]):
    """Tarea para procesar mensajes de chat."""

    def __init__(self, data: ChatTaskData) -> None:
        """Inicializa la tarea de chat.

        Args:
            data: Datos del mensaje de chat.

        """
        super().__init__(data)
        self._msg = data.get("msg")
        self._action_name = "chat"

    def _execute(
        self,
        client: IClientProtocol,
        context: GameContext,  # noqa: ARG002
    ) -> None:
        client.server.enviar_chat(client.username(), self._msg)


class ServerTaskEmpezar(IServerTask[EmpezarTaskData]):
    """Tarea para configurar e iniciar la partida."""

    def __init__(self, data: EmpezarTaskData) -> None:
        """Inicializa la tarea de empezar partida.

        Args:
            data: Datos de configuración de la partida.

        """
        super().__init__(data)
        self._segundos = data.get("segundos")
        self._paises_para_victoria = data.get("paises_para_victoria")
        self._objetivos_secretos = data.get("objetivos_secretos", False)
        self._misiles_habilitados = data.get("misiles_habilitados", False)
        self._action_name = "empezar"

    def _execute(
        self,
        client: IClientProtocol,
        context: GameContext,  # noqa: ARG002
    ) -> None:
        # Configurar segundos por turno si se envió desde el cliente
        if self._segundos is not None:
            try:
                segundos_int = int(self._segundos)
                if segundos_int > 0:
                    client.server.set_segundos_por_turno(segundos_int)
            except (TypeError, ValueError):
                pass

        # Configurar países para victoria si se envió desde el cliente
        if self._paises_para_victoria is not None:
            try:
                paises_int = int(self._paises_para_victoria)
                if paises_int >= 0:  # Permitir 0 para desactivar objetivo específico
                    client.server.set_paises_para_victoria(paises_int)
            except (TypeError, ValueError):
                pass

        # Configurar objetivos secretos si se envió desde el cliente
        client.server.set_objetivos_secretos(activados=self._objetivos_secretos)
        LOGGER.debug("Objetivos secretos configurados: %s", self._objetivos_secretos)

        # Configurar misiles si se envió desde el cliente
        client.server.set_misiles_habilitados(activados=self._misiles_habilitados)
        LOGGER.debug("Misiles habilitados: %s", self._misiles_habilitados)

        if client.server.estado.esperar_jugadores():
            client.server.enviar_estado()
        else:
            LOGGER.warning(
                "No se pudo cambiar a estado EsperarJugadores desde %s",
                client.server.estado.estado_actual(),
            )


class ServerTaskSeleccionarColor(IServerTask[SeleccionarColorTaskData]):
    """Tarea para seleccionar el color de un jugador."""

    def __init__(self, data: SeleccionarColorTaskData) -> None:
        """Inicializa la tarea de seleccionar color.

        Args:
            data: Datos con el color seleccionado.

        """
        super().__init__(data)
        self._color = data.get("color")
        self._action_name = "seleccionar_color"

    def _execute(
        self,
        client: IClientProtocol,
        context: GameContext,  # noqa: ARG002
    ) -> None:
        if self._color is not None:
            client.cambiar_color(self._color)
        client.server.enviar_colores_asignados()


class ServerTaskEmpezarPartida(IServerTask[BaseTaskData]):
    """Tarea para iniciar la partida después de la configuración."""

    def __init__(self, data: BaseTaskData) -> None:
        """Inicializa la tarea de empezar partida.

        Args:
            data: Datos del mensaje (vacío para esta tarea).

        """
        super().__init__(data)
        self._action_name = "empezar_partida"

    def _execute(
        self,
        client: IClientProtocol,
        context: GameContext,  # noqa: ARG002
    ) -> None:
        if client.server.estado.empezar_partida():
            client.server.enviar_estado()
            client.server.empezar_partida()
        else:
            LOGGER.warning(
                "No se pudo empezar la partida desde el estado %s",
                client.server.estado.estado_actual(),
            )


class ServerTaskSetUsername(IServerTask[SetUsernameTaskData]):
    """Tarea para establecer el nombre de usuario de un cliente."""

    def __init__(self, data: SetUsernameTaskData) -> None:
        """Inicializa la tarea de establecer username.

        Args:
            data: Datos con el nombre de usuario.

        """
        super().__init__(data)
        self._username = data.get("username")
        self._action_name = "set_username"

    def _execute(self, client: IClientProtocol, context: GameContext) -> None:
        if self._username and isinstance(self._username, str):
            # Verificar si el username ya está en uso por otro cliente
            for other_client in context.dame_clientes():
                if (
                    other_client.userid() != client.userid()
                    and other_client.username() == self._username
                ):
                    # Username duplicado, enviar error al cliente
                    error_msg = (
                        f"El nombre de usuario '{self._username}' ya está en uso. "
                        "Por favor, elige otro nombre."
                    )
                    client.transmisor.enviar_error("duplicate_username", error_msg)
                    LOGGER.warning(
                        "Usuario %s intentó usar username duplicado: %s",
                        client.userid(),
                        self._username,
                    )
                    return

            # Username válido, actualizar el nombre de usuario del cliente
            client.set_username(self._username)
            # Notificar a todos los clientes sobre el cambio de nombre
            client.server.enviar_username()
            LOGGER.info(
                "Usuario %s ha cambiado su nombre a: %s",
                client.userid(),
                self._username,
            )
