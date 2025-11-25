"""Módulo para la ventana de administración del juego."""

from __future__ import annotations

from typing import Any

from PySide6.QtGui import QIntValidator
from PySide6.QtWidgets import (
    QCheckBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from src.config import DEFAULT_TURN_SECONDS


class VentanaAdmin(QWidget):
    """Ventana de administración para configurar parámetros de la partida."""

    def __init__(self, main_window: Any) -> None:
        """Inicializa la ventana de administración.

        Args:
            main_window: Ventana principal de la aplicación.

        """
        super().__init__()
        self.main_window = main_window
        self.setWindowTitle("Admin")

        self._layout = QVBoxLayout()

        # Fila para ingresar los segundos
        self.seconds_layout = QHBoxLayout()
        self.seconds_label = QLabel("Duración del turno (segundos):")
        self.seconds_input = QLineEdit()
        self.seconds_input.setPlaceholderText("p. ej., 30, 60, 120")
        self.seconds_input.setToolTip("Duración del turno en segundos")
        self.seconds_input.setValidator(QIntValidator(0, 3600, self))
        self.seconds_input.setText(str(DEFAULT_TURN_SECONDS))  # valor por defecto

        self.seconds_layout.addWidget(self.seconds_label)
        self.seconds_layout.addWidget(self.seconds_input)

        self._layout.addLayout(self.seconds_layout)

        # Checkbox para habilitar objetivo específico de países
        self.countries_checkbox = QCheckBox("Objetivo específico de países")
        self.countries_checkbox.setChecked(True)  # habilitado por defecto (50 países)
        self.countries_checkbox.setToolTip(
            "Activar para usar un objetivo específico de países "
            "en lugar de controlar todos"
        )
        self._layout.addWidget(self.countries_checkbox)

        # Fila para ingresar países para ganar
        self.countries_layout = QHBoxLayout()
        self.countries_label = QLabel("Países para ganar:")
        self.countries_input = QLineEdit()
        self.countries_input.setPlaceholderText("p. ej., 30, 50, 42")
        self.countries_input.setToolTip("Cantidad de países necesarios para ganar")
        self.countries_input.setValidator(QIntValidator(1, 999, self))
        self.countries_input.setText("50")  # valor por defecto

        self.countries_layout.addWidget(self.countries_label)
        self.countries_layout.addWidget(self.countries_input)

        self._layout.addLayout(self.countries_layout)

        # Checkbox para habilitar objetivos secretos
        self.objetivos_secretos_checkbox = QCheckBox("Objetivos secretos")
        self.objetivos_secretos_checkbox.setChecked(True)
        self.objetivos_secretos_checkbox.setToolTip(
            "Activar para usar objetivos secretos del TEG clásico "
            "en lugar de solo conquistar países"
        )
        self._layout.addWidget(self.objetivos_secretos_checkbox)

        # Checkbox para habilitar misiles
        self.misiles_checkbox = QCheckBox("Habilitar Misiles")
        self.misiles_checkbox.setChecked(True)  # habilitado por defecto
        self.misiles_checkbox.setToolTip(
            "Activar para permitir canjear y lanzar misiles durante la partida"
        )
        self._layout.addWidget(self.misiles_checkbox)

        # Conectar checkbox para habilitar/deshabilitar el campo de países
        self.countries_checkbox.toggled.connect(self._toggle_countries_input)

        self.button = QPushButton("Empezar")
        self.button.clicked.connect(self.empezar)
        # Permitir activar con Enter
        self.button.setDefault(True)
        self.button.setAutoDefault(True)
        self.seconds_input.returnPressed.connect(self.empezar)
        self.countries_input.returnPressed.connect(self.empezar)

        self._layout.addWidget(self.button)
        self.setLayout(self._layout)

        # Inicializar estado del campo de países
        self._toggle_countries_input(self.countries_checkbox.isChecked())

    def _toggle_countries_input(self, enabled: bool) -> None:  # noqa: FBT001
        """Habilita o deshabilita el campo de países según el checkbox."""
        self.countries_input.setEnabled(enabled)
        self.countries_label.setEnabled(enabled)

    def empezar(self) -> None:
        """Inicia la partida con la configuración ingresada."""
        # Leer y validar los segundos ingresados
        segundos = None
        if self.seconds_input.text().strip():
            try:
                segundos = int(self.seconds_input.text())
            except ValueError:
                segundos = None

        # Leer y validar los países para ganar según el checkbox
        paises_para_victoria = None
        if self.countries_checkbox.isChecked():
            # Checkbox habilitado: usar valor específico del campo
            if self.countries_input.text().strip():
                try:
                    paises_para_victoria = int(self.countries_input.text())
                except ValueError:
                    paises_para_victoria = None
        else:
            # Checkbox deshabilitado: usar 0 para indicar "todos los países"
            paises_para_victoria = 0

        # Leer configuración de objetivos secretos
        objetivos_secretos = self.objetivos_secretos_checkbox.isChecked()

        # Leer configuración de misiles
        misiles_habilitados = self.misiles_checkbox.isChecked()

        transmisor = getattr(self.main_window, "transmisor", None)
        if transmisor is not None:
            transmisor.empezar(
                segundos,
                paises_para_victoria,
                objetivos_secretos=objetivos_secretos,
                misiles_habilitados=misiles_habilitados,
            )
        self.close()

    def cargar_colores_asignados(self) -> None:
        """Método no-op para el admin.

        El cliente admin no visualiza la lista de colores como la ventana
        principal, pero algunos tasks del cliente invocan este método.
        Definirlo evita errores cuando el admin está abierto.
        """
