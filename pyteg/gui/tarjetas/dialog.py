"""Diálogo modal de tarjetas del jugador."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from pyteg.i18n import translate as _

from . import styles
from .exchange_mixin import TarjetasExchangeMixin
from .selection_mixin import TarjetasSelectionMixin

if TYPE_CHECKING:
    from pyteg.gui.widgets.tarjeta import TarjetaWidget


class TarjetasDialog(TarjetasExchangeMixin, TarjetasSelectionMixin, QDialog):
    """Diálogo para mostrar las tarjetas asignadas al jugador."""

    def __init__(self, parent: QWidget | None = None) -> None:
        """Inicializa el diálogo de tarjetas.

        Args:
            parent: Widget padre (opcional).

        """
        super().__init__(parent)
        self.setWindowTitle(_("Mis Tarjetas"))
        self.setModal(True)
        self.setFixedSize(600, 550)

        self.tarjetas: list[dict[str, str]] = [
            {"pais": "Circulo", "simbolo": "Galeon"},
            {"pais": "Rectangulo", "simbolo": "Globo"},
        ]

        self.tarjetas_widgets: list[TarjetaWidget] = []
        self.tarjetas_seleccionadas: list[TarjetaWidget] = []

        self.objetivo_secreto_id: str | None = None
        self.objetivo_secreto_descripcion: str | None = None

        self._setup_ui()

    def _setup_ui(self) -> None:
        """Configura la interfaz del diálogo."""
        layout = QVBoxLayout()

        self.titulo = QLabel(_("Tarjetas Asignadas"))
        self.titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.titulo.setStyleSheet(styles.STYLE_TITULO_PRINCIPAL)
        layout.addWidget(self.titulo)

        self.tarjetas_widget = self._create_tarjetas_area()
        layout.addWidget(self.tarjetas_widget)

        self.objetivo_widget = self._create_objetivo_secreto_area()
        layout.addWidget(self.objetivo_widget)

        self.info_seleccion = self._create_info_seleccion()
        layout.addWidget(self.info_seleccion)

        botones_layout = self._create_buttons_layout()
        layout.addLayout(botones_layout)

        cerrar_layout = QHBoxLayout()
        cerrar_layout.addStretch()

        self.button_cerrar = QPushButton(_("Cerrar"))
        self.button_cerrar.clicked.connect(self.accept)
        self.button_cerrar.setStyleSheet(styles.STYLE_BUTTON_CERRAR)
        cerrar_layout.addWidget(self.button_cerrar)
        cerrar_layout.addStretch()

        layout.addLayout(cerrar_layout)
        self.setLayout(layout)

    def update_language(self, lang_code: str) -> None:
        """Re-aplica las traducciones a las etiquetas y botones del diálogo."""
        del lang_code
        self.setWindowTitle(_("Mis Tarjetas"))
        self.titulo.setText(_("Tarjetas Asignadas"))
        self.titulo_objetivo.setText(_("Objetivo Secreto"))
        self.button_cerrar.setText(_("Cerrar"))
        self.button_seleccionar_todas.setText(_("Seleccionar Todas"))
        self.button_deseleccionar_todas.setText(_("Deseleccionar Todas"))
        self.button_reclamar.setText(_("Reclamar Tarjeta"))
        self.button_canje.setText(_("Canje"))
        self._actualizar_info_seleccion()
        if not self.objetivo_secreto_descripcion:
            self.label_objetivo.setText(_("No hay objetivo secreto asignado"))

    def _create_objetivo_secreto_area(self) -> QWidget:
        """Crea el área para mostrar el objetivo secreto.

        Returns:
            Contenedor con título y descripción del objetivo.

        """
        container = QWidget()
        vlayout = QVBoxLayout()

        self.titulo_objetivo = QLabel(_("Objetivo Secreto"))
        self.titulo_objetivo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.titulo_objetivo.setStyleSheet(styles.STYLE_TITULO_OBJETIVO)
        vlayout.addWidget(self.titulo_objetivo)

        self.label_objetivo = QLabel(_("No hay objetivo secreto asignado"))
        self.label_objetivo.setWordWrap(True)
        self.label_objetivo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label_objetivo.setStyleSheet(styles.STYLE_LABEL_OBJETIVO)
        vlayout.addWidget(self.label_objetivo)

        container.setLayout(vlayout)
        return container

    def _create_buttons_layout(self) -> QHBoxLayout:
        """Crea el layout con los botones de acción.

        Returns:
            Layout horizontal con seleccionar/deseleccionar, reclamar y canje.

        """
        layout = QHBoxLayout()
        layout.addStretch()

        self.button_seleccionar_todas = QPushButton(_("Seleccionar Todas"))
        self.button_seleccionar_todas.setStyleSheet(
            styles.STYLE_BUTTON_SELECCIONAR_TODAS
        )
        self.button_seleccionar_todas.clicked.connect(self.seleccionar_todas)

        self.button_deseleccionar_todas = QPushButton(_("Deseleccionar Todas"))
        self.button_deseleccionar_todas.setStyleSheet(
            styles.STYLE_BUTTON_DESELECCIONAR_TODAS
        )
        self.button_deseleccionar_todas.clicked.connect(self.deseleccionar_todas)

        layout.addWidget(self.button_seleccionar_todas)
        layout.addWidget(self.button_deseleccionar_todas)

        self.button_reclamar = QPushButton(_("Reclamar Tarjeta"))
        self.button_reclamar.setStyleSheet(styles.STYLE_BUTTON_RECLAMAR)
        self.button_reclamar.clicked.connect(self.reclamar_tarjeta)

        self.button_canje = QPushButton(_("Canje"))
        self.button_canje.setStyleSheet(styles.STYLE_BUTTON_CANJE)
        self.button_canje.clicked.connect(self.realizar_canje)
        self.button_canje.setEnabled(False)

        layout.addWidget(self.button_reclamar)
        layout.addWidget(self.button_canje)
        layout.addStretch()

        return layout

    def actualizar_tarjetas(self, nuevas_tarjetas: list[dict[str, str]]) -> None:
        """Actualiza las tarjetas mostradas en el diálogo."""
        self.tarjetas = nuevas_tarjetas[:4]

        self.tarjetas_widget.setParent(None)
        self.tarjetas_widget = self._create_tarjetas_area()

        layout = self.layout()
        if layout is None:
            return
        layout_vbox = cast("QVBoxLayout", layout)
        layout_vbox.insertWidget(1, self.tarjetas_widget)

    def set_objetivo_secreto(
        self, objetivo_id: str | None, descripcion: str | None
    ) -> None:
        """Establece el objetivo secreto del jugador."""
        self.objetivo_secreto_id = objetivo_id
        self.objetivo_secreto_descripcion = descripcion
        if descripcion:
            self.label_objetivo.setText(descripcion)

    def get_objetivo_secreto(self) -> dict[str, str | None]:
        """Obtiene el objetivo secreto asignado.

        Returns:
            Diccionario con claves ``id`` y ``descripcion``.

        """
        return {
            "id": self.objetivo_secreto_id,
            "descripcion": self.objetivo_secreto_descripcion,
        }
