"""Protocolo estructural de la ventana principal vista por los managers.

Extiende `GameWindowProtocol` (ver `pyteg.client.tasks.protocols`) con el
subconjunto de atributos y metodos adicionales que consumen los 10
managers y el panel de unidades. Asi se evita duplicar el contrato de
las tareas y se mantiene un superset claro.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol

from pyteg.client.tasks.protocols import GameWindowProtocol

if TYPE_CHECKING:
    from collections.abc import Callable


class MainWindowProtocol(GameWindowProtocol, Protocol):
    """Interfaz minima del `Gui` requerida por los managers (superset de GameWindow)."""

    theme: str
    turno_actual: int
    jugador_actual_id: int | None
    jugador_actual_nombre: str | None
    jugador_actual_color: str | None
    last_units: dict[str, Any]
    row_widgets: dict[str, Any]
    status_temp_label: Any

    view: Any
    toolbar: Any
    ventana_conectar: Any

    turno_label: Any
    timer_label: Any
    estado_label: Any
    mi_username_label: Any
    mi_color_indicator: Any
    mi_jugador_text: Any
    value_labels: Any
    player_labels: Any
    players_layout: Any
    right_column_widget: Any
    main_widget: Any

    theme_manager: Any
    players_manager: Any
    config_manager: Any
    layout_manager: Any
    language_manager: Any
    card_manager: Any
    window_manager: Any
    game_actions_manager: Any
    units_manager: Any
    status_manager: Any

    def setWindowTitle(self, title: str) -> None:  # noqa: N802
        """Establece el titulo de la ventana (heredado de QWidget)."""
        ...

    def setCentralWidget(self, widget: Any) -> None:  # noqa: N802
        """Establece el widget central (heredado de QMainWindow)."""
        ...

    def addToolBar(self, toolbar: Any) -> Any:  # noqa: N802
        """Agrega una toolbar (heredado de QMainWindow)."""
        ...

    def setMinimumSize(self, *args: Any, **kwargs: Any) -> None:  # noqa: N802
        """Tamaño minimo (heredado de QWidget)."""
        ...

    def setMouseTracking(self, *args: Any, **kwargs: Any) -> None:  # noqa: N802
        """Seguimiento de mouse (heredado de QWidget)."""
        ...

    def show(self) -> None:
        """Muestra la ventana (heredado de QWidget)."""
        ...

    findChildren: Callable[..., list[Any]]  # noqa: N815
