from __future__ import annotations

from typing import Any, ClassVar, cast

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QMouseEvent, QPixmap
from PySide6.QtWidgets import (
    QDialog,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from src.i18n import translate as _
from src.utils import get_resource_path


class TarjetaWidget(QWidget):
    """Widget que representa una tarjeta individual."""

    seleccionada = Signal(object)  # Señal emitida cuando se selecciona/deselecciona

    # Mapeo de símbolos a archivos de imagen
    SIMBOLOS_IMAGENES: ClassVar[dict[str, str]] = {
        "Galeon": "themes/classic/tar_galeon.png",
        "Globo": "themes/classic/tar_globo.png",
        "Canon": "themes/classic/tar_canon.png",
        "Comodin": "themes/classic/tar_comodin.png",
    }

    def __init__(self, pais: str, simbolo: str, index: int = 0) -> None:
        super().__init__()
        self.pais = pais
        self.simbolo = simbolo
        self.index = index
        self._seleccionada = False
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Configura la interfaz del widget de tarjeta."""
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Etiqueta del país
        self.label_pais = QLabel(self.pais)
        self.label_pais.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label_pais.setStyleSheet("""
            QLabel {
                font-weight: bold;
                font-size: 12px;
                padding: 5px;
                background-color: #f0f0f0;
                border: 1px solid #ccc;
                border-radius: 3px;
            }
        """)

        # Etiqueta del símbolo con imagen
        self.label_simbolo = QLabel()
        self.label_simbolo.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Cargar imagen del símbolo si existe
        imagen_path = self.SIMBOLOS_IMAGENES.get(self.simbolo)
        if imagen_path:
            pixmap = QPixmap(str(get_resource_path(imagen_path)))
            if not pixmap.isNull():
                # Escalar la imagen a un tamaño apropiado
                scaled_pixmap = pixmap.scaled(
                    32,
                    32,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
                self.label_simbolo.setPixmap(scaled_pixmap)
            else:
                # Si no se puede cargar la imagen, mostrar texto
                self.label_simbolo.setText(self.simbolo)
        else:
            # Si no hay mapeo, mostrar texto
            self.label_simbolo.setText(self.simbolo)

        self.label_simbolo.setStyleSheet("""
            QLabel {
                padding: 8px;
                margin-top: 5px;
            }
        """)

        layout.addWidget(self.label_pais)
        layout.addWidget(self.label_simbolo)
        self.setLayout(layout)

        # Estilo del widget completo
        self._actualizar_estilo()
        self.setFixedSize(120, 80)

        # Hacer el widget clickeable
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def _actualizar_estilo(self) -> None:
        """Actualiza el estilo según el estado de selección."""
        if self._seleccionada:
            self.setStyleSheet("""
                TarjetaWidget {
                    background-color: #e8f5e8;
                    border: 3px solid #27ae60;
                    border-radius: 8px;
                    margin: 5px;
                }
                TarjetaWidget:hover {
                    border-color: #229954;
                    background-color: #d5f4d5;
                }
            """)
        else:
            self.setStyleSheet("""
                TarjetaWidget {
                    background-color: white;
                    border: 2px solid #3498db;
                    border-radius: 8px;
                    margin: 5px;
                }
                TarjetaWidget:hover {
                    border-color: #2980b9;
                    background-color: #ecf0f1;
                }
            """)

    def mousePressEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        """Maneja el clic en la tarjeta para seleccionar/deseleccionar."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.toggle_seleccion()
        super().mousePressEvent(event)

    def toggle_seleccion(self) -> None:
        """Alterna el estado de selección de la tarjeta."""
        self._seleccionada = not self._seleccionada
        self._actualizar_estilo()
        self.seleccionada.emit(self)

    def set_seleccionada(self, *, seleccionada: bool) -> None:
        """Establece el estado de selección de la tarjeta."""
        if self._seleccionada != seleccionada:
            self._seleccionada = seleccionada
            self._actualizar_estilo()

    def is_seleccionada(self) -> bool:
        """Retorna True si la tarjeta está seleccionada."""
        return self._seleccionada


class TarjetasDialog(QDialog):
    """Diálogo para mostrar las tarjetas asignadas al jugador."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle(_("Mis Tarjetas"))
        self.setModal(True)
        self.setFixedSize(600, 550)  # Aumentado para acomodar objetivo secreto

        # Lista de tarjetas de ejemplo (máximo 4)
        self.tarjetas: list[dict[str, str]] = [
            {"pais": "Circulo", "simbolo": "Galeon"},
            {"pais": "Rectangulo", "simbolo": "Globo"},
            # Agregar más tarjetas de prueba si es necesario
        ]

        # Lista de widgets de tarjetas para manejar selección
        self.tarjetas_widgets: list[TarjetaWidget] = []
        self.tarjetas_seleccionadas: list[TarjetaWidget] = []

        # Objetivo secreto asignado
        self.objetivo_secreto_id: str | None = None
        self.objetivo_secreto_descripcion: str | None = None

        self._setup_ui()

    def _setup_ui(self) -> None:
        """Configura la interfaz del diálogo."""
        layout = QVBoxLayout()

        # Título
        titulo = QLabel(_("Tarjetas Asignadas"))
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        titulo.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: #2c3e50;
                padding: 10px;
            }
        """)
        layout.addWidget(titulo)

        # Área de tarjetas
        self.tarjetas_widget = self._create_tarjetas_area()
        layout.addWidget(self.tarjetas_widget)

        # Objetivo secreto
        self.objetivo_widget = self._create_objetivo_secreto_area()
        layout.addWidget(self.objetivo_widget)

        # Información de selección
        self.info_seleccion = self._create_info_seleccion()
        layout.addWidget(self.info_seleccion)

        # Botones de acción
        botones_layout = self._create_buttons_layout()
        layout.addLayout(botones_layout)

        # Botón cerrar
        cerrar_layout = QHBoxLayout()
        cerrar_layout.addStretch()

        self.button_cerrar = QPushButton(_("Cerrar"))
        self.button_cerrar.clicked.connect(self.accept)
        self.button_cerrar.setStyleSheet("""
            QPushButton {
                padding: 8px 16px;
                font-size: 12px;
                background-color: #95a5a6;
                color: white;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #7f8c8d;
            }
        """)
        cerrar_layout.addWidget(self.button_cerrar)
        cerrar_layout.addStretch()

        layout.addLayout(cerrar_layout)
        self.setLayout(layout)

    def _create_tarjetas_area(self) -> QWidget:
        """Crea el área donde se muestran las tarjetas."""
        widget = QWidget()
        grid_layout = QGridLayout()
        grid_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Limpiar lista de widgets
        self.tarjetas_widgets.clear()

        # Mostrar tarjetas en una grilla de 2x2 (máximo 4 tarjetas)
        for i, tarjeta in enumerate(self.tarjetas[:4]):  # Máximo 4 tarjetas
            tarjeta_widget = TarjetaWidget(tarjeta["pais"], tarjeta["simbolo"], i)
            tarjeta_widget.seleccionada.connect(self._on_tarjeta_seleccionada)
            self.tarjetas_widgets.append(tarjeta_widget)
            row = i // 2
            col = i % 2
            grid_layout.addWidget(tarjeta_widget, row, col)

        # Si hay menos de 4 tarjetas, mostrar espacios vacíos
        for i in range(len(self.tarjetas), 4):
            placeholder = QLabel(_("Vacío"))
            placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
            placeholder.setStyleSheet("""
                QLabel {
                    background-color: #ecf0f1;
                    border: 2px dashed #bdc3c7;
                    border-radius: 8px;
                    color: #7f8c8d;
                    font-style: italic;
                }
            """)
            placeholder.setFixedSize(120, 80)
            row = i // 2
            col = i % 2
            grid_layout.addWidget(placeholder, row, col)

        widget.setLayout(grid_layout)
        return widget

    def _create_objetivo_secreto_area(self) -> QWidget:
        """Crea el área para mostrar el objetivo secreto."""
        container = QWidget()
        layout = QVBoxLayout()

        # Título de objetivo secreto
        titulo_objetivo = QLabel(_("Objetivo Secreto"))
        titulo_objetivo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        titulo_objetivo.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: bold;
                color: #8e44ad;
                padding: 5px;
                background-color: #f8f9fa;
                border-radius: 5px;
                margin-bottom: 5px;
            }
        """)
        layout.addWidget(titulo_objetivo)

        # Descripción del objetivo secreto
        self.label_objetivo = QLabel(_("No hay objetivo secreto asignado"))
        self.label_objetivo.setWordWrap(True)
        self.label_objetivo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label_objetivo.setStyleSheet("""
            QLabel {
                font-size: 12px;
                color: #2c3e50;
                padding: 10px;
                background-color: #ecf0f1;
                border: 1px solid #bdc3c7;
                border-radius: 5px;
                margin: 5px;
            }
        """)
        layout.addWidget(self.label_objetivo)

        container.setLayout(layout)
        return container

    def _create_buttons_layout(self) -> QHBoxLayout:
        """Crea el layout con los botones de acción."""
        layout = QHBoxLayout()
        layout.addStretch()

        # Botón Seleccionar Todas
        self.button_seleccionar_todas = QPushButton(_("Seleccionar Todas"))
        self.button_seleccionar_todas.setStyleSheet("""
            QPushButton {
                padding: 8px 16px;
                font-size: 12px;
                background-color: #f39c12;
                color: white;
                border: none;
                border-radius: 4px;
                margin: 5px;
            }
            QPushButton:hover {
                background-color: #d68910;
            }
        """)
        self.button_seleccionar_todas.clicked.connect(self.seleccionar_todas)

        # Botón Deseleccionar Todas
        self.button_deseleccionar_todas = QPushButton(_("Deseleccionar Todas"))
        self.button_deseleccionar_todas.setStyleSheet("""
            QPushButton {
                padding: 8px 16px;
                font-size: 12px;
                background-color: #95a5a6;
                color: white;
                border: none;
                border-radius: 4px;
                margin: 5px;
            }
            QPushButton:hover {
                background-color: #7f8c8d;
            }
        """)
        self.button_deseleccionar_todas.clicked.connect(self.deseleccionar_todas)

        layout.addWidget(self.button_seleccionar_todas)
        layout.addWidget(self.button_deseleccionar_todas)

        # Botón Reclamar Tarjeta
        self.button_reclamar = QPushButton(_("Reclamar Tarjeta"))
        self.button_reclamar.setStyleSheet("""
            QPushButton {
                padding: 10px 20px;
                font-size: 14px;
                background-color: #27ae60;
                color: white;
                border: none;
                border-radius: 5px;
                margin: 5px;
            }
            QPushButton:hover {
                background-color: #229954;
            }
            QPushButton:disabled {
                background-color: #95a5a6;
            }
        """)
        self.button_reclamar.clicked.connect(self.reclamar_tarjeta)

        # Botón Canje
        self.button_canje = QPushButton(_("Canje"))
        self.button_canje.setStyleSheet("""
            QPushButton {
                padding: 10px 20px;
                font-size: 14px;
                background-color: #e74c3c;
                color: white;
                border: none;
                border-radius: 5px;
                margin: 5px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
            QPushButton:disabled {
                background-color: #95a5a6;
            }
        """)
        self.button_canje.clicked.connect(self.realizar_canje)
        self.button_canje.setEnabled(False)  # Deshabilitado hasta seleccionar tarjetas

        layout.addWidget(self.button_reclamar)
        layout.addWidget(self.button_canje)
        layout.addStretch()

        return layout

    def actualizar_tarjetas(self, nuevas_tarjetas: list[dict[str, str]]) -> None:
        """Actualiza las tarjetas mostradas en el diálogo.

        Args:
            nuevas_tarjetas: Lista de diccionarios con 'pais' y 'simbolo'
        """
        self.tarjetas = nuevas_tarjetas[:4]  # Máximo 4 tarjetas

        # Recrear el área de tarjetas
        self.tarjetas_widget.setParent(None)
        self.tarjetas_widget = self._create_tarjetas_area()

        # Actualizar el layout
        layout = self.layout()
        if layout is None:
            return
        layout_vbox = cast("QVBoxLayout", layout)
        layout_vbox.insertWidget(1, self.tarjetas_widget)

    def _create_info_seleccion(self) -> QWidget:
        """Crea el área de información sobre la selección actual."""
        widget = QWidget()
        layout = QHBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.label_info_seleccion = QLabel(_("Seleccionadas: 0"))
        self.label_info_seleccion.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: bold;
                color: #2c3e50;
                padding: 8px;
                background-color: #ecf0f1;
                border-radius: 4px;
                margin: 5px;
            }
        """)

        layout.addWidget(self.label_info_seleccion)
        widget.setLayout(layout)
        return widget

    def _on_tarjeta_seleccionada(self, _tarjeta_widget: TarjetaWidget) -> None:
        """Maneja la selección/deselección de una tarjeta."""
        self._actualizar_lista_seleccionadas()
        self._actualizar_info_seleccion()
        self._actualizar_estado_botones()

    def _actualizar_lista_seleccionadas(self) -> None:
        """Actualiza la lista de tarjetas seleccionadas."""
        self.tarjetas_seleccionadas = [
            widget for widget in self.tarjetas_widgets if widget.is_seleccionada()
        ]

    def _actualizar_info_seleccion(self) -> None:
        """Actualiza la información mostrada sobre la selección."""
        cantidad = len(self.tarjetas_seleccionadas)
        self.label_info_seleccion.setText(_("Seleccionadas: %s") % cantidad)

        # Cambiar color según cantidad seleccionada
        if cantidad == 0:
            color = "#95a5a6"  # Gris
        elif cantidad <= 2:
            color = "#f39c12"  # Naranja
        else:
            color = "#27ae60"  # Verde

        self.label_info_seleccion.setStyleSheet(f"""
            QLabel {{
                font-size: 14px;
                font-weight: bold;
                color: white;
                padding: 8px;
                background-color: {color};
                border-radius: 4px;
                margin: 5px;
            }}
        """)

    def _actualizar_estado_botones(self) -> None:
        """Actualiza el estado habilitado/deshabilitado de los botones."""
        cantidad_seleccionadas = len(self.tarjetas_seleccionadas)

        # El botón de canje se habilita con 3 tarjetas o con combinaciones válidas
        self.button_canje.setEnabled(self._puede_realizar_canje())

        # Botones de selección masiva
        total_tarjetas = len(self.tarjetas_widgets)
        self.button_seleccionar_todas.setEnabled(
            cantidad_seleccionadas < total_tarjetas
        )
        self.button_deseleccionar_todas.setEnabled(cantidad_seleccionadas > 0)

    def _puede_realizar_canje(self) -> bool:
        """Determina si se puede realizar un canje con las tarjetas seleccionadas."""
        cantidad = len(self.tarjetas_seleccionadas)

        # Reglas básicas de canje (pueden ajustarse según las reglas del juego)
        if cantidad == 3:
            # Verificar si son 3 iguales o 3 diferentes
            simbolos = [tarjeta.simbolo for tarjeta in self.tarjetas_seleccionadas]
            return len(set(simbolos)) == 1 or len(set(simbolos)) == 3
        if cantidad == 1:
            # Canje especial: una tarjeta si poseo el país
            return self._puede_realizar_canje_especial()

        return False

    def _puede_realizar_canje_especial(self) -> bool:
        """Verifica si se puede realizar un canje especial (país + tarjeta)."""
        # La validación real de posesión del país se hace en el servidor
        # Aquí solo verificamos que hay exactamente una tarjeta seleccionada
        return len(self.tarjetas_seleccionadas) == 1

    def seleccionar_todas(self) -> None:
        """Selecciona todas las tarjetas disponibles."""
        for widget in self.tarjetas_widgets:
            widget.set_seleccionada(seleccionada=True)

        self._actualizar_lista_seleccionadas()
        self._actualizar_info_seleccion()
        self._actualizar_estado_botones()

    def deseleccionar_todas(self) -> None:
        """Deselecciona todas las tarjetas."""
        for widget in self.tarjetas_widgets:
            widget.set_seleccionada(seleccionada=False)

        self._actualizar_lista_seleccionadas()
        self._actualizar_info_seleccion()
        self._actualizar_estado_botones()

    def realizar_canje(self) -> None:
        """Realiza el canje de las tarjetas seleccionadas."""
        if not self._puede_realizar_canje():
            return

        cantidad_seleccionadas = len(self.tarjetas_seleccionadas)

        # Obtener información de las tarjetas seleccionadas
        tarjetas_info = [
            {"pais": tarjeta.pais, "simbolo": tarjeta.simbolo, "index": tarjeta.index}
            for tarjeta in self.tarjetas_seleccionadas
        ]

        transmisor = self._get_transmisor()
        if transmisor is None:
            print("Error: No se puede acceder al transmisor")
            return

        try:
            if cantidad_seleccionadas == 1:
                tarjeta = self.tarjetas_seleccionadas[0]
                transmisor.canje_especial(tarjeta.pais)
            else:
                transmisor.canjear_tarjetas(tarjetas_info)

            self.deseleccionar_todas()
        except (AttributeError, RuntimeError) as e:
            print(f"Error al realizar canje: {e}")

    def reclamar_tarjeta(self) -> None:
        """Reclama una tarjeta del servidor."""
        transmisor = self._get_transmisor()
        if transmisor is None:
            print("Error: No se puede acceder al transmisor")
            return

        try:
            transmisor.reclamar_tarjeta()
            transmisor.solicitar_tarjetas()
        except (AttributeError, RuntimeError) as e:
            print(f"Error al reclamar tarjeta: {e}")

    def set_objetivo_secreto(
        self, objetivo_id: str | None, descripcion: str | None
    ) -> None:
        """Establece el objetivo secreto del jugador."""
        self.objetivo_secreto_id = objetivo_id
        self.objetivo_secreto_descripcion = descripcion
        if descripcion:
            self.label_objetivo.setText(descripcion)

    def get_objetivo_secreto(self) -> dict[str, str | None]:
        """Obtiene el objetivo secreto asignado."""
        return {
            "id": self.objetivo_secreto_id,
            "descripcion": self.objetivo_secreto_descripcion,
        }

    def _get_transmisor(self) -> Any | None:
        """Obtiene el transmisor desde la ventana padre si existe."""
        parent = self.parent()
        if parent is None:
            return None
        return getattr(parent, "transmisor", None)
