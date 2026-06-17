"""Tests de `VentanaAdmin` sin QWidget completo."""

from __future__ import annotations

import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock

from pyteg.gui.windows.admin import VentanaAdmin


class TestVentanaAdmin(unittest.TestCase):
    """Configuración enviada al transmisor e i18n de etiquetas."""

    def test_empezar_envia_configuracion_al_transmisor(self) -> None:
        """`empezar` lee los campos y delega en `transmisor.empezar`."""
        transmisor = MagicMock()
        ventana = SimpleNamespace(
            seconds_input=MagicMock(text=MagicMock(return_value="45")),
            countries_checkbox=MagicMock(isChecked=MagicMock(return_value=True)),
            countries_input=MagicMock(text=MagicMock(return_value="30")),
            objetivos_secretos_checkbox=MagicMock(
                isChecked=MagicMock(return_value=False)
            ),
            misiles_checkbox=MagicMock(isChecked=MagicMock(return_value=True)),
            main_window=SimpleNamespace(transmisor=transmisor),
            close=MagicMock(),
        )

        VentanaAdmin.empezar(ventana)  # type: ignore[arg-type]

        transmisor.empezar.assert_called_once_with(
            45,
            30,
            objetivos_secretos=False,
            misiles_habilitados=True,
        )
        ventana.close.assert_called_once()

    def test_empezar_todos_los_paises_usa_cero(self) -> None:
        """Con el checkbox desactivado, victoria = controlar todos (0)."""
        transmisor = MagicMock()
        ventana = SimpleNamespace(
            seconds_input=MagicMock(text=MagicMock(return_value="")),
            countries_checkbox=MagicMock(isChecked=MagicMock(return_value=False)),
            countries_input=MagicMock(text=MagicMock(return_value="50")),
            objetivos_secretos_checkbox=MagicMock(
                isChecked=MagicMock(return_value=True)
            ),
            misiles_checkbox=MagicMock(isChecked=MagicMock(return_value=False)),
            main_window=SimpleNamespace(transmisor=transmisor),
            close=MagicMock(),
        )

        VentanaAdmin.empezar(ventana)  # type: ignore[arg-type]

        transmisor.empezar.assert_called_once_with(
            None,
            0,
            objetivos_secretos=True,
            misiles_habilitados=False,
        )

    def test_update_language_refresca_etiquetas(self) -> None:
        """`update_language` actualiza título, labels y botón."""
        ventana = SimpleNamespace(
            setWindowTitle=MagicMock(),
            seconds_label=MagicMock(),
            seconds_input=MagicMock(),
            countries_checkbox=MagicMock(),
            countries_label=MagicMock(),
            countries_input=MagicMock(),
            objetivos_secretos_checkbox=MagicMock(),
            misiles_checkbox=MagicMock(),
            button=MagicMock(),
        )

        VentanaAdmin.update_language(ventana, "en")  # type: ignore[arg-type]

        ventana.setWindowTitle.assert_called_once()
        ventana.button.setText.assert_called_once()


if __name__ == "__main__":
    unittest.main()
