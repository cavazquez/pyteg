"""Módulo para gestión de configuración de partida en la interfaz gráfica.

Este módulo contiene la clase ConfigManager que maneja toda la lógica
relacionada con la configuración de la partida.
"""

from __future__ import annotations

from typing import Any

from src.config import DEFAULT_TURN_SECONDS, DEFAULT_VICTORY_COUNTRIES
from src.gui_configuracion_dialog import ConfiguracionDialog


class ConfigManager:
    """Gestiona la configuración de la partida.

    Esta clase se encarga de almacenar y gestionar los parámetros de
    configuración de la partida, incluyendo objetivos secretos y misiles.
    """

    def __init__(self, main_window: Any) -> None:
        """Inicializa el gestor de configuración.

        Args:
            main_window: Referencia a la ventana principal (Gui)

        """
        self.main_window = main_window

        # Inicializar configuración por defecto
        self._segundos_por_turno = DEFAULT_TURN_SECONDS
        self._paises_para_victoria = DEFAULT_VICTORY_COUNTRIES
        self._objetivos_secretos = False
        self.misiles_habilitados = False

        # Inicializar variables para objetivo secreto
        self._objetivo_secreto_id: str | None = None
        self._objetivo_secreto_descripcion: str | None = None

    def set_configuracion_partida(
        self,
        segundos_por_turno: int,
        paises_para_victoria: int,
        *,
        objetivos_secretos: bool = False,
        misiles_habilitados: bool = False,
    ) -> None:
        """Establece la configuración de la partida.

        Args:
            segundos_por_turno: Duración de cada turno en segundos.
            paises_para_victoria: Número de países necesarios para ganar.
            objetivos_secretos: Si los objetivos secretos están activados.
            misiles_habilitados: Si el sistema de misiles está habilitado.

        """
        self._segundos_por_turno = segundos_por_turno
        self._paises_para_victoria = paises_para_victoria
        self._objetivos_secretos = objetivos_secretos
        self.misiles_habilitados = misiles_habilitados

        # Inicializar variables para objetivo secreto
        self._objetivo_secreto_id = None
        self._objetivo_secreto_descripcion = None

    def mostrar_configuracion_partida(self) -> None:
        """Muestra la ventana de configuración de la partida."""
        dialog = ConfiguracionDialog(
            self.main_window,
            self._segundos_por_turno,
            self._paises_para_victoria,
            objetivos_secretos=self._objetivos_secretos,
            misiles_habilitados=self.misiles_habilitados,
        )
        dialog.exec()

    @property
    def segundos_por_turno(self) -> int:
        """Obtiene los segundos por turno configurados."""
        return self._segundos_por_turno

    @property
    def paises_para_victoria(self) -> int:
        """Obtiene los países para victoria configurados."""
        return self._paises_para_victoria

    @property
    def objetivos_secretos(self) -> bool:
        """Obtiene si los objetivos secretos están habilitados."""
        return self._objetivos_secretos

    @property
    def objetivo_secreto_id(self) -> str | None:
        """Obtiene el ID del objetivo secreto asignado."""
        return self._objetivo_secreto_id

    @property
    def objetivo_secreto_descripcion(self) -> str | None:
        """Obtiene la descripción del objetivo secreto asignado."""
        return self._objetivo_secreto_descripcion

    def set_objetivo_secreto(
        self, objetivo_id: str | None, descripcion: str | None
    ) -> None:
        """Establece el objetivo secreto del jugador.

        Args:
            objetivo_id: ID del objetivo secreto.
            descripcion: Descripción del objetivo secreto.

        """
        self._objetivo_secreto_id = objetivo_id
        self._objetivo_secreto_descripcion = descripcion

        # Si hay un diálogo de tarjetas abierto, actualizarlo
        from src.gui_tarjetas_dialog import TarjetasDialog  # noqa: PLC0415

        for widget in self.main_window.findChildren(TarjetasDialog):
            if widget.isVisible():
                widget.set_objetivo_secreto(objetivo_id, descripcion)
