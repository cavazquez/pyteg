"""Regresiones de recursos para wheel, sdist y Nuitka."""

from __future__ import annotations

import unittest
from pathlib import Path

from scripts.build_binaries import RESOURCE_DIRS
from scripts.verify_sdist import REQUIRED_FILES as SDIST_REQUIRED_FILES
from scripts.verify_wheel import REQUIRED_FILES as WHEEL_REQUIRED_FILES


class PackagingResourceTests(unittest.TestCase):
    """Los verificadores cubren los dos temas jugables y sus assets."""

    def test_revancha_resources_are_required_by_both_archives(self) -> None:
        """Wheel y sdist exigen los archivos normativos de Revancha."""
        required = {
            "themes/revancha/paises.toml",
            "themes/revancha/reglas.toml",
            "themes/revancha/objetivos_secretos.toml",
            "themes/revancha/countries/Argentina.svg",
            "themes/revancha/cards/Avion.svg",
        }

        self.assertTrue(required.issubset(WHEEL_REQUIRED_FILES))
        self.assertTrue(required.issubset(SDIST_REQUIRED_FILES))

    def test_required_theme_resources_exist_in_checkout(self) -> None:
        """Cada ruta estática exigida por los verificadores existe localmente."""
        root = Path(__file__).resolve().parents[1]
        for relative in set(WHEEL_REQUIRED_FILES) | set(SDIST_REQUIRED_FILES):
            with self.subTest(relative=relative):
                self.assertTrue((root / relative).is_file(), relative)

    def test_nuitka_copies_all_resource_namespaces(self) -> None:
        """Las entradas Nuitka incluyen temas, traducciones y recursos visuales."""
        self.assertEqual(
            set(RESOURCE_DIRS),
            {"themes", "locales", "icons", "sounds"},
        )


if __name__ == "__main__":
    unittest.main()
