"""Pruebas de layout adaptable y paneles colapsables."""

# ruff: noqa: D102, FBT003, PLC0415, SLF001

from __future__ import annotations

import unittest
from types import SimpleNamespace
from typing import TYPE_CHECKING, ClassVar, cast
from unittest.mock import MagicMock

from PySide6.QtCore import QEvent, QPointF, QSize, Qt
from PySide6.QtGui import QMouseEvent
from PySide6.QtWidgets import QApplication, QMainWindow, QSplitter, QWidget

from pyteg.client.app import Client
from pyteg.config import DEFAULT_MAP_THEME
from pyteg.gui import Gui
from pyteg.gui.managers.layout import LayoutManager
from pyteg.gui.toolbar.toolbar import ToolBar
from pyteg.gui.toolbar.window_mixin import ToolBarWindowMixin
from pyteg.gui.widgets.view import QCustomGraphicsView

if TYPE_CHECKING:
    from pyteg.gui.managers.protocols import MainWindowProtocol
    from pyteg.gui.widgets.chat import Chat


class _WindowMixinHost(ToolBarWindowMixin):
    """Host mínimo para probar los toggles de paneles."""

    def __init__(self, main_window: object) -> None:
        self.main_window: MainWindowProtocol = cast("MainWindowProtocol", main_window)
        self.button_fullscreen = MagicMock()
        self.button_toggle_chat = MagicMock()
        self.button_toggle_sidebar = MagicMock()


class GuiLayoutTests(unittest.TestCase):
    """El mapa conserva espacio y los paneles se pueden ocultar."""

    app: ClassVar[QApplication]

    @classmethod
    def setUpClass(cls) -> None:
        cls.app = cast("QApplication", QApplication.instance() or QApplication([]))

    def test_splitters_y_panel_derecho_son_colapsables_y_scrollables(self) -> None:
        window = cast("MainWindowProtocol", QMainWindow())
        window.view = cast("QCustomGraphicsView", QWidget())
        window.chat = cast("Chat", QWidget())
        window.map_theme = DEFAULT_MAP_THEME
        window.theme_manager = MagicMock()
        manager = LayoutManager(window)

        vertical = manager._create_vertical_splitter()
        horizontal = manager._create_horizontal_splitter(vertical)
        manager._setup_right_column()
        manager._setup_main_layout(horizontal)

        self.assertEqual(vertical.count(), 2)
        self.assertTrue(vertical.isCollapsible(1))
        self.assertIs(window.vertical_splitter, vertical)
        self.assertIs(window.horizontal_splitter, horizontal)
        self.assertEqual(horizontal.count(), 2)
        self.assertTrue(horizontal.isCollapsible(1))
        self.assertTrue(window.right_column_scroll.widgetResizable())

    def test_toggles_ocultan_chat_y_panel_sin_destruirlos(self) -> None:
        chat = QWidget()
        sidebar = QWidget()
        vertical = QSplitter(Qt.Orientation.Vertical)
        vertical.addWidget(QWidget())
        vertical.addWidget(chat)
        vertical.setSizes([300, 120])
        horizontal = QSplitter(Qt.Orientation.Horizontal)
        horizontal.addWidget(QWidget())
        horizontal.addWidget(sidebar)
        horizontal.setSizes([500, 240])
        host = _WindowMixinHost(
            SimpleNamespace(
                chat=chat,
                right_column_scroll=sidebar,
                vertical_splitter=vertical,
                horizontal_splitter=horizontal,
            )
        )

        host.toggle_chat(False)
        host.toggle_sidebar(False)
        self.assertTrue(chat.isHidden())
        self.assertTrue(sidebar.isHidden())

        host.toggle_chat(True)
        host.toggle_sidebar(True)
        self.assertFalse(chat.isHidden())
        self.assertFalse(sidebar.isHidden())

    def test_toolbar_usa_solo_iconos_en_ancho_reducido(self) -> None:
        toolbar = ToolBar("test", MagicMock())

        toolbar.update_responsive_layout(1024)
        self.assertEqual(
            toolbar.toolButtonStyle(), Qt.ToolButtonStyle.ToolButtonIconOnly
        )
        toolbar.update_responsive_layout(1280)
        self.assertEqual(
            toolbar.toolButtonStyle(),
            Qt.ToolButtonStyle.ToolButtonTextBesideIcon,
        )

    def test_resize_no_reajusta_un_zoom_manual(self) -> None:
        from PySide6.QtWidgets import QGraphicsScene

        scene = QGraphicsScene()
        scene.setSceneRect(0, 0, 1000, 600)
        view = QCustomGraphicsView(scene, MagicMock())
        view.resize(700, 400)
        self.app.processEvents()
        view._auto_fit_on_resize = False
        transform = view.transform()

        view.resize(500, 300)
        self.app.processEvents()

        self.assertEqual(view.transform(), transform)
        view.reset_zoom()
        self.assertTrue(view._auto_fit_on_resize)

    def test_boton_central_desplaza_el_mapa_sin_activar_seleccion(self) -> None:
        from PySide6.QtWidgets import QGraphicsScene

        scene = QGraphicsScene()
        scene.setSceneRect(0, 0, 1000, 600)
        view = QCustomGraphicsView(scene, MagicMock())
        view.resize(300, 200)
        self.app.processEvents()

        press = QMouseEvent(
            QEvent.Type.MouseButtonPress,
            QPointF(100, 100),
            Qt.MouseButton.MiddleButton,
            Qt.MouseButton.MiddleButton,
            Qt.KeyboardModifier.NoModifier,
        )
        view.mousePressEvent(press)
        self.assertFalse(view._auto_fit_on_resize)
        self.assertIsNotNone(view._pan_last_position)

        move = QMouseEvent(
            QEvent.Type.MouseMove,
            QPointF(80, 80),
            Qt.MouseButton.NoButton,
            Qt.MouseButton.MiddleButton,
            Qt.KeyboardModifier.NoModifier,
        )
        view.mouseMoveEvent(move)

        release = QMouseEvent(
            QEvent.Type.MouseButtonRelease,
            QPointF(80, 80),
            Qt.MouseButton.MiddleButton,
            Qt.MouseButton.NoButton,
            Qt.KeyboardModifier.NoModifier,
        )
        view.mouseReleaseEvent(release)
        self.assertIsNone(view._pan_last_position)

    def test_tamanos_soportados_conservan_mapa_y_paneles_accesibles(self) -> None:
        window = Gui(Client())
        try:
            for width, height in ((1024, 600), (1280, 800), (1920, 1080)):
                window.resize(QSize(width, height))
                self.app.processEvents()
                self.assertEqual(window.size(), QSize(width, height))
                view = window.view
                chat = window.chat
                if view is None or chat is None:
                    self.fail("La GUI debe crear vista y chat al iniciar")
                self.assertGreater(view.width(), 0)
                self.assertGreater(view.height(), 0)
                self.assertGreater(window.right_column_scroll.height(), 0)
                self.assertLessEqual(chat.height(), 160)
                self.assertGreaterEqual(chat.height(), 72)
                self.assertGreaterEqual(window.right_column_scroll.width(), 220)
                self.assertGreater(view.width(), window.right_column_scroll.width())
        finally:
            window.close()

    def test_estado_global_y_contexto_de_turno_se_muestran_por_separado(self) -> None:
        window = Gui(Client())
        try:
            window.status_manager.update_game_state("JUGANDO")
            window.fase_actual = "colocacion"
            window.jugador_actual_nombre = "Ana"
            window.unidades_pendientes_servidor = 4
            window.status_manager.update_gameplay_context()

            self.assertIn("En Juego", window.estado_label.text())
            self.assertIn("Ana", window.contexto_partida_label.text())
            self.assertIn("4", window.contexto_partida_label.text())
            self.assertTrue(window.contexto_partida_label.isVisible())
        finally:
            window.close()


if __name__ == "__main__":
    unittest.main()
