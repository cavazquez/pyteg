"""Tests de i18n en `VentanaEsperarJugadores.update_language` (sin QWidget real)."""

# ruff: noqa: SLF001 — accedemos al atributo privado `_empezar_button` por simetría.

from __future__ import annotations

import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock

from pyteg.gui_esperar_jugadores import VentanaEsperarJugadores


class TestVentanaEsperarJugadoresUpdateLanguage(unittest.TestCase):
    """`update_language` re-aplica las traducciones a título y botón Empezar."""

    def test_update_language_con_boton_empezar(self) -> None:
        """Si `_empezar_button` existe (admin), también se retraduce su texto."""
        fake = SimpleNamespace()
        fake.setWindowTitle = MagicMock()
        fake._empezar_button = MagicMock()
        VentanaEsperarJugadores.update_language(fake, "en")  # type: ignore[arg-type]
        fake.setWindowTitle.assert_called_once()
        fake._empezar_button.setText.assert_called_once()

    def test_update_language_sin_boton_empezar(self) -> None:
        """Si no hay botón (no es admin), solo se actualiza el título."""
        fake = SimpleNamespace()
        fake.setWindowTitle = MagicMock()
        fake._empezar_button = None
        VentanaEsperarJugadores.update_language(fake, "es")  # type: ignore[arg-type]
        fake.setWindowTitle.assert_called_once()


if __name__ == "__main__":
    unittest.main()
