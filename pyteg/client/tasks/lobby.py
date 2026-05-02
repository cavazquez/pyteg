"""Tareas del cliente: lobby (chat, usuario, colores, errores)."""

from __future__ import annotations

from typing import Any

from PySide6.QtGui import QColor
from PySide6.QtWidgets import QMessageBox

from pyteg.client.app import Client
from pyteg.client.tasks.base import IClientTask
from pyteg.client.tasks.logging_helper import CLIENT_TASKS_LOG
from pyteg.client_color import Color
from pyteg.i18n import translate as _


class ClientTaskChat(IClientTask):
    """Tarea para mostrar mensajes de chat."""

    def __init__(self, data: dict[str, Any]) -> None:
        """Inicializa la tarea de chat.

        Args:
            data: Diccionario con el mensaje y tipo de mensaje.

        """
        super().__init__(data)
        self._msg = data.get("msg")
        self._msg_type = data.get("msg_type", "normal")

    def run(self, main_window: Any) -> None:
        """Ejecuta la tarea agregando el mensaje al chat."""
        main_window.chat.append(self._msg, self._msg_type)


class ClientTaskSerAdmin(IClientTask):
    """Tarea para convertir al cliente en administrador."""

    def __init__(self, data: dict[str, Any]) -> None:
        """Inicializa la tarea de administrador.

        Args:
            data: Diccionario con los datos de la tarea.

        """
        super().__init__(data)

    def run(self, main_window: Any) -> None:
        """Ejecuta la tarea convirtiendo al cliente en administrador."""
        main_window.client.ahora_es_admin()
        main_window.ventana_admin()


class ClientTaskEstado(IClientTask):
    """Tarea para actualizar el estado del juego."""

    def __init__(self, data: dict[str, Any]) -> None:
        """Inicializa la tarea de estado.

        Args:
            data: Diccionario con el nuevo estado del juego.

        """
        super().__init__(data)
        self._msg = data.get("estado")

    def run(self, main_window: Any) -> None:
        """Ejecuta la tarea actualizando el estado del juego."""
        CLIENT_TASKS_LOG.debug("Recibido cambio de estado: %s", self._msg)

        # Actualizar el estado en la interfaz gráfica
        main_window.update_game_state(self._msg)

        if self._msg == "EsperarJugadores":
            CLIENT_TASKS_LOG.debug("Mostrando ventana de espera de jugadores")
            main_window.ventana_esperar_jugadores()
        elif self._msg == "JUGANDO":
            CLIENT_TASKS_LOG.debug("Cambiando a estado JUGANDO")
            # Cerrar la ventana de espera si está abierta
            if hasattr(main_window, "w") and main_window.w is not None:
                CLIENT_TASKS_LOG.debug("Cerrando ventana de espera...")
                try:
                    # Forzar el cierre de la ventana
                    main_window.w.close()
                    main_window.w.deleteLater()
                    main_window.w = None
                    CLIENT_TASKS_LOG.debug("Ventana de espera cerrada correctamente")
                except (AttributeError, RuntimeError) as e:
                    CLIENT_TASKS_LOG.warning(
                        "Error al cerrar la ventana de espera: %s", e
                    )
            else:
                CLIENT_TASKS_LOG.debug("No hay ventana de espera abierta para cerrar")

            # Actualizar la lista de jugadores en la interfaz principal
            try:
                self.actualizar_lista_jugadores(main_window)
            except (AttributeError, KeyError, TypeError) as e:
                CLIENT_TASKS_LOG.warning(
                    "Error al actualizar lista de jugadores: %s", e
                )

            # Forzar actualización de la interfaz
            if hasattr(main_window, "update"):
                main_window.update()

    def actualizar_lista_jugadores(self, main_window: Any) -> None:
        """Actualiza la lista de jugadores en la interfaz de usuario."""
        # Obtener la lista de jugadores con sus colores
        jugadores: list[tuple[str, Any]] = []
        for user_id, color in main_window.colores.colores_asignados().items():
            # Obtener el nombre de usuario del cliente
            client = main_window.client_by_id.get(user_id)
            if client:
                jugadores.append((client.username(), color))

        # Actualizar la lista de jugadores en la interfaz
        main_window.update_player_list(jugadores)


class ClientTaskColorAsignado(IClientTask):
    """Tarea para asignar un color a un jugador."""

    def __init__(self, data: dict[str, Any]) -> None:
        """Inicializa la tarea de asignación de color.

        Args:
            data: Diccionario con el ID del usuario y los componentes RGB del color.

        """
        super().__init__(data)
        self._msg = data

    def run(self, main_window: Any) -> None:
        """Ejecuta la tarea asignando el color al jugador."""
        try:
            # Extraer el ID de usuario y el color del mensaje
            id_user = self._msg.get("id")
            if not id_user:
                CLIENT_TASKS_LOG.warning(
                    "No se proporcionó ID de usuario en el mensaje de color asignado"
                )
                return

            # Extraer los componentes de color
            r = self._msg.get("r", 0)
            g = self._msg.get("g", 0)
            b = self._msg.get("b", 0)

            CLIENT_TASKS_LOG.debug(
                "Asignando color al jugador %s: R=%s, G=%s, B=%s",
                id_user,
                r,
                g,
                b,
            )

            # Crear el color y asignarlo al jugador
            color_data = {"r": r, "g": g, "b": b}
            main_window.colores.asignar(id_user, color_data)

            # Actualizar la lista de jugadores en la interfaz
            self.actualizar_lista_jugadores(main_window)

            # Actualizar la ventana de espera de jugadores si está abierta
            tiene_w = hasattr(main_window, "w") and main_window.w
            tiene_cargar_colores_asignados = hasattr(
                main_window.w, "cargar_colores_asignados"
            )
            if tiene_w and tiene_cargar_colores_asignados:
                main_window.w.cargar_colores_asignados()

            # Actualizar información del usuario actual si es su color
            if hasattr(main_window, "client") and main_window.client:
                mi_user_id = main_window.client.userid()
                CLIENT_TASKS_LOG.debug(
                    "ClientTaskColorAsignado: Mi user_id: %s, Color asignado a: %s",
                    mi_user_id,
                    id_user,
                )
                if mi_user_id == id_user:
                    CLIENT_TASKS_LOG.debug(
                        "ClientTaskColorAsignado: ES MI COLOR, actualizando mi info"
                    )
                    if hasattr(main_window, "update_mi_jugador_info"):
                        main_window.update_mi_jugador_info()
                else:
                    CLIENT_TASKS_LOG.debug(
                        "ClientTaskColorAsignado: NO es mi color, no actualizo"
                    )

        except (AttributeError, KeyError, ValueError) as e:
            CLIENT_TASKS_LOG.warning("Error en ClientTaskColorAsignado: %s", e)

    def actualizar_lista_jugadores(self, main_window: Any) -> None:
        """Actualiza la lista de jugadores en la interfaz de usuario."""
        try:
            # Obtener la lista de jugadores con sus colores
            jugadores: list[tuple[str, Any]] = []
            for user_id, color in main_window.colores.colores_asignados().items():
                # Obtener el nombre de usuario del cliente
                client = main_window.client_by_id.get(user_id)
                if client and hasattr(client, "username"):
                    jugadores.append((client.username(), color))
                    CLIENT_TASKS_LOG.debug(
                        "Jugador %s tiene color %s",
                        client.username(),
                        color.getRgb(),
                    )

            # Actualizar la lista de jugadores en la interfaz si el método existe
            if hasattr(main_window, "update_player_list"):
                main_window.update_player_list(jugadores)
        except (AttributeError, KeyError, TypeError) as e:
            CLIENT_TASKS_LOG.warning("Error al actualizar lista de jugadores: %s", e)


class ClientTaskColor(IClientTask):
    """Tarea para agregar un color disponible."""

    def __init__(self, data: dict[str, Any]) -> None:
        """Inicializa la tarea de color.

        Args:
            data: Diccionario con los componentes RGB del color.

        """
        super().__init__(data)
        self._msg = data

    def run(self, main_window: Any) -> None:
        """Ejecuta la tarea agregando el color a la lista de colores disponibles."""
        self._msg.pop("mensaje")
        main_window.colores.agregar_color(Color(**self._msg))


class ClientTaskUserId(IClientTask):
    """Tarea para asignar un ID de usuario al cliente."""

    def __init__(self, data: dict[str, Any]) -> None:
        """Inicializa la tarea de ID de usuario.

        Args:
            data: Diccionario con el ID de usuario.

        """
        super().__init__(data)
        self._msg = data

    def run(self, main_window: Any) -> None:
        """Ejecuta la tarea asignando el ID de usuario al cliente."""
        user_id_raw = self._msg.get("user_id")
        if user_id_raw is None:
            return
        userid = int(user_id_raw)
        CLIENT_TASKS_LOG.debug("ClientTaskUserId: Recibido user_id %s", userid)

        # Solo establecer el ID del cliente actual si aún no tiene uno
        if not main_window.client.userid():
            CLIENT_TASKS_LOG.debug(
                "ClientTaskUserId: Estableciendo %s como MI user_id", userid
            )
            main_window.client.set_userid(userid)
            # Actualizar información del usuario actual
            if hasattr(main_window, "update_mi_jugador_info"):
                main_window.update_mi_jugador_info()
        else:
            CLIENT_TASKS_LOG.debug(
                "ClientTaskUserId: Ya tengo user_id %s, agregando %s a la lista",
                main_window.client.userid(),
                userid,
            )

        # Siempre mantener información de todos los jugadores
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

    def run(self, main_window: Any) -> None:
        """Ejecuta la tarea actualizando el nombre de usuario."""
        username = self._msg.get("username")
        userid = self._msg.get("user_id")

        # Actualizar el nombre de usuario
        # en el cliente principal si es el propio cliente
        if main_window.client.userid() == userid:
            main_window.client.set_username(username)

        # Actualizar el nombre de usuario en el diccionario de clientes
        if userid in main_window.client_by_id:
            main_window.client_by_id[userid].set_username(username)

        # Actualizar la lista de jugadores en la interfaz
        self.actualizar_lista_jugadores(main_window)

        # Actualizar información del usuario actual si es mi usuario
        if main_window.client.userid() == userid and hasattr(
            main_window, "update_mi_jugador_info"
        ):
            main_window.update_mi_jugador_info()

        # Actualizar la ventana de espera de jugadores si está abierta
        if hasattr(main_window, "w") and main_window.w is not None:
            main_window.w.cargar_colores_asignados()

    def actualizar_lista_jugadores(self, main_window: Any) -> None:
        """Actualiza la lista de jugadores en la interfaz de usuario."""
        # Obtener la lista de jugadores con sus colores
        jugadores: list[tuple[str, Any]] = []
        for user_id, color in main_window.colores.colores_asignados().items():
            # Obtener el nombre de usuario del cliente
            client = main_window.client_by_id.get(user_id)
            if client and client.username():
                jugadores.append((client.username(), color))

        # Actualizar la lista de jugadores en la interfaz
        main_window.update_player_list(jugadores)


class ClientTaskAsignarPais(IClientTask):
    """Tarea para asignar un país a un jugador."""

    def __init__(self, data: dict[str, Any]) -> None:
        """Inicializa la tarea de asignación de país.

        Args:
            data: Diccionario con el país, ID de usuario y unidades.

        """
        super().__init__(data)
        self._msg = data

    def run(self, main_window: Any) -> None:
        """Ejecuta la tarea asignando el país al jugador."""
        try:
            nombre_pais = self._msg.get("pais")
            userid = self._msg.get("userid")
            unidades = self._msg.get("unidades", 1)  # Valor por defecto de 1 unidad

            # Obtener el objeto país de la escena
            pais = main_window.scene.paises.get(nombre_pais)
            if not pais:
                CLIENT_TASKS_LOG.warning("País no encontrado: %s", nombre_pais)
                return

            # Establecer las unidades del país
            pais.set_unidades(unidades)

            # Obtener el color asignado al jugador
            color = main_window.colores.color_asignado(userid)
            if not color:
                CLIENT_TASKS_LOG.warning(
                    "No se encontró color para el jugador %s", userid
                )
                return

            # Establecer el color del país
            pais.set_color(color)

            CLIENT_TASKS_LOG.debug(
                "País %s asignado al jugador %s con %s unidades y color %s",
                nombre_pais,
                userid,
                unidades,
                color.getRgb(),
            )

        except (AttributeError, KeyError, ValueError) as e:
            CLIENT_TASKS_LOG.warning("Error al asignar país: %s", e)


class ClientTaskUnidadesDisponibles(IClientTask):
    """Tarea para actualizar las unidades disponibles del jugador."""

    def __init__(self, data: dict[str, Any]) -> None:
        """Inicializa la tarea de unidades disponibles.

        Args:
            data: Diccionario con las unidades disponibles por tipo.

        """
        super().__init__(data)
        self._unidades = data.get("unidades", {})

    def run(self, main_window: Any) -> None:
        """Ejecuta la tarea actualizando las unidades disponibles."""
        CLIENT_TASKS_LOG.debug("Recibidas unidades disponibles: %s", self._unidades)
        if hasattr(main_window, "update_unidades_disponibles"):
            main_window.update_unidades_disponibles(self._unidades)


class ClientTaskActualizarListaJugadores(IClientTask):
    """Tarea para actualizar la lista de jugadores con el orden actualizado."""

    def __init__(self, data: dict[str, Any]) -> None:
        """Inicializa la tarea de actualización de lista de jugadores.

        Args:
            data: Diccionario con la lista de jugadores.

        """
        super().__init__(data)
        self._jugadores = data.get("jugadores", [])

    def run(self, main_window: Any) -> None:
        """Actualiza la lista de jugadores en la interfaz de usuario.

        Actualiza la lista de jugadores en la interfaz de usuario con el
        orden actualizado.

        Args:
            main_window: La ventana principal de la aplicación

        """
        try:
            # Crear una lista de tuplas (nombre, color) para actualizar la interfaz
            jugadores_actualizados = []

            for jugador in self._jugadores:
                userid = jugador.get("userid")
                color_data = jugador.get("color", {})

                # Obtener el nombre de usuario del cliente
                # Valor por defecto si no se encuentra el cliente
                nombre = _("Jugador {}").format(userid)
                if (
                    hasattr(main_window, "client_by_id")
                    and userid in main_window.client_by_id
                ):
                    cliente = main_window.client_by_id[userid]
                    if hasattr(cliente, "username") and cliente.username():
                        nombre = cliente.username()

                # Crear un objeto QColor a partir de los componentes RGB

                color = QColor(
                    color_data.get("r", 200),
                    color_data.get("g", 200),
                    color_data.get("b", 200),
                )

                jugadores_actualizados.append((nombre, color))

            # Actualizar la lista de jugadores en la interfaz
            if hasattr(main_window, "update_player_list"):
                main_window.update_player_list(jugadores_actualizados)

        except (AttributeError, KeyError, TypeError) as e:
            CLIENT_TASKS_LOG.warning("Error al actualizar la lista de jugadores: %s", e)


class ClientTaskError(IClientTask):
    """Tarea para manejar errores enviados por el servidor."""

    def __init__(self, data: dict[str, Any]) -> None:
        """Inicializa la tarea de error.

        Args:
            data: Diccionario con el tipo y mensaje de error.

        """
        super().__init__(data)
        self._error_type = data.get("error_type")
        self._message = data.get("message")

    def run(self, main_window: Any) -> None:
        """Maneja errores enviados por el servidor.

        Maneja errores enviados por el servidor mostrando un diálogo
        de error al usuario.
        """
        if self._error_type == "duplicate_username":
            # Mostrar diálogo específico para nombres de usuario duplicados
            msg_box = QMessageBox(main_window)
            msg_box.setIcon(QMessageBox.Icon.Warning)
            msg_box.setWindowTitle(_("Nombre de usuario duplicado"))
            msg_box.setText(_("El nombre de usuario que elegiste ya está en uso."))
            msg_box.setInformativeText(
                _("Por favor, elige un nombre de usuario diferente.")
            )
            msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
            msg_box.exec()

            # Cerrar ventana de esperar jugadores si está abierta
            if hasattr(main_window, "w") and main_window.w:
                main_window.w.close()

            # Desconectar del servidor y abrir ventana de conexión
            if hasattr(main_window, "conexion") and main_window.conexion:
                main_window.conexion.desconectar()

            # Abrir la ventana de conexión para que el usuario pueda
            # intentar con un nombre diferente
            main_window.abrir_ventana_conectar()
        else:
            # Mostrar diálogo genérico para otros tipos de error
            msg_box = QMessageBox(main_window)
            msg_box.setIcon(QMessageBox.Icon.Critical)
            msg_box.setWindowTitle(_("Error"))
            msg_box.setText(self._message or _("Ha ocurrido un error."))
            msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
            msg_box.exec()
