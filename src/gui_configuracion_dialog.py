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

from src.i18n import translate as _


class ConfiguracionDialog(QDialog):
    """Diálogo para mostrar la configuración de la partida."""

    def __init__(
        self,
        parent: QWidget | None = None,
        segundos_por_turno: int = 20,
        paises_para_victoria: int = 30,
        *,
        objetivos_secretos: bool = False,
        misiles_habilitados: bool = False,
    ) -> None:
        """Inicializa el diálogo de configuración.

        Args:
            parent: Widget padre (opcional).
            segundos_por_turno: Duración de cada turno en segundos.
            paises_para_victoria: Cantidad de países necesarios para ganar.
            objetivos_secretos: Si los objetivos secretos están activados.
            misiles_habilitados: Si los misiles están habilitados.

        """
        super().__init__(parent)
        self.paises_para_victoria = paises_para_victoria
        self.objetivos_secretos = objetivos_secretos
        self.misiles_habilitados = misiles_habilitados
        self.setWindowTitle(_("Configuración de la Partida"))
        self.setFixedSize(350, 280)
        self.setModal(True)

        # Configurar el layout principal
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Título
        titulo = QLabel(_("Configuración de la Partida"))
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        titulo.setStyleSheet("font-weight: bold; font-size: 14px; margin-bottom: 10px;")
        layout.addWidget(titulo)

        # Grid layout para los datos
        grid_layout = QGridLayout()
        layout.addLayout(grid_layout)

        # Duración del turno
        duracion_label = QLabel(_("Duración del turno:"))
        duracion_label.setStyleSheet("font-weight: bold;")
        duracion_value = QLabel(_("{} segundos").format(segundos_por_turno))
        grid_layout.addWidget(duracion_label, 0, 0)
        grid_layout.addWidget(duracion_value, 0, 1)

        # Objetivo de países
        objetivo_label = QLabel(_("Países para ganar:"))
        objetivo_label.setStyleSheet("font-weight: bold;")
        if self.paises_para_victoria == 0:
            objetivo_text = _("Todos los países")
        else:
            objetivo_text = str(self.paises_para_victoria)
        objetivo_value = QLabel(objetivo_text)
        grid_layout.addWidget(objetivo_label, 1, 0)
        grid_layout.addWidget(objetivo_value, 1, 1)

        # Objetivos secretos
        objetivos_label = QLabel(_("Objetivos secretos:"))
        objetivos_label.setStyleSheet("font-weight: bold;")
        objetivos_text = (
            _("Activados") if self.objetivos_secretos else _("Desactivados")
        )
        objetivos_value = QLabel(objetivos_text)
        grid_layout.addWidget(objetivos_label, 2, 0)
        grid_layout.addWidget(objetivos_value, 2, 1)

        # Misiles
        misiles_label = QLabel(_("Misiles:"))
        misiles_label.setStyleSheet("font-weight: bold;")
        misiles_text = _("Activados") if self.misiles_habilitados else _("Desactivados")
        misiles_value = QLabel(misiles_text)
        grid_layout.addWidget(misiles_label, 3, 0)
        grid_layout.addWidget(misiles_value, 3, 1)

        # Separador
        layout.addSpacing(20)

        # Botón de cerrar
        boton_cerrar = QPushButton(_("Cerrar"))
        boton_cerrar.clicked.connect(self.accept)
        layout.addWidget(boton_cerrar)

        # Aplicar estilos
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
