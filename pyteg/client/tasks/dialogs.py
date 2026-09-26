"""Diálogos iniciados por eventos de red sin bloquear el lector TCP."""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import Qt

if TYPE_CHECKING:
    from collections.abc import Callable

    from PySide6.QtWidgets import QMessageBox


def open_message_box(
    dialog: QMessageBox, *, on_finished: Callable[[], None] | None = None
) -> None:
    """Muestra un aviso y permite que ``readyRead`` siga procesando pings."""
    dialog.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
    if on_finished is not None:
        dialog.finished.connect(lambda _result: on_finished())
    dialog.open()
