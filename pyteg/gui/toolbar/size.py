"""Menú de tamaño de ventana, estilos y acciones asociadas para la toolbar."""

from __future__ import annotations

import contextlib
from functools import partial
from typing import TYPE_CHECKING, Protocol, cast

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QAction, QScreen
from PySide6.QtWidgets import QApplication, QMenu, QToolButton, QWidget

from pyteg.exceptions import ImagenNoEncontradaError
from pyteg.gui.toolbar.icons import cargar_icono_toolbar
from pyteg.i18n import translate as _

if TYPE_CHECKING:
    from pyteg.gui.managers.protocols import MainWindowProtocol


class _ToolBarSizeTarget(Protocol):
    """Interfaz mínima de la barra para redimensionar ventana y menú de tamaños."""

    main_window: MainWindowProtocol
    button_fullscreen: QAction | None

    def resize_window(self, width: int, height: int) -> None: ...
    def fit_to_screen(self) -> None: ...


SIZE_TOOLBUTTON_STYLESHEET = """
    QToolButton {
        border: none;
        padding: 4px;
        border-radius: 4px;
    }
    QToolButton:hover {
        background-color: rgba(67, 97, 238, 0.1);
    }
    QToolButton:pressed {
        background-color: rgba(67, 97, 238, 0.2);
    }
"""


def predefined_window_size_rows() -> list[tuple[str, int, int, str]]:
    """Filas (texto traducido, ancho, alto, ícono) para tamaños predefinidos.

    Returns:
        Lista de tuplas para cada tamaño predefinido.

    """
    return [
        (_("Pequeño (800x600)"), 800, 600, "icons/size_small.png"),
        (_("Mediano (1024x768)"), 1024, 768, "icons/size_medium.png"),
        (_("Tamaño por defecto") + " (1280x800)", 1280, 800, "icons/size_large.png"),
    ]


def populate_size_menu(menu: QMenu, host: _ToolBarSizeTarget) -> None:
    """Deja las opciones comunes visibles y los tamaños fijos en un submenú."""
    menu.clear()

    action_parent = cast("QWidget", host)

    fit_action = QAction(_("Ajustar a la pantalla"), action_parent)
    with contextlib.suppress(ImagenNoEncontradaError):
        fit_action.setIcon(
            cargar_icono_toolbar("icons/fit_screen.png", "ajustar pantalla")
        )
    fit_action.triggered.connect(host.fit_to_screen)
    menu.addAction(fit_action)

    fullscreen_action = QAction(_("Pantalla Completa"), action_parent)
    with contextlib.suppress(ImagenNoEncontradaError):
        fullscreen_action.setIcon(
            cargar_icono_toolbar("icons/fullscreen.png", "pantalla completa")
        )
    fullscreen_action.triggered.connect(partial(host.resize_window, 0, 0))
    menu.addAction(fullscreen_action)

    menu.addSeparator()

    preset_menu = menu.addMenu(_("Tamaños predefinidos"))
    for text, width, height, icon_path in predefined_window_size_rows():
        act = QAction(text, action_parent)
        with contextlib.suppress(ImagenNoEncontradaError):
            act.setIcon(cargar_icono_toolbar(icon_path, f"tamaño {text}"))
        act.triggered.connect(partial(host.resize_window, width, height))
        preset_menu.addAction(act)


def create_size_menu(host: _ToolBarSizeTarget) -> QMenu:
    """Crea un `QMenu` de tamaños completo y estilado.

    Returns:
        Menú poblado y asociado al host (toolbar).

    """
    menu = QMenu(cast("QWidget", host))
    populate_size_menu(menu, host)
    return menu


def create_size_button(host: _ToolBarSizeTarget, size_menu: QMenu) -> QToolButton:
    """Botón con menú desplegable de tamaños (esquina derecha de la toolbar).

    Returns:
        `QToolButton` configurado con el menú de tamaños.

    """
    size_button = QToolButton(cast("QWidget", host))
    with contextlib.suppress(ImagenNoEncontradaError):
        size_button.setIcon(
            cargar_icono_toolbar("icons/resize.png", "botón de redimensionar")
        )
    size_button.setToolTip(_("Cambiar tamaño de la ventana"))
    size_button.setStatusTip(_("Ajustar o elegir tamaño de ventana"))
    size_button.setText(_("Cambiar tamaño de la ventana"))
    size_button.setAccessibleName(_("Cambiar tamaño de la ventana"))
    size_button.setAccessibleDescription(_("Ajustar o elegir tamaño de ventana"))
    size_button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
    size_button.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
    size_button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
    size_button.setMenu(size_menu)
    size_button.setIconSize(QSize(24, 24))
    size_button.setStyleSheet(SIZE_TOOLBUTTON_STYLESHEET)
    return size_button


def screen_for_window(main_window: QWidget | MainWindowProtocol) -> QScreen | None:
    """Devuelve la pantalla de la ventana, o la primaria como respaldo.

    Returns:
        La pantalla elegida, si hay alguna disponible.

    """
    qt_window = cast("QWidget", main_window)
    screen = qt_window.screen()
    return screen if isinstance(screen, QScreen) else QApplication.primaryScreen()


def center_window_on_screen(
    main_window: QWidget | MainWindowProtocol, screen: QScreen | None = None
) -> None:
    """Centra la ventana en la pantalla donde está ubicada."""
    selected_screen = screen if screen is not None else screen_for_window(main_window)
    if selected_screen is None:
        return
    qt_window = cast("QWidget", main_window)
    frame_geometry = qt_window.frameGeometry()
    screen_center = selected_screen.availableGeometry().center()
    frame_geometry.moveCenter(screen_center)
    qt_window.move(frame_geometry.topLeft())
