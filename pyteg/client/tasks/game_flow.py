"""Tareas del cliente: turno, tiempo, mapa y configuración."""

from __future__ import annotations

from typing import Any

from PySide6.QtWidgets import QMessageBox

from pyteg.client.tasks.base import IClientTask
from pyteg.client.tasks.logging_helper import CLIENT_TASKS_LOG
from pyteg.config import (
    DEFAULT_TURN_SECONDS,
    DEFAULT_VICTORY_COUNTRIES,
    TIMER_COLOR_GREEN_THRESHOLD,
    TIMER_COLOR_ORANGE_THRESHOLD,
)
from pyteg.i18n import _


class ClientTaskTurno(IClientTask):
    """Tarea para actualizar el turno actual del juego."""

    def __init__(self, data: dict[str, Any]) -> None:
        """Inicializa la tarea de turno.

        Args:
            data: Diccionario con información del turno.

        """
        super().__init__(data)
        self._msg = data

    def run(self, main_window: Any) -> None:
        """Ejecuta la tarea actualizando el turno en la interfaz."""
        num_turno = int(self._msg.get("num_turno", 0))
        num_ronda = int(
            self._msg.get("num_ronda", 1)
        )  # Por defecto 1 si no se especifica

        # Obtener información del jugador actual
        jugador_actual_id = self._msg.get("jugador_actual_id")
        jugador_actual_nombre = self._msg.get("jugador_actual_nombre")
        jugador_actual_color = self._msg.get("jugador_actual_color")

        main_window.update_turno(
            num_turno,
            num_ronda,
            jugador_actual_id,
            jugador_actual_nombre,
            jugador_actual_color,
        )

        # Reproducir sonido de cambio de turno
        if hasattr(main_window, "sound_manager"):
            main_window.sound_manager.play_turn()

        # Mostrar mensaje de inicio de turno en el chat
        main_window.chat.append(f"Turno {num_turno + 1} iniciado", "system")

        # Solicitar actualización de unidades disponibles al servidor
        # Esto debería ser manejado por el servidor enviando un mensaje
        # de unidades_disponibles


class ClientTaskTiempo(IClientTask):
    """Tarea para actualizar el tiempo restante del turno."""

    def __init__(self, data: dict[str, Any]) -> None:
        """Inicializa la tarea de tiempo.

        Args:
            data: Diccionario con el tiempo restante.

        """
        super().__init__(data)
        self._msg = data

    def run(self, main_window: Any) -> None:
        """Ejecuta la tarea actualizando el display del tiempo."""
        tiempo = int(self._msg.get("tiempo", 0))
        # Mostrar el tiempo restante en el widget dedicado del lado derecho
        if tiempo > 0:
            # Determinar color basado en tiempo restante
            if tiempo > TIMER_COLOR_GREEN_THRESHOLD:
                color = "green"
            elif tiempo > TIMER_COLOR_ORANGE_THRESHOLD:
                color = "orange"
            else:  # Muy poco tiempo - Rojo
                color = "red"

            main_window.update_timer_display(f"Tiempo: {tiempo}s", color=color)
        else:
            main_window.update_timer_display("")


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


class ClientTaskVictoria(IClientTask):
    """Tarea para mostrar el mensaje de victoria."""

    def __init__(self, data: dict[str, Any]) -> None:
        """Inicializa la tarea de victoria.

        Args:
            data: Diccionario con el ID y nombre del ganador.

        """
        super().__init__(data)
        self._ganador_id = data.get("ganador_id")
        self._ganador_nombre = data.get("ganador_nombre")

    def run(self, main_window: Any) -> None:
        """Muestra un mensaje de victoria cuando alguien gana la partida."""
        try:
            # Reproducir sonido de victoria
            if hasattr(main_window, "sound_manager"):
                main_window.sound_manager.play_victory()

            # Mostrar mensaje en la barra de estado
            if hasattr(main_window, "update_status_bar"):
                main_window.update_status_bar(
                    _("🏆 ¡{} ha ganado la partida!").format(self._ganador_nombre),
                    "green",
                )

            # Mostrar diálogo de victoria
            msg_box = QMessageBox(main_window)
            msg_box.setWindowTitle(_("¡Partida Terminada!"))
            msg_box.setIcon(QMessageBox.Icon.Information)
            msg_box.setText(_("🏆 ¡Felicitaciones!"))
            msg_box.setInformativeText(
                _(
                    "{} ha ganado la partida controlando el número objetivo de países."
                ).format(self._ganador_nombre)
            )
            msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
            msg_box.exec()

            # También mostrar en el chat
            if hasattr(main_window, "chat"):
                main_window.chat.append(
                    _("🏆 ¡{} ha ganado la partida!").format(self._ganador_nombre),
                    "system",
                )

        except (AttributeError, RuntimeError) as e:
            CLIENT_TASKS_LOG.warning("Error al mostrar mensaje de victoria: %s", e)


class ClientTaskConfiguracionPartida(IClientTask):
    """Tarea para procesar la configuración de la partida."""

    def __init__(self, data: dict[str, Any]) -> None:
        """Inicializa la tarea de configuración de partida.

        Args:
            data: Diccionario con la configuración de la partida.

        """
        super().__init__(data)
        self._segundos_por_turno = data.get("segundos_por_turno", DEFAULT_TURN_SECONDS)
        self._paises_para_victoria = data.get(
            "paises_para_victoria", DEFAULT_VICTORY_COUNTRIES
        )
        self._objetivos_secretos = data.get("objetivos_secretos", False)
        self._misiles_habilitados = data.get("misiles_habilitados", False)

    def run(self, main_window: Any) -> None:
        """Procesa la configuración de la partida.

        Almacena la configuración en la ventana principal.
        """
        try:
            # Almacenar la configuración en la ventana principal
            if hasattr(main_window, "set_configuracion_partida"):
                main_window.set_configuracion_partida(
                    self._segundos_por_turno,
                    self._paises_para_victoria,
                    objetivos_secretos=self._objetivos_secretos,
                    misiles_habilitados=self._misiles_habilitados,
                )

            # Mostrar mensaje en la barra de estado
            if hasattr(main_window, "update_status_bar"):
                if self._paises_para_victoria == 0:
                    objetivo_texto = _("todos los países")
                else:
                    objetivo_texto = _("{} países").format(self._paises_para_victoria)
                main_window.update_status_bar(
                    _("Objetivo: {} | Turno: {}s").format(
                        objetivo_texto, self._segundos_por_turno
                    ),
                    "blue",
                )

        except (AttributeError, RuntimeError) as e:
            CLIENT_TASKS_LOG.warning(
                "Error al procesar configuración de partida: %s", e
            )


class ClientTaskObjetivoSecreto(IClientTask):
    """Tarea para procesar el objetivo secreto asignado."""

    def __init__(self, data: dict[str, Any]) -> None:
        """Inicializa la tarea de objetivo secreto.

        Args:
            data: Diccionario con el ID y descripción del objetivo secreto.

        """
        super().__init__(data)
        self._objetivo_id = data.get("objetivo_id", "")
        self._descripcion = data.get("descripcion", "")

    def run(self, main_window: Any) -> None:
        """Procesa el objetivo secreto asignado.

        Lo almacena en la ventana principal.
        """
        try:
            CLIENT_TASKS_LOG.debug(
                "ClientTaskObjetivoSecreto: objetivo_id=%s desc=%s",
                self._objetivo_id,
                self._descripcion,
            )

            # Almacenar el objetivo secreto en la ventana principal
            if hasattr(main_window, "set_objetivo_secreto"):
                main_window.set_objetivo_secreto(self._objetivo_id, self._descripcion)
                CLIENT_TASKS_LOG.debug(
                    "ClientTaskObjetivoSecreto: objetivo almacenado en main_window"
                )
            else:
                CLIENT_TASKS_LOG.warning(
                    "ClientTaskObjetivoSecreto: main_window carece de "
                    "set_objetivo_secreto"
                )

            # Mostrar mensaje en el chat del sistema
            if hasattr(main_window, "chat"):
                main_window.chat.append(
                    _("Objetivo secreto asignado: {}").format(self._descripcion),
                    "system",
                )
                CLIENT_TASKS_LOG.debug(
                    "ClientTaskObjetivoSecreto: mensaje agregado al chat"
                )

        except (AttributeError, RuntimeError) as e:
            CLIENT_TASKS_LOG.warning("Error al procesar objetivo secreto: %s", e)
