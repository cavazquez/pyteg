"""Recolecta los ciclos de objetos Qt exclusivamente en el hilo gráfico.

El motor entre pares crea muchos objetos en workers. El GC automático puede
destruir allí wrappers de escenas y efectos que sólo admite el hilo de Qt.
El conteo de referencias sigue funcionando; un timer Qt recoge los ciclos.
"""

from __future__ import annotations

import gc
from typing import TYPE_CHECKING

from PySide6.QtCore import QObject, QTimer, Slot

if TYPE_CHECKING:
    from PySide6.QtWidgets import QApplication


class GuiGarbageCollector(QObject):
    """Sustituye el GC automático mientras corre la aplicación gráfica."""

    def __init__(self, app: QApplication) -> None:
        """Comparte un único timer con todas las ventanas de la aplicación."""
        super().__init__(app)
        self.setObjectName("pyteg-gui-gc")
        self._previously_enabled = gc.isenabled()
        self._timer = QTimer(self)
        self._timer.setInterval(1000)
        self._timer.timeout.connect(self.collect)
        app.aboutToQuit.connect(self.stop)
        self.start()

    def start(self) -> None:
        """Evita que un worker active la destrucción cíclica de objetos Qt."""
        gc.disable()
        self._timer.start()

    @Slot()
    def collect(self) -> None:
        """Recoge los ciclos desde el timer que pertenece al hilo gráfico."""
        gc.collect()

    @Slot()
    def stop(self) -> None:
        """Recoge los últimos ciclos y restaura la configuración al salir."""
        self._timer.stop()
        self.collect()
        if self._previously_enabled:
            gc.enable()


def install_gui_collection(app: QApplication) -> GuiGarbageCollector:
    """Instala una sola recolección por aplicación, aunque haya varias ventanas.

    Returns:
        Recolector compartido, propiedad de la aplicación Qt.

    """
    collector = app.findChild(GuiGarbageCollector, "pyteg-gui-gc")
    if collector is None:
        collector = GuiGarbageCollector(app)
    elif not collector._timer.isActive():  # noqa: SLF001 -- servicio compartido del módulo.
        collector.start()
    return collector
