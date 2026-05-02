"""Menú de tamaño de ventana, estilos y acciones asociadas para la toolbar."""

from __future__ import annotations

import contextlib
from functools import partial
from typing import Any, Protocol, cast

from PySide6.QtCore import QSize
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QApplication, QMenu, QToolButton, QWidget

from pyteg.exception import ImagenNoEncontradaError
from pyteg.gui_toolbar_icons import cargar_icono_toolbar
from pyteg.i18n import translate as _


class _ToolBarSizeTarget(Protocol):
    """Interfaz mínima de la barra para redimensionar ventana y menú de tamaños."""

    main_window: Any
    button_fullscreen: QAction | None

    def resize_window(self, width: int, height: int) -> None: ...
    def fit_to_screen(self) -> None: ...


SIZE_MENU_STYLESHEET = """
    QMenu {
        background-color: #f8f9fa;
        border: 1px solid #dee2e6;
        border-radius: 4px;
        padding: 5px;
    }
    QMenu::item {
        padding: 6px 25px 6px 30px;
        border-radius: 3px;
        margin: 2px;
    }
    QMenu::item:selected {
        background-color: #4361ee;
        color: white;
    }
    QMenu::icon {
        padding-left: 10px;
    }
    QMenu::separator {
        height: 1px;
        background: #dee2e6;
        margin: 5px 10px;
    }
"""

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
    QToolButton::menu-indicator {
        image: none;
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
        (_("Grande (1280x800)"), 1280, 800, "icons/size_large.png"),
    ]


def populate_size_menu(menu: QMenu, host: _ToolBarSizeTarget) -> None:
    """Llena el menú: tamaños fijos, pantalla completa, ajustar, tamaño por defecto."""
    menu.clear()
    menu.setStyleSheet(SIZE_MENU_STYLESHEET)

    action_parent = cast("QWidget", host)

    menu.addSection(_("Tamaños predefinidos"))
    for text, width, height, icon_path in predefined_window_size_rows():
        act = QAction(text, action_parent)
        with contextlib.suppress(ImagenNoEncontradaError):
            act.setIcon(cargar_icono_toolbar(icon_path, f"tamaño {text}"))
        act.triggered.connect(partial(host.resize_window, width, height))
        menu.addAction(act)

    menu.addSeparator()

    fullscreen_action = QAction(_("Pantalla Completa"), action_parent)
    with contextlib.suppress(ImagenNoEncontradaError):
        fullscreen_action.setIcon(
            cargar_icono_toolbar("icons/fullscreen.png", "pantalla completa")
        )
    fullscreen_action.triggered.connect(partial(host.resize_window, 0, 0))
    menu.addAction(fullscreen_action)

    fit_action = QAction(_("Ajustar a la pantalla"), action_parent)
    with contextlib.suppress(ImagenNoEncontradaError):
        fit_action.setIcon(
            cargar_icono_toolbar("icons/fit_screen.png", "ajustar pantalla")
        )
    fit_action.triggered.connect(host.fit_to_screen)
    menu.addAction(fit_action)

    menu.addSeparator()

    default_action = QAction(_("Tamaño por defecto"), action_parent)
    with contextlib.suppress(ImagenNoEncontradaError):
        default_action.setIcon(
            cargar_icono_toolbar("icons/default_size.png", "tamaño por defecto")
        )
    default_action.triggered.connect(partial(host.resize_window, 1280, 800))
    menu.addAction(default_action)


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
    size_button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
    size_button.setMenu(size_menu)
    size_button.setIconSize(QSize(24, 24))
    size_button.setStyleSheet(SIZE_TOOLBUTTON_STYLESHEET)
    return size_button


def center_window_on_screen(main_window: Any) -> None:
    """Centra la ventana principal en la pantalla disponible."""
    frame_geometry = main_window.frameGeometry()
    screen_center = QApplication.primaryScreen().availableGeometry().center()
    frame_geometry.moveCenter(screen_center)
    main_window.move(frame_geometry.topLeft())
