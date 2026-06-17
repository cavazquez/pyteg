"""Protocolo estructural de la ventana principal vista por los managers.

Extiende `GameWindowProtocol` (ver `pyteg.client.tasks.protocols`) con el
subconjunto de atributos y métodos adicionales que consumen los managers y
el panel de unidades. Así se evita duplicar el contrato de las tareas y se
mantiene un superset claro.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol

from pyteg.client.tasks.protocols import GameWindowProtocol

if TYPE_CHECKING:
    from collections.abc import Callable

    from PySide6.QtWidgets import (
        QFrame,
        QLabel,
        QToolBar,
        QVBoxLayout,
        QWidget,
    )

    from pyteg.gui.dialogs.conectar import VentanaConectar
    from pyteg.gui.managers.cards import CardManager
    from pyteg.gui.managers.config import ConfigManager
    from pyteg.gui.managers.game_actions import GameActionsManager
    from pyteg.gui.managers.language import LanguageManager
    from pyteg.gui.managers.layout import LayoutManager
    from pyteg.gui.managers.players import PlayersManager
    from pyteg.gui.managers.status import StatusManager
    from pyteg.gui.managers.theme import ThemeManager
    from pyteg.gui.managers.units import UnitsManager
    from pyteg.gui.managers.window import WindowManager
    from pyteg.gui.toolbar import ToolBar
    from pyteg.gui.widgets.view import QCustomGraphicsView


class MainWindowProtocol(GameWindowProtocol, Protocol):
    """Interfaz mínima del `Gui` requerida por los managers.

    Es un superset estructural de `GameWindowProtocol`.
    """

    theme: str
    turno_actual: int
    jugador_actual_id: int | None
    jugador_actual_nombre: str | None
    jugador_actual_color: str | None
    last_units: dict[str, int]
    row_widgets: dict[str, QFrame]
    value_labels: dict[str, QLabel]
    status_temp_label: QLabel | None
    players_title_label: QLabel | None
    units_section_title_label: QLabel | None

    view: QCustomGraphicsView | None
    toolbar: ToolBar | None
    ventana_conectar: VentanaConectar | None

    turno_label: QLabel
    timer_label: QLabel
    estado_label: QLabel
    mi_username_label: QLabel
    mi_color_indicator: QLabel
    mi_jugador_text: QLabel
    player_labels: list[tuple[QLabel, QLabel, QFrame]]
    players_layout: QVBoxLayout
    right_column_widget: QWidget
    main_widget: QWidget

    theme_manager: ThemeManager
    players_manager: PlayersManager
    config_manager: ConfigManager
    layout_manager: LayoutManager
    language_manager: LanguageManager
    card_manager: CardManager
    window_manager: WindowManager
    game_actions_manager: GameActionsManager
    units_manager: UnitsManager
    status_manager: StatusManager

    def setWindowTitle(self, title: str) -> None:  # noqa: N802
        """Establece el título de la ventana (heredado de QWidget)."""
        ...

    def setCentralWidget(self, widget: QWidget) -> None:  # noqa: N802
        """Establece el widget central (heredado de QMainWindow)."""
        ...

    def addToolBar(self, toolbar: QToolBar) -> QToolBar:  # noqa: N802
        """Agrega una toolbar (heredado de QMainWindow)."""
        ...

    def setMinimumSize(self, *args: Any, **kwargs: Any) -> None:  # noqa: N802
        """Tamaño mínimo (heredado de QWidget)."""
        ...

    def setMouseTracking(self, *args: Any, **kwargs: Any) -> None:  # noqa: N802
        """Seguimiento de mouse (heredado de QWidget)."""
        ...

    def show(self) -> None:
        """Muestra la ventana (heredado de QWidget)."""
        ...

    def atacar(self) -> None:
        """Acción de la toolbar para iniciar un ataque."""
        ...

    def finalizar_turno(self) -> None:
        """Acción de la toolbar para finalizar el turno actual."""
        ...

    def mostrar_tarjetas(self) -> None:
        """Acción de la toolbar para mostrar las tarjetas del jugador."""
        ...

    def mostrar_configuracion_partida(self) -> None:
        """Acción de la toolbar para mostrar la configuración de la partida."""
        ...

    def showNormal(self) -> None:  # noqa: N802
        """Muestra la ventana en modo normal (heredado de QWidget)."""
        ...

    def showFullScreen(self) -> None:  # noqa: N802
        """Muestra la ventana en pantalla completa (heredado de QWidget)."""
        ...

    def isFullScreen(self) -> bool:  # noqa: N802
        """Indica si la ventana está en pantalla completa (heredado de QWidget)."""
        ...

    def resize(self, *args: Any, **kwargs: Any) -> None:
        """Cambia el tamaño de la ventana (heredado de QWidget)."""
        ...

    findChildren: Callable[..., list[Any]]  # noqa: N815
