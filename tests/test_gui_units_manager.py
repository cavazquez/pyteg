"""Tests de `UnitsManager` sin ventana Qt real."""

from __future__ import annotations

import unittest
from types import SimpleNamespace
from typing import TYPE_CHECKING, cast
from unittest.mock import MagicMock

from pyteg.gui.managers.units import UnitsManager

if TYPE_CHECKING:
    from pyteg.gui.managers.protocols import MainWindowProtocol


class TestUnitsManager(unittest.TestCase):
    """Actualización y refresco de etiquetas del panel UNIDADES."""

    def setUp(self) -> None:
        """Arma un host mínimo con etiquetas y filas registradas."""
        self.label_generales = MagicMock()
        self.label_africa = MagicMock()
        self.label_misiles = MagicMock()
        self.row_misiles = MagicMock()
        self.main_window = SimpleNamespace(
            value_labels={
                "Generales": self.label_generales,
                "África": self.label_africa,
                "Misiles": self.label_misiles,
            },
            row_widgets={
                "Generales": MagicMock(),
                "África": MagicMock(),
                "Misiles": self.row_misiles,
            },
            last_units={},
        )
        self.manager = UnitsManager(cast("MainWindowProtocol", self.main_window))

    def test_update_infanteria_guarda_cantidad(self) -> None:
        """Las unidades generales actualizan etiqueta y `last_units`."""
        self.manager.update_unidades_disponibles({"infanteria": 4})

        self.label_generales.setText.assert_called_once()
        self.assertEqual(self.main_window.last_units["Generales"], 4)

    def test_update_continente_con_unidades(self) -> None:
        """Un continente con refuerzos actualiza su fila."""
        self.manager.update_unidades_disponibles({"Africa": 2})

        self.label_africa.setText.assert_called_once()
        self.assertEqual(self.main_window.last_units["África"], 2)

    def test_misiles_visibles_cuando_hay_stock(self) -> None:
        """La fila de misiles se muestra si el servidor envía misiles > 0."""
        self.manager.update_unidades_disponibles({"misiles": 1})

        self.row_misiles.setVisible.assert_called_with(True)  # noqa: FBT003
        self.assertEqual(self.main_window.last_units["Misiles"], 1)

    def test_misiles_ocultos_sin_stock(self) -> None:
        """Sin misiles en el payload, la fila queda oculta."""
        self.manager.update_unidades_disponibles({"infanteria": 0})

        self.row_misiles.setVisible.assert_called_with(False)  # noqa: FBT003
        self.assertEqual(self.main_window.last_units["Misiles"], 0)

    def test_refresh_unit_labels_reaplica_texto(self) -> None:
        """`refresh_unit_labels` vuelve a formatear desde `last_units`."""
        self.main_window.last_units = {"Generales": 5, "África": 0}

        self.manager.refresh_unit_labels()

        self.label_generales.setText.assert_called_once()
        self.label_africa.setText.assert_called_once()


if __name__ == "__main__":
    unittest.main()
