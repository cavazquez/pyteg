"""Cierre y destrucción de widgets en el hilo Qt entre pruebas."""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import QCoreApplication, QEvent
from shiboken6.Shiboken import isValid

if TYPE_CHECKING:
    from PySide6.QtCore import QObject
    from PySide6.QtWidgets import QWidget


def dispose_widget(widget: QWidget) -> None:
    """Libera el árbol Qt antes de que el GC de un hilo de red lo recoja."""
    if isValid(widget):
        widget.close()
        dispose_object(widget)


def dispose_object(obj: QObject) -> None:
    """Destruye también escenas sin padre antes de abandonar la prueba."""
    if isValid(obj):
        obj.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
