"""Módulo para el diálogo de configuración de la partida."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QGridLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from pyteg.config import DEFAULT_TURN_SECONDS, DEFAULT_VICTORY_COUNTRIES
from pyteg.i18n import translate as _


class ConfiguracionDialog(QDialog):
    """Diálogo para mostrar la configuración de la partida."""

    def __init__(
        self,
        parent: QWidget | None = None,
        segundos_por_turno: int | None = None,
        paises_para_victoria: int | None = None,
        *,
        objetivos_secretos: bool = False,
        misiles_habilitados: bool = False,
    ) -> None:
        """Inicializa el diálogo de configuración.

        Args:
            parent: Widget padre.
            segundos_por_turno: Segundos por turno.
            paises_para_victoria: Países necesarios para ganar.
            objetivos_secretos: Si los objetivos secretos están activados.
            misiles_habilitados: Si los misiles están habilitados.

        """
        if segundos_por_turno is None:
            segundos_por_turno = DEFAULT_TURN_SECONDS
        if paises_para_victoria is None:
            paises_para_victoria = DEFAULT_VICTORY_COUNTRIES
        super().__init__(parent)
        self.paises_para_victoria = paises_para_victoria
        self.objetivos_secretos = objetivos_secretos
        self.misiles_habilitados = misiles_habilitados
        self._build_ui(segundos_por_turno)

    def _build_ui(self, segundos_por_turno: int) -> None:
        self.setWindowTitle(_("Configuración de la Partida"))
        self.setFixedSize(350, 280)
        self.setModal(True)

        layout = QVBoxLayout()
        self.setLayout(layout)

        titulo = QLabel(_("Configuración de la Partida"))
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        titulo.setStyleSheet("font-weight: bold; font-size: 14px; margin-bottom: 10px;")
        layout.addWidget(titulo)

        grid_layout = QGridLayout()
        layout.addLayout(grid_layout)
        self._fill_config_grid(grid_layout, segundos_por_turno)

        layout.addSpacing(20)

        boton_cerrar = QPushButton(_("Cerrar"))
        boton_cerrar.clicked.connect(self.accept)
        layout.addWidget(boton_cerrar)

        self._apply_dialog_styles()

    def _fill_config_grid(
        self, grid_layout: QGridLayout, segundos_por_turno: int
    ) -> None:
        duracion_label = QLabel(_("Duración del turno:"))
        duracion_label.setStyleSheet("font-weight: bold;")
        duracion_value = QLabel(_("{} segundos").format(segundos_por_turno))
        grid_layout.addWidget(duracion_label, 0, 0)
        grid_layout.addWidget(duracion_value, 0, 1)

        objetivo_label = QLabel(_("Países para ganar:"))
        objetivo_label.setStyleSheet("font-weight: bold;")
        if self.paises_para_victoria == 0:
            objetivo_text = _("Todos los países")
        else:
            objetivo_text = str(self.paises_para_victoria)
        objetivo_value = QLabel(objetivo_text)
        grid_layout.addWidget(objetivo_label, 1, 0)
        grid_layout.addWidget(objetivo_value, 1, 1)

        objetivos_label = QLabel(_("Objetivos secretos:"))
        objetivos_label.setStyleSheet("font-weight: bold;")
        objetivos_text = (
            _("Activados") if self.objetivos_secretos else _("Desactivados")
        )
        objetivos_value = QLabel(objetivos_text)
        grid_layout.addWidget(objetivos_label, 2, 0)
        grid_layout.addWidget(objetivos_value, 2, 1)

        misiles_label = QLabel(_("Misiles:"))
        misiles_label.setStyleSheet("font-weight: bold;")
        misiles_text = _("Activados") if self.misiles_habilitados else _("Desactivados")
        misiles_value = QLabel(misiles_text)
        grid_layout.addWidget(misiles_label, 3, 0)
        grid_layout.addWidget(misiles_value, 3, 1)

    def _apply_dialog_styles(self) -> None:
        self.setStyleSheet("""
            QDialog {
                background-color: #f0f0f0;
            }
            QLabel {
                color: #333;
                padding: 5px;
            }
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
        """)
