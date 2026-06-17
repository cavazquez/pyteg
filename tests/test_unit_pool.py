"""Tests para consumo de unidades en el reparto."""

from __future__ import annotations

import unittest

from pyteg.core.turnos.turnos import SiguientesTurnos
from pyteg.core.turnos.unit_pool import (
    cant_unidades_continente,
    consumir_unidad_reparto,
    unidades_disponibles_en_pais,
)
from pyteg.server.juego.mapa import Mapa


class TestUnitPool(unittest.TestCase):
    """Consumo de bonificaciones continentales vs generales."""

    def _mapa_africa(self) -> Mapa:
        def build() -> dict[str, list[int | str | None]]:
            return {
                "Egipto": [2, "Africa", 1],
                "Sudáfrica": [2, "Africa", 1],
                "Chile": [1, "America", None],
            }

        return Mapa(build)

    def test_unidades_disponibles_suma_continental_y_generales(self) -> None:
        """En África se pueden usar bonificación + generales."""
        mapa = self._mapa_africa()
        turno = SiguientesTurnos(1, mapa)

        total = unidades_disponibles_en_pais(turno, "Africa")

        self.assertEqual(
            total,
            turno.cant_unidades() + turno.cant_unidades_por_continente("Africa"),
        )

    def test_consumir_prefiere_bonificacion_continental(self) -> None:
        """Al colocar en África se descuenta primero la bonificación."""
        mapa = self._mapa_africa()
        turno = SiguientesTurnos(1, mapa)
        africa_antes = turno.cant_unidades_por_continente("Africa")
        generales_antes = turno.cant_unidades()

        consumir_unidad_reparto(turno, "Africa")

        self.assertEqual(turno.cant_unidades_por_continente("Africa"), africa_antes - 1)
        self.assertEqual(turno.cant_unidades(), generales_antes)

    def test_consumir_general_si_no_hay_continental(self) -> None:
        """Sin bonificación continental se descuenta una general."""
        mapa = self._mapa_africa()
        turno = SiguientesTurnos(1, mapa)
        while turno.cant_unidades_por_continente("Africa") > 0:
            turno.usar_unidad_por_continente("Africa")
        generales_antes = turno.cant_unidades()

        consumir_unidad_reparto(turno, "Africa")

        self.assertEqual(turno.cant_unidades(), generales_antes - 1)
        self.assertEqual(cant_unidades_continente(turno, "Africa"), 0)


if __name__ == "__main__":
    unittest.main()
