#!/usr/bin/env python3
"""
Script para compilar archivos .po a .mo usando Python puro.
"""

import struct
from pathlib import Path


def compile_po_to_mo(po_file: Path, mo_file: Path) -> None:
    """
    Compila un archivo .po a .mo usando Python puro.

    Args:
        po_file: Path al archivo .po
        mo_file: Path al archivo .mo de salida
    """
    translations: dict[str, str] = {}

    # Leer archivo .po
    content = po_file.read_text(encoding="utf-8")

    # Parsear el contenido
    lines = content.split("\n")
    current_msgid = None
    current_msgstr = None
    in_msgid = False
    in_msgstr = False

    for original_line in lines:
        line = original_line.strip()

        if line.startswith('msgid "'):
            current_msgid = line[7:-1]  # Remover 'msgid "' y '"'
            in_msgid = True
            in_msgstr = False
        elif line.startswith('msgstr "'):
            current_msgstr = line[8:-1]  # Remover 'msgstr "' y '"'
            in_msgid = False
            in_msgstr = True
        elif line.startswith('"') and line.endswith('"'):
            # Línea de continuación
            text = line[1:-1]  # Remover comillas
            if in_msgid and current_msgid is not None:
                current_msgid += text
            elif in_msgstr and current_msgstr is not None:
                current_msgstr += text
        elif not line or line.startswith("#"):
            # Línea vacía o comentario - finalizar entrada actual
            if (
                current_msgid is not None
                and current_msgstr is not None
                and current_msgid
                and current_msgstr
            ):
                translations[current_msgid] = current_msgstr
            current_msgid = None
            current_msgstr = None
            in_msgid = False
            in_msgstr = False

    # Agregar la última entrada si existe
    if (
        current_msgid is not None
        and current_msgstr is not None
        and current_msgid
        and current_msgstr
    ):
        translations[current_msgid] = current_msgstr

    # Crear archivo .mo
    create_mo_file(translations, mo_file)
    print(f"✓ Compilado: {po_file} -> {mo_file} ({len(translations)} traducciones)")


def create_mo_file(translations: dict[str, str], mo_file: Path) -> None:
    """
    Crea un archivo .mo válido desde un diccionario de traducciones.

    Args:
        translations: Diccionario {msgid: msgstr}
        mo_file: Path al archivo .mo de salida
    """
    # Asegurar que el directorio existe
    mo_file.parent.mkdir(parents=True, exist_ok=True)

    # Si no hay traducciones, crear un archivo .mo mínimo válido
    if not translations:
        translations = {"": ""}  # Header mínimo

    # Ordenar las claves para consistencia
    keys = sorted(translations.keys())

    # Calcular offsets
    koffsets: list[tuple[int, int]] = []
    voffsets: list[tuple[int, int]] = []
    kencoded: list[bytes] = []
    vencoded: list[bytes] = []

    for key in keys:
        kencoded.append(key.encode("utf-8"))
        vencoded.append(translations[key].encode("utf-8"))

    # Calcular posiciones
    keystart = 7 * 4 + 16 * len(keys)
    valuestart = keystart
    for k in kencoded:
        valuestart += len(k)

    # Calcular offsets para keys
    offset = keystart
    for k in kencoded:
        koffsets.append((len(k), offset))
        offset += len(k)

    # Calcular offsets para values
    offset = valuestart
    for v in vencoded:
        voffsets.append((len(v), offset))
        offset += len(v)

    # Escribir archivo .mo
    with mo_file.open("wb") as f:
        # Magic number
        f.write(struct.pack("<I", 0x950412DE))
        # Version
        f.write(struct.pack("<I", 0))
        # Number of entries
        f.write(struct.pack("<I", len(keys)))
        # Offset of key table
        f.write(struct.pack("<I", 7 * 4))
        # Offset of value table
        f.write(struct.pack("<I", 7 * 4 + 8 * len(keys)))
        # Hash table size (0 = no hash table)
        f.write(struct.pack("<I", 0))
        # Offset of hash table (0 = no hash table)
        f.write(struct.pack("<I", 0))

        # Write key offsets
        for length, offset in koffsets:
            f.write(struct.pack("<I", length))
            f.write(struct.pack("<I", offset))

        # Write value offsets
        for length, offset in voffsets:
            f.write(struct.pack("<I", length))
            f.write(struct.pack("<I", offset))

        # Write keys
        for k in kencoded:
            f.write(k)

        # Write values
        for v in vencoded:
            f.write(v)


def main() -> None:
    """Función principal."""
    base_dir = Path(__file__).parent.parent
    locales_dir = base_dir / "locales"

    if not locales_dir.exists():
        print("❌ Directorio locales/ no encontrado")
        return

    for lang_dir in locales_dir.iterdir():
        if not lang_dir.is_dir():
            continue

        po_file = lang_dir / "LC_MESSAGES" / "pyteg.po"
        mo_file = lang_dir / "LC_MESSAGES" / "pyteg.mo"

        if po_file.exists():
            try:
                compile_po_to_mo(po_file, mo_file)
            except (OSError, UnicodeDecodeError, ValueError, struct.error) as e:
                print(f"❌ Error compilando {po_file}: {e}")
        else:
            print(f"⚠️  Archivo no encontrado: {po_file}")


if __name__ == "__main__":
    main()
