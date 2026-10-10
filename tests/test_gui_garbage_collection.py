"""El GC que puede destruir objetos Qt pertenece al hilo de la interfaz."""

from __future__ import annotations

import gc
import threading
import unittest
from typing import ClassVar, cast
from unittest.mock import patch

from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from pyteg.gui.garbage_collection import GuiGarbageCollector, install_gui_collection
from tests.qt_fixtures import dispose_object


class GuiGarbageCollectionTests(unittest.TestCase):
    """Varios clientes comparten un timer y restauran el GC al salir."""

    app: ClassVar[QApplication]

    @classmethod
    def setUpClass(cls) -> None:
        """Reutiliza la aplicación Qt creada por la suite."""
        cls.app = cast("QApplication", QApplication.instance() or QApplication([]))

    def test_all_windows_share_one_collector_on_the_gui_thread(self) -> None:
        """Instalar el servicio otra vez no crea timers ni habilita GC en workers."""
        first = install_gui_collection(self.app)
        self.assertIs(first, install_gui_collection(self.app))
        self.assertIs(first.parent(), self.app)
        self.assertEqual(first.thread(), self.app.thread())
        self.assertFalse(gc.isenabled())

    def test_timer_collects_only_from_the_thread_processing_qt(self) -> None:
        """Un ciclo del timer realiza la recolección en el hilo del QApplication."""
        install_gui_collection(self.app)
        callers: list[int] = []
        with patch(
            "pyteg.gui.garbage_collection.gc.collect",
            side_effect=lambda: callers.append(threading.get_ident()),
        ):
            QTest.qWait(1100)
        self.assertTrue(callers)
        self.assertEqual(set(callers), {threading.get_ident()})

    def test_shutdown_restores_the_previous_gc_setting(self) -> None:
        """El servicio no altera permanentemente la configuración de Python."""
        with (
            patch("pyteg.gui.garbage_collection.gc.isenabled", return_value=True),
            patch("pyteg.gui.garbage_collection.gc.disable") as disable,
            patch("pyteg.gui.garbage_collection.gc.enable") as enable,
            patch("pyteg.gui.garbage_collection.gc.collect") as collect,
        ):
            collector = GuiGarbageCollector(self.app)
            collector.stop()
            disable.assert_called_once_with()
            collect.assert_called_once_with()
            enable.assert_called_once_with()
            dispose_object(collector)


if __name__ == "__main__":
    unittest.main()
