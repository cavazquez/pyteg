"""La compilación portable genera catálogos gettext válidos sin msgfmt."""

from __future__ import annotations

import gettext
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

import polib

from scripts import manage_translations


class TranslationBuildTests(unittest.TestCase):
    """Comprueba el mismo comando que ejecutan los builds de las tres plataformas."""

    def setUp(self) -> None:
        """Prepara un catálogo aislado con caracteres no ASCII y plurales."""
        directory = TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.locales = Path(directory.name)
        self.catalog = self.locales / "en" / "LC_MESSAGES" / "pyteg.po"
        self.catalog.parent.mkdir(parents=True)
        po = polib.POFile()
        po.metadata = {
            "Content-Type": "text/plain; charset=UTF-8",
            "Plural-Forms": "nplurals=2; plural=(n != 1);",
        }
        po.append(polib.POEntry(msgid="País", msgstr="Country"))
        po.append(
            polib.POEntry(
                msgid="País controlado",
                msgid_plural="Países controlados",
                msgstr_plural={0: "Controlled country", 1: "Controlled countries"},
            )
        )
        po.save(str(self.catalog))

    def test_compile_command_uses_polib_and_preserves_plural_translations(self) -> None:
        """El comando CLI funciona aun cuando gettext-tools no esté instalado."""
        with (
            patch.object(manage_translations, "LOCALES_DIR", self.locales),
            patch("scripts.manage_translations.sys.argv", ["translations", "compile"]),
            patch("scripts.manage_translations.subprocess.run") as external,
        ):
            manage_translations.main()
        external.assert_not_called()
        with self.catalog.with_suffix(".mo").open("rb") as stream:
            translation = gettext.GNUTranslations(stream)
        self.assertEqual(translation.gettext("País"), "Country")
        self.assertEqual(
            translation.ngettext("País controlado", "Países controlados", 2),
            "Controlled countries",
        )

    def test_missing_compilers_fail_without_emptying_an_existing_catalog(self) -> None:
        """Un build sin compilador falla y conserva el último catálogo válido."""
        mo_file = self.catalog.with_suffix(".mo")
        mo_file.write_bytes(b"previous catalog")
        with (
            patch.object(manage_translations, "LOCALES_DIR", self.locales),
            patch.object(manage_translations, "polib", None),
            patch(
                "scripts.manage_translations.subprocess.run",
                side_effect=FileNotFoundError,
            ),
            self.assertRaises(RuntimeError),
        ):
            manage_translations.compile_translations()
        self.assertEqual(mo_file.read_bytes(), b"previous catalog")


if __name__ == "__main__":
    unittest.main()
