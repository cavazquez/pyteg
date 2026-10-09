"""Regresiones de recursos para wheel, sdist y Nuitka."""

from __future__ import annotations

import unittest
from argparse import Namespace
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from zipfile import ZipFile

from scripts import smoke_binaries, smoke_wheel
from scripts.build_binaries import RESOURCE_DIRS, _nuitka_command  # noqa: PLC2701
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

    def test_nuitka_disables_console_using_the_current_windows_option(self) -> None:
        """Sólo Windows recibe el flag de consola vigente de Nuitka."""
        output = Path("build/pyteg-client.exe")
        output_dir = Path("build")
        entry = Path("pyteg/client/run.py")
        with patch("scripts.build_binaries.os.name", "nt"):
            command = _nuitka_command(
                entry,
                output,
                disable_console=True,
                output_dir=output_dir,
            )
        self.assertIn("--windows-console-mode=disable", command)
        self.assertNotIn("--disable-console", command)
        self.assertIn("--include-data-files=pyproject.toml=pyproject.toml", command)

    def test_nuitka_does_not_add_windows_console_options_on_linux(self) -> None:
        """Linux y macOS mantienen su comportamiento de consola predeterminado."""
        entry = Path("pyteg/client/run.py")
        output = Path("build/pyteg-client")
        output_dir = Path("build")
        with patch("scripts.build_binaries.os.name", "posix"):
            command = _nuitka_command(
                entry, output, disable_console=True, output_dir=output_dir
            )
        self.assertNotIn("--windows-console-mode=disable", command)
        self.assertNotIn("--disable-console", command)

    def test_binary_smoke_opens_client_with_each_map(self) -> None:
        """El cliente compilado prueba ambos mapas explícitamente."""
        with TemporaryDirectory() as directory:
            server, client = (Path(directory) / name for name in ("server", "client"))
            server.touch()
            client.touch()
            args = Namespace(server=server, client=client)
            with (
                patch("scripts.smoke_binaries.parse_args", return_value=args),
                patch("scripts.smoke_binaries._run_server"),
                patch("scripts.smoke_binaries._run_client") as launch,
            ):
                self.assertEqual(smoke_binaries.main(), 0)
            self.assertEqual(
                [call.args[1] for call in launch.call_args_list],
                ["classic", "revancha"],
            )

    def test_wheel_smoke_opens_client_with_each_map(self) -> None:
        """El wheel prueba ambos mapas también en el cliente Qt."""
        with TemporaryDirectory() as directory:
            wheel = Path(directory) / "empty.whl"
            with ZipFile(wheel, "w"):
                pass
            with (
                patch(
                    "scripts.smoke_wheel.parse_args",
                    return_value=Namespace(wheel=wheel),
                ),
                patch("scripts.smoke_wheel._run_server"),
                patch("scripts.smoke_wheel._run_client") as launch,
            ):
                self.assertEqual(smoke_wheel.main(), 0)
            self.assertEqual(
                [call.args[2] for call in launch.call_args_list],
                ["classic", "revancha"],
            )


if __name__ == "__main__":
    unittest.main()
