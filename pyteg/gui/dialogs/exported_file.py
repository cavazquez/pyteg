"""Acceso al archivo exportado para compartirlo por el medio elegido."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from pyteg.i18n import translate as _


class ExportedFileDialog(QDialog):
    """Permite copiar la ruta o abrir su carpeta sin enviar el archivo."""

    def __init__(self, path: Path, parent: QWidget) -> None:
        """Muestra la ubicación exacta del documento ya escrito."""
        super().__init__(parent)
        self.setWindowTitle(_("Archivo exportado"))
        self.resize(600, 150)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(_("El archivo está listo para compartir:")))
        self.path_field = QLineEdit(str(path.resolve()))
        self.path_field.setReadOnly(True)
        layout.addWidget(self.path_field)
        row = QHBoxLayout()
        self.copy_button = QPushButton(_("Copiar ruta"))
        self.copy_button.clicked.connect(self._copy)
        self.folder_button = QPushButton(_("Abrir carpeta"))
        self.folder_button.clicked.connect(self._folder)
        close = QPushButton(_("Cerrar"))
        close.clicked.connect(self.accept)
        for button in (self.copy_button, self.folder_button, close):
            row.addWidget(button)
        layout.addLayout(row)

    def _copy(self) -> None:
        QApplication.clipboard().setText(self.path_field.text())

    def _folder(self) -> None:
        QDesktopServices.openUrl(
            QUrl.fromLocalFile(str(Path(self.path_field.text()).parent))
        )
