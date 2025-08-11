from PySide6.QtCore import Signal
from PySide6.QtWidgets import QComboBox, QHBoxLayout, QLabel, QWidget

from src.i18n import (
    get_available_languages,
    get_current_language,
    set_language,
)
from src.i18n import (
    translate as _,
)


class LanguageSelector(QWidget):
    """Widget selector de idioma."""

    # Señal emitida cuando cambia el idioma
    language_changed = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        layout = QHBoxLayout()
        layout.setContentsMargins(8, 2, 8, 2)  # Márgenes más generosos
        layout.setSpacing(6)  # Espaciado entre elementos
        self.setLayout(layout)

        # Label
        label = QLabel(_("Idioma:"))
        label.setStyleSheet("font-weight: 500; color: #555;")
        layout.addWidget(label)

        # ComboBox
        self.combo = QComboBox()
        self.combo.setMinimumWidth(100)  # Ancho mínimo
        self.combo.setFixedHeight(22)  # Altura fija para consistencia

        # Estilo mejorado para el ComboBox
        self.combo.setStyleSheet("""
            QComboBox {
                background-color: #ffffff;
                border: 1px solid #cccccc;
                border-radius: 4px;
                padding: 2px 8px;
                font-size: 12px;
                min-width: 80px;
            }
            QComboBox:hover {
                border-color: #4361ee;
            }
            QComboBox:focus {
                border-color: #4361ee;
                outline: none;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 4px solid #666;
                margin-right: 4px;
            }
            QComboBox QAbstractItemView {
                background-color: #ffffff;
                border: 1px solid #cccccc;
                selection-background-color: #4361ee;
                selection-color: white;
            }
        """)

        self.combo.currentTextChanged.connect(self.on_language_changed)
        layout.addWidget(self.combo)

        # Cargar idiomas disponibles
        self.load_languages()

    def load_languages(self):
        """Carga los idiomas disponibles en el combo."""
        languages = get_available_languages()
        current_lang = get_current_language()

        language_names = {"es": "Español", "en": "English"}

        # Bloquear señales temporalmente para evitar bucles
        self.combo.blockSignals(True)  # noqa: FBT003

        self.combo.clear()
        for lang in languages:
            display_name = language_names.get(lang, lang.upper())
            self.combo.addItem(display_name, lang)

            if lang == current_lang:
                self.combo.setCurrentText(display_name)

        # Reactivar señales
        self.combo.blockSignals(False)  # noqa: FBT003

    def on_language_changed(self, display_name):
        """Maneja el cambio de idioma."""
        lang_code = None
        for i in range(self.combo.count()):
            if self.combo.itemText(i) == display_name:
                lang_code = self.combo.itemData(i)
                break

        if lang_code and lang_code != get_current_language():
            set_language(lang_code)
            # Emitir señal para que toda la GUI se actualice
            self.language_changed.emit(lang_code)
            print(f"Idioma cambiado a: {lang_code}")
        # Si el idioma es el mismo, no hacer nada para evitar bucles
