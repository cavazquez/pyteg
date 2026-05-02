"""Tareas del cliente: tarjetas y misiles."""

from __future__ import annotations

from typing import Any

from pyteg.client.tasks.base import IClientTask
from pyteg.client.tasks.logging_helper import CLIENT_TASKS_LOG
from pyteg.gui.tarjetas import TarjetasDialog


class ClientTaskTarjetasJugador(IClientTask):
    """Tarea para actualizar las tarjetas del jugador."""

    def __init__(self, data: dict[str, Any]) -> None:
        """Inicializa la tarea de tarjetas del jugador.

        Args:
            data: Diccionario con la lista de tarjetas del jugador.

        """
        super().__init__(data)
        self._tarjetas = data.get("tarjetas", [])

    def run(self, main_window: Any) -> None:
        """Actualiza las tarjetas del jugador en la GUI.

        Args:
            main_window: Ventana principal de la GUI

        """
        try:
            # Almacenar las tarjetas en la GUI para uso posterior
            if hasattr(main_window, "tarjetas_jugador"):
                main_window.tarjetas_jugador = self._tarjetas
            else:
                # Si no existe el atributo, crearlo
                main_window.tarjetas_jugador = self._tarjetas

            CLIENT_TASKS_LOG.info(
                "Tarjetas del jugador actualizadas: %s tarjetas", len(self._tarjetas)
            )
            CLIENT_TASKS_LOG.debug(
                "ClientTaskTarjetasJugador: tarjetas=%s", self._tarjetas
            )

            # Si hay un diálogo de tarjetas abierto, actualizarlo
            for widget in main_window.findChildren(TarjetasDialog):
                if widget.isVisible():
                    widget.actualizar_tarjetas(self._tarjetas)
                    CLIENT_TASKS_LOG.info(
                        "Diálogo de tarjetas actualizado automáticamente"
                    )

        except (AttributeError, RuntimeError) as e:
            CLIENT_TASKS_LOG.warning("Error al procesar tarjetas del jugador: %s", e)


class ClientTaskResultadoMisil(IClientTask):
    """Tarea para procesar el resultado del lanzamiento de un misil."""

    def __init__(self, data: dict[str, Any]) -> None:
        """Inicializa la tarea de resultado de misil.

        Args:
            data: Diccionario con los datos del lanzamiento del misil.

        """
        super().__init__(data)
        self._jugador = data.get("jugador")
        self._pais_origen = data.get("pais_origen")
        self._pais_destino = data.get("pais_destino")
        self._distancia = data.get("distancia")
        self._dano = data.get("dano")
        self._unidades_restantes = data.get("unidades_restantes")

    def run(self, main_window: Any) -> None:
        """Procesa el resultado del lanzamiento de un misil."""
        try:
            # Mostrar mensaje en el chat
            mensaje = (
                f"🚀 {self._jugador} lanzó un misil desde {self._pais_origen} "
                f"hacia {self._pais_destino} (distancia: {self._distancia}). "
                f"Daño: {self._dano} unidades. "
                f"Unidades restantes: {self._unidades_restantes}"
            )
            main_window.chat.append(mensaje, "system")

            # Mostrar mensaje temporal en barra de estado
            if hasattr(main_window, "status_bar"):
                status_mensaje = (
                    f"Misil: {self._pais_origen} → {self._pais_destino} "
                    f"(-{self._dano} unidades)"
                )
                main_window.status_bar.showMessage(status_mensaje, 5000)

        except (AttributeError, KeyError, TypeError) as e:
            CLIENT_TASKS_LOG.warning("Error al procesar resultado de misil: %s", e)


class ClientTaskMisilAgregado(IClientTask):
    """Tarea para notificar que se agregó un misil a un país."""

    def __init__(self, data: dict[str, Any]) -> None:
        """Inicializa la tarea de misil agregado.

        Args:
            data: Diccionario con el país y cantidad de misiles.

        """
        super().__init__(data)
        self._pais = data.get("pais")
        self._cantidad_misiles = data.get("cantidad_misiles")

    def run(self, main_window: Any) -> None:
        """Ejecuta la tarea actualizando la cantidad de misiles en la interfaz."""
        try:
            # Actualizar visualmente el país en el mapa
            # (Esto se implementará en la GUI cuando agregue el indicador visual)
            if hasattr(main_window, "scene") and main_window.scene:
                pais_widget = main_window.scene.obtener_pais(self._pais)
                if pais_widget and hasattr(pais_widget, "actualizar_misiles"):
                    pais_widget.actualizar_misiles(self._cantidad_misiles)

            # Mensaje en barra de estado
            if hasattr(main_window, "status_bar"):
                mensaje = f"{self._pais} ahora tiene {self._cantidad_misiles} misil(es)"
                main_window.status_bar.showMessage(mensaje, 3000)

        except (AttributeError, KeyError, TypeError) as e:
            CLIENT_TASKS_LOG.warning(
                "Error al actualizar misiles en %s: %s", self._pais, e
            )
