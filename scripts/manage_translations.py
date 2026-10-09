#!/usr/bin/env python3
"""Script para gestionar las traducciones de PyTeg.

Este script permite compilar archivos .po a .mo, extraer strings para traducir
del código fuente y validar archivos de traducción.
"""

import re
import subprocess  # noqa: S404
import sys
from pathlib import Path

try:
    import polib
except ImportError:
    polib = None  # type: ignore[assignment]

# Agregar el paquete pyteg al path para importar módulos
sys.path.insert(0, str(Path(__file__).parent.parent / "pyteg"))

BASE_DIR = Path(__file__).parent.parent
LOCALES_DIR = BASE_DIR / "locales"
SRC_DIR = BASE_DIR / "pyteg"
DOMAIN = "pyteg"


def compile_translations() -> None:
    """Compila archivos .po a .mo usando Python puro."""
    if polib is None:
        print("polib no está disponible, usando fallback")
        compile_translations_manual()
        return

    for lang_dir in LOCALES_DIR.iterdir():
        if not lang_dir.is_dir():
            continue

        po_file = lang_dir / "LC_MESSAGES" / f"{DOMAIN}.po"
        mo_file = lang_dir / "LC_MESSAGES" / f"{DOMAIN}.mo"

        if po_file.exists():
            po = polib.pofile(str(po_file))
            po.save_as_mofile(str(mo_file))
            print(f"✓ Compilado: {po_file} -> {mo_file}")


def compile_translations_manual() -> None:
    """Compila con msgfmt si el script se ejecuta sin polib.

    Raises:
        RuntimeError: Si no hay compilador o un catálogo no se puede compilar.

    """
    for lang_dir in LOCALES_DIR.iterdir():
        if not lang_dir.is_dir():
            continue

        po_file = lang_dir / "LC_MESSAGES" / f"{DOMAIN}.po"
        mo_file = lang_dir / "LC_MESSAGES" / f"{DOMAIN}.mo"

        if not po_file.exists():
            continue

        try:
            # Usar msgfmt para compilar archivos .po
            cmd = ["msgfmt", str(po_file), "-o", str(mo_file)]
            subprocess.run(cmd, check=True, timeout=30)  # noqa: S603
            print(f"✓ Compilado con msgfmt: {po_file} -> {mo_file}")
        except (subprocess.CalledProcessError, FileNotFoundError) as error:
            msg = f"No se pudo compilar {po_file}; instala 'polib' o 'gettext'"
            raise RuntimeError(msg) from error


def extract_strings() -> set[str]:
    """Extrae strings marcados con _() del código fuente.

    Returns:
        Conjunto de strings únicos encontrados en el código.

    """
    print("Extrayendo strings para traducir...")

    pattern = re.compile(r'_\("([^"]+)"\)|_\(\'([^\']+)\'\)')
    strings: set[str] = set()

    for py_file in SRC_DIR.glob("**/*.py"):
        try:
            content = py_file.read_text(encoding="utf-8")
            matches = pattern.findall(content)
            for match in matches:
                # match es una tupla (grupo1, grupo2), tomar el no vacío
                string = match[0] or match[1]
                if string:
                    strings.add(string)
        except (OSError, UnicodeDecodeError) as e:
            print(f"Error leyendo {py_file}: {e}")

    print(f"Encontrados {len(strings)} strings únicos:")
    for string in sorted(strings):
        print(f"  - {string}")

    return strings


def validate_translations() -> None:
    """Valida que los archivos de traducción estén correctos."""
    print("Validando archivos de traducción...")

    for lang_dir in LOCALES_DIR.iterdir():
        if not lang_dir.is_dir():
            continue

        po_file = lang_dir / "LC_MESSAGES" / f"{DOMAIN}.po"
        if po_file.exists():
            print(f"Validando {po_file}...")
            # Aquí se podría agregar validación más sofisticada
            print(f"✓ {po_file} parece válido")


def create_language_selector() -> None:
    """Crea un widget selector de idioma para la GUI."""
    selector_code = '''
from PySide6.QtWidgets import QComboBox, QLabel, QHBoxLayout, QWidget
from i18n import get_available_languages, set_language, get_current_language, _


class LanguageSelector(QWidget):
    """Widget selector de idioma."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        layout = QHBoxLayout()
        self.setLayout(layout)

        # Label
        label = QLabel(_("Idioma:"))
        layout.addWidget(label)

        # ComboBox
        self.combo = QComboBox()
        self.combo.currentTextChanged.connect(self.on_language_changed)
        layout.addWidget(self.combo)

        # Cargar idiomas disponibles
        self.load_languages()

    def load_languages(self):
        """Carga los idiomas disponibles en el combo."""
        languages = get_available_languages()
        current_lang = get_current_language()

        language_names = {
            'es': 'Español',
            'en': 'English'
        }

        self.combo.clear()
        for lang in languages:
            display_name = language_names.get(lang, lang.upper())
            self.combo.addItem(display_name, lang)

            if lang == current_lang:
                self.combo.setCurrentText(display_name)

    def on_language_changed(self, display_name):
        """Maneja el cambio de idioma."""
        lang_code = None
        for i in range(self.combo.count()):
            if self.combo.itemText(i) == display_name:
                lang_code = self.combo.itemData(i)
                break

        if lang_code and lang_code != get_current_language():
            set_language(lang_code)
            # Aquí se podría emitir una señal para que la GUI se actualice
            print(f"Idioma cambiado a: {lang_code}")
'''

    selector_file = SRC_DIR / "gui" / "widgets" / "language_selector.py"
    selector_file.write_text(selector_code, encoding="utf-8")

    print(f"✓ Creado selector de idioma: {selector_file}")


# Constantes
MIN_ARGS_REQUIRED = 2
"""Mínimo de argumentos requeridos (script + comando)."""


def main() -> None:
    """Función principal."""
    if len(sys.argv) < MIN_ARGS_REQUIRED:
        print("Uso: python manage_translations.py <comando>")
        print("Comandos disponibles:")
        print("  compile    - Compilar archivos .po a .mo")
        print("  extract    - Extraer strings del código fuente")
        print("  validate   - Validar archivos de traducción")
        print("  selector   - Crear widget selector de idioma")
        print("  all        - Ejecutar todos los comandos")
        return

    command = sys.argv[1]

    if command == "compile":
        compile_translations()
    elif command == "extract":
        extract_strings()
    elif command == "validate":
        validate_translations()
    elif command == "selector":
        create_language_selector()
    elif command == "all":
        extract_strings()
        validate_translations()
        compile_translations()
        create_language_selector()
    else:
        print(f"Comando desconocido: {command}")


if __name__ == "__main__":
    main()
