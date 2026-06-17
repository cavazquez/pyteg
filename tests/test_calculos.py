"""Tests para el módulo de cálculos."""

from __future__ import annotations

import unittest

from pyteg.config import BONIFICACIONES_CONTINENTE
from pyteg.core.combate.calculos import Calculos
from pyteg.server.juego.mapa import Mapa

J_MENGANO = 2
J_FULANO = 1


class TestCalculos(unittest.TestCase):
    """Tests para la clase Calculos."""

    def test_calcular_unidades_generales_sin_paises(self) -> None:
        """Prueba calcular unidades generales sin países del jugador."""

        def build_mapa() -> dict[str, list[int | str | None]]:
            return {"Argentina": [1, "Pangea", None], "Uruguay": [10, "Pangea", None]}

        mapa = Mapa(build_mapa)
        self.assertEqual(Calculos.calcular_unidades_generales(mapa, J_MENGANO), 3)

    def test_calcular_unidades_generales_con_4_paises(self) -> None:
        """Prueba calcular unidades generales con 4 países del jugador."""

        def build_mapa() -> dict[str, list[int | str | None]]:
            return {
                "Argentina": [1, "Pangea", J_MENGANO],
                "Uruguay": [10, "Pangea", J_MENGANO],
                "Chile": [10, "America", J_MENGANO],
                "Brasil": [10, "Pangea", J_MENGANO],
            }

        mapa = Mapa(build_mapa)
        self.assertEqual(Calculos.calcular_unidades_generales(mapa, J_MENGANO), 3)

    def test_calcular_unidades_generales_con_8_paises(self) -> None:
        """Prueba calcular unidades generales con 8 países del jugador."""

        def build_mapa() -> dict[str, list[int | str | None]]:
            return {
                "Argentina": [1, "Pangea", J_MENGANO],
                "Uruguay": [10, "Pangea", J_MENGANO],
                "Chile": [10, "Pangea", J_MENGANO],
                "Brasil": [10, "America", J_MENGANO],
                "Mexico": [10, "Pangea", J_MENGANO],
                "Canada": [10, "Pangea", J_MENGANO],
                "Francia": [10, "Europa", J_MENGANO],
                "Italia": [10, "Europa", J_MENGANO],
            }

        mapa = Mapa(build_mapa)
        self.assertEqual(Calculos.calcular_unidades_generales(mapa, J_MENGANO), 4)

    def test_calcular_unidades_continente_invalido(self) -> None:
        """Prueba calcular unidades con un continente inválido."""
        mapa = Mapa(dict)
        self.assertEqual(
            Calculos.calcular_unidades_continente(mapa, J_MENGANO, "Atlantis"),
            0,
        )

    def test_calcular_unidades_con_toda_europa(self) -> None:
        """Prueba calcular unidades cuando el jugador tiene toda Europa."""

        def build_mapa() -> dict[str, list[int | str | None]]:
            return {
                "Argentina": [1, "Europa", J_MENGANO],
                "Uruguay": [10, "Europa", J_MENGANO],
                "Chile": [10, "America", J_MENGANO],
                "Brasil": [10, "Pangea", None],
            }

        mapa = Mapa(build_mapa)
        self.assertEqual(
            Calculos.calcular_unidades_continente(mapa, J_MENGANO, "Europa"),
            BONIFICACIONES_CONTINENTE["Europa"],
        )

    def test_calcular_unidades_sin_toda_europa(self) -> None:
        """Prueba calcular unidades cuando el jugador no tiene toda Europa."""

        def build_mapa() -> dict[str, list[int | str | None]]:
            return {
                "Argentina": [1, "Europa", J_MENGANO],
                "Uruguay": [10, "Europa", J_FULANO],
                "Chile": [10, "America", J_MENGANO],
                "Brasil": [10, "Pangea", None],
            }

        mapa = Mapa(build_mapa)
        self.assertEqual(
            Calculos.calcular_unidades_continente(mapa, J_MENGANO, "Europa"), 0
        )

    def test_calcular_unidades_con_toda_asia(self) -> None:
        """Prueba calcular unidades cuando el jugador tiene toda Asia."""

        def build_mapa() -> dict[str, list[int | str | None]]:
            return {
                "Argentina": [1, "Asia", J_MENGANO],
                "Uruguay": [10, "Asia", J_MENGANO],
                "Chile": [10, "America", J_MENGANO],
                "Brasil": [10, "Pangea", None],
            }

        mapa = Mapa(build_mapa)
        self.assertEqual(
            Calculos.calcular_unidades_continente(mapa, J_MENGANO, "Asia"),
            BONIFICACIONES_CONTINENTE["Asia"],
        )

    def test_calcular_unidades_sin_toda_asia(self) -> None:
        """Prueba calcular unidades cuando el jugador no tiene toda Asia."""

        def build_mapa() -> dict[str, list[int | str | None]]:
            return {
                "Argentina": [1, "Asia", J_MENGANO],
                "Uruguay": [10, "Asia", J_FULANO],
                "Chile": [10, "America", J_MENGANO],
                "Brasil": [10, "Pangea", None],
            }

        mapa = Mapa(build_mapa)
        self.assertEqual(
            Calculos.calcular_unidades_continente(mapa, J_MENGANO, "Asia"), 0
        )

    def test_calcular_unidades_con_toda_africa(self) -> None:
        """Prueba calcular unidades cuando el jugador tiene toda África."""

        def build_mapa() -> dict[str, list[int | str | None]]:
            return {
                "Argentina": [1, "Africa", J_MENGANO],
                "Uruguay": [10, "Africa", J_MENGANO],
                "Chile": [10, "America", J_MENGANO],
                "Brasil": [10, "Pangea", None],
            }

        mapa = Mapa(build_mapa)
        self.assertEqual(
            Calculos.calcular_unidades_continente(mapa, J_MENGANO, "Africa"),
            BONIFICACIONES_CONTINENTE["Africa"],
        )

    def test_calcular_unidades_sin_toda_africa(self) -> None:
        """Prueba calcular unidades cuando el jugador no tiene toda África."""

        def build_mapa() -> dict[str, list[int | str | None]]:
            return {
                "Argentina": [1, "Africa", J_MENGANO],
                "Uruguay": [10, "Africa", J_FULANO],
                "Chile": [10, "America", J_MENGANO],
                "Brasil": [10, "Pangea", None],
            }

        mapa = Mapa(build_mapa)
        self.assertEqual(
            Calculos.calcular_unidades_continente(mapa, J_MENGANO, "Africa"), 0
        )

    def test_calcular_unidades_con_toda_oceania(self) -> None:
        """Prueba calcular unidades cuando el jugador tiene toda Oceanía."""

        def build_mapa() -> dict[str, list[int | str | None]]:
            return {
                "Argentina": [1, "Oceania", J_MENGANO],
                "Uruguay": [10, "Oceania", J_MENGANO],
                "Chile": [10, "America", J_MENGANO],
                "Brasil": [10, "Pangea", None],
            }

        mapa = Mapa(build_mapa)
        self.assertEqual(
            Calculos.calcular_unidades_continente(mapa, J_MENGANO, "Oceania"),
            BONIFICACIONES_CONTINENTE["Oceania"],
        )

    def test_calcular_unidades_sin_toda_ocenia(self) -> None:
        """Prueba calcular unidades cuando el jugador no tiene toda Oceanía."""

        def build_mapa() -> dict[str, list[int | str | None]]:
            return {
                "Argentina": [1, "Oceania", J_MENGANO],
                "Uruguay": [10, "Oceania", J_FULANO],
                "Chile": [10, "America", J_MENGANO],
                "Brasil": [10, "Pangea", None],
            }

        mapa = Mapa(build_mapa)
        self.assertEqual(
            Calculos.calcular_unidades_continente(mapa, J_MENGANO, "Oceania"), 0
        )

    def test_calcular_unidades_con_toda_america_del_sur(self) -> None:
        """Prueba calcular unidades cuando el jugador tiene toda América del Sur."""

        def build_mapa() -> dict[str, list[int | str | None]]:
            return {
                "Argentina": [1, "Sudamerica", J_MENGANO],
                "Uruguay": [10, "Sudamerica", J_MENGANO],
                "Chile": [10, "America", J_MENGANO],
                "Brasil": [10, "Pangea", None],
            }

        mapa = Mapa(build_mapa)
        self.assertEqual(
            Calculos.calcular_unidades_continente(mapa, J_MENGANO, "Sudamerica"),
            BONIFICACIONES_CONTINENTE["Sudamerica"],
        )

    def test_calcular_unidades_sin_toda_america_del_sur(self) -> None:
        """Prueba calcular unidades cuando el jugador no tiene toda América del Sur."""

        def build_mapa() -> dict[str, list[int | str | None]]:
            return {
                "Argentina": [1, "Sudamerica", J_MENGANO],
                "Uruguay": [10, "Sudamerica", J_FULANO],
                "Chile": [10, "America", J_MENGANO],
                "Brasil": [10, "Pangea", None],
            }

        mapa = Mapa(build_mapa)
        self.assertEqual(
            Calculos.calcular_unidades_continente(mapa, J_MENGANO, "Sudamerica"),
            0,
        )

    def test_calcular_unidades_con_toda_america_del_norte(self) -> None:
        """Prueba calcular unidades cuando el jugador tiene toda América del Norte."""

        def build_mapa() -> dict[str, list[int | str | None]]:
            return {
                "Argentina": [1, "Norteamerica", J_MENGANO],
                "Uruguay": [10, "Norteamerica", J_MENGANO],
                "Chile": [10, "America", J_MENGANO],
                "Brasil": [10, "Pangea", None],
            }

        mapa = Mapa(build_mapa)
        self.assertEqual(
            Calculos.calcular_unidades_continente(mapa, J_MENGANO, "Norteamerica"),
            BONIFICACIONES_CONTINENTE["Norteamerica"],
        )

    def test_calcular_unidades_sin_toda_america_del_norte(self) -> None:
        """Prueba calcular unidades sin toda América del Norte.

        Verifica cuando el jugador no tiene toda América del Norte.
        """

        def build_mapa() -> dict[str, list[int | str | None]]:
            return {
                "Argentina": [1, "Norteamerica", J_MENGANO],
                "Uruguay": [10, "Norteamerica", J_FULANO],
                "Chile": [10, "America", J_MENGANO],
                "Brasil": [10, "Pangea", None],
            }

        mapa = Mapa(build_mapa)
        self.assertEqual(
            Calculos.calcular_unidades_continente(mapa, J_MENGANO, "Norteamerica"),
            0,
        )


if __name__ == "__main__":
    unittest.main()
