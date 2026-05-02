"""Tareas del cliente: identidad y lista de jugadores."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from PySide6.QtGui import QColor

from pyteg.client.app import Client
from pyteg.client.tasks.base import IClientTask
from pyteg.client.tasks.logging_helper import CLIENT_TASKS_LOG
from pyteg.i18n import translate as _

if TYPE_CHECKING:
    from pyteg.client.tasks.protocols import GameWindowProtocol


class ClientTaskUserId(IClientTask):
    """Tarea para asignar un ID de usuario al cliente."""

    def __init__(self, data: dict[str, Any]) -> None:
        """Inicializa la tarea de ID de usuario.

        Args:
            data: Diccionario con el ID de usuario.

        """
        super().__init__(data)
        self._msg = data

    def run(self, main_window: GameWindowProtocol) -> None:
        """Ejecuta la tarea asignando el ID de usuario al cliente."""
        user_id_raw = self._msg.get("user_id")
        if user_id_raw is None:
            return
        userid = int(user_id_raw)
        CLIENT_TASKS_LOG.debug("ClientTaskUserId: Recibido user_id %s", userid)

        if not main_window.client.userid():
            CLIENT_TASKS_LOG.debug(
                "ClientTaskUserId: Estableciendo %s como MI user_id", userid
            )
            main_window.client.set_userid(userid)
            main_window.update_mi_jugador_info()
        else:
            CLIENT_TASKS_LOG.debug(
                "ClientTaskUserId: Ya tengo user_id %s, agregando %s a la lista",
                main_window.client.userid(),
                userid,
            )

        main_window.client_by_id[userid] = Client()
        main_window.client_by_id[userid].set_userid(userid)


class ClientTaskUsername(IClientTask):
    """Tarea para actualizar el nombre de usuario de un jugador."""

    def __init__(self, data: dict[str, Any]) -> None:
        """Inicializa la tarea de nombre de usuario.

        Args:
            data: Diccionario con el ID y nombre de usuario.

        """
        super().__init__(data)
        self._msg = data

    def run(self, main_window: GameWindowProtocol) -> None:
        """Ejecuta la tarea actualizando el nombre de usuario."""
        username = self._msg.get("username")
        userid = self._msg.get("user_id")

        if main_window.client.userid() == userid:
            main_window.client.set_username(username)

        if userid in main_window.client_by_id:
            main_window.client_by_id[userid].set_username(username)

        self.actualizar_lista_jugadores(main_window)

        if main_window.client.userid() == userid:
            main_window.update_mi_jugador_info()

        if main_window.w is not None:
            main_window.w.cargar_colores_asignados()

    def actualizar_lista_jugadores(self, main_window: Any) -> None:
        """Actualiza la lista de jugadores en la interfaz de usuario."""
        jugadores: list[tuple[str, Any]] = []
        for user_id, color in main_window.colores.colores_asignados().items():
            client = main_window.client_by_id.get(user_id)
            if client and client.username():
                jugadores.append((client.username(), color))

        main_window.update_player_list(jugadores)


class ClientTaskActualizarListaJugadores(IClientTask):
    """Tarea para actualizar la lista de jugadores con el orden actualizado."""

    def __init__(self, data: dict[str, Any]) -> None:
        """Inicializa la tarea de actualización de lista de jugadores.

        Args:
            data: Diccionario con la lista de jugadores.

        """
        super().__init__(data)
        self._jugadores = data.get("jugadores", [])

    def run(self, main_window: GameWindowProtocol) -> None:
        """Actualiza la lista de jugadores en la interfaz de usuario.

        Actualiza la lista de jugadores en la interfaz de usuario con el
        orden actualizado.

        Args:
            main_window: La ventana principal de la aplicación

        """
        try:
            jugadores_actualizados = []

            for jugador in self._jugadores:
                userid = jugador.get("userid")
                color_data = jugador.get("color", {})

                nombre = _("Jugador {}").format(userid)
                if userid in main_window.client_by_id:
                    cliente = main_window.client_by_id[userid]
                    if hasattr(cliente, "username") and cliente.username():
                        nombre = cliente.username()

                color = QColor(
                    color_data.get("r", 200),
                    color_data.get("g", 200),
                    color_data.get("b", 200),
                )

                jugadores_actualizados.append((nombre, color))

            main_window.update_player_list(jugadores_actualizados)

        except (AttributeError, KeyError, TypeError) as e:
            CLIENT_TASKS_LOG.warning("Error al actualizar la lista de jugadores: %s", e)
