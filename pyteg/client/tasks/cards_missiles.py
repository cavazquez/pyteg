"""Tareas del cliente: tarjetas y misiles."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pyteg.client.tasks.base import IClientTask
from pyteg.client.tasks.logging_helper import CLIENT_TASKS_LOG
from pyteg.client.tasks.types import (
    MisilAgregadoTaskData,
    ResultadoMisilTaskData,
    TarjetasJugadorTaskData,
)
from pyteg.i18n import ngettext
from pyteg.i18n import translate as _

if TYPE_CHECKING:
    from pyteg.client.tasks.protocols import GameWindowProtocol


class ClientTaskTarjetasJugador(IClientTask[TarjetasJugadorTaskData]):
    """Tarea para actualizar las tarjetas del jugador."""

    def __init__(self, data: TarjetasJugadorTaskData) -> None:
        """Inicializa la tarea de tarjetas del jugador.

        Args:
            data: Diccionario con la lista de tarjetas del jugador.

        """
        super().__init__(data)
        self._tarjetas = data.get("tarjetas", [])

    def run(self, main_window: GameWindowProtocol) -> None:
        """Actualiza las tarjetas del jugador en la GUI.

        Args:
            main_window: Ventana principal de la GUI

        """
        try:
            tarjetas_anteriores = getattr(main_window, "tarjetas_jugador", [])
            main_window.tarjetas_jugador = self._tarjetas

            if tarjetas_anteriores != self._tarjetas:
                main_window.sound_manager.play_card()

            CLIENT_TASKS_LOG.info(
                "Tarjetas del jugador actualizadas: %s tarjetas", len(self._tarjetas)
            )
            CLIENT_TASKS_LOG.debug(
                "ClientTaskTarjetasJugador: tarjetas=%s", self._tarjetas
            )

            main_window.refresh_open_tarjetas_dialogs(self._tarjetas)

        except (AttributeError, RuntimeError) as e:
            CLIENT_TASKS_LOG.warning("Error al procesar tarjetas del jugador: %s", e)


class ClientTaskResultadoMisil(IClientTask[ResultadoMisilTaskData]):
    """Tarea para procesar el resultado del lanzamiento de un misil."""

    def __init__(self, data: ResultadoMisilTaskData) -> None:
        """Inicializa la tarea de resultado de misil.

        Args:
            data: Diccionario con los datos del lanzamiento del misil.

        """
        super().__init__(data)
        self._jugador_id = data.get("jugador_id")
        self._jugador_fallback = data.get("jugador")
        self._pais_origen = data.get("pais_origen")
        self._pais_destino = data.get("pais_destino")
        self._distancia = data.get("distancia")
        self._dano = data.get("dano")
        self._unidades_restantes = data.get("unidades_restantes")

    def run(self, main_window: GameWindowProtocol) -> None:
        """Procesa el resultado del lanzamiento de un misil."""
        try:
            jugador_nombre: str | None = None
            if self._jugador_id is not None:
                cliente = main_window.client_by_id.get(int(self._jugador_id))
                if cliente is not None and hasattr(cliente, "username"):
                    jugador_nombre = cliente.username()
            if not jugador_nombre:
                jugador_nombre = self._jugador_fallback or str(self._jugador_id)

            mensaje = _(
                "🚀 {} lanzó un misil desde {} hacia {} (distancia: {}). "
                "Daño: {} unidades. Unidades restantes: {}"
            ).format(
                jugador_nombre,
                self._pais_origen,
                self._pais_destino,
                self._distancia,
                self._dano,
                self._unidades_restantes,
            )
            if main_window.chat is not None:
                main_window.chat.append(mensaje, "system")

            status_mensaje = _("Misil: {} → {} (-{} unidades)").format(
                self._pais_origen, self._pais_destino, self._dano
            )
            main_window.update_status_bar(status_mensaje, "blue")

        except (AttributeError, KeyError, TypeError) as e:
            CLIENT_TASKS_LOG.warning("Error al procesar resultado de misil: %s", e)


class ClientTaskMisilAgregado(IClientTask[MisilAgregadoTaskData]):
    """Tarea para notificar que se agregó un misil a un país."""

    def __init__(self, data: MisilAgregadoTaskData) -> None:
        """Inicializa la tarea de misil agregado.

        Args:
            data: Diccionario con el país y cantidad de misiles.

        """
        super().__init__(data)
        self._pais = data.get("pais")
        self._cantidad_misiles = data.get("cantidad_misiles")

    def run(self, main_window: GameWindowProtocol) -> None:
        """Ejecuta la tarea actualizando la cantidad de misiles en la interfaz."""
        try:
            if self._pais is None or self._cantidad_misiles is None:
                return

            if main_window.scene is not None:
                pais_widget = main_window.scene.obtener_pais(self._pais)
                if pais_widget and hasattr(pais_widget, "actualizar_misiles"):
                    pais_widget.actualizar_misiles(self._cantidad_misiles)

            mensaje = _("{} ahora tiene {} {}").format(
                self._pais,
                self._cantidad_misiles,
                ngettext("misil", "misiles", self._cantidad_misiles),
            )
            main_window.update_status_bar(mensaje, "blue")

        except (AttributeError, KeyError, TypeError) as e:
            CLIENT_TASKS_LOG.warning(
                "Error al actualizar misiles en %s: %s", self._pais, e
            )
