"""Tests para el módulo de turnos."""

from __future__ import annotations

import unittest

from pyteg.core.turnos.turnos import PrimerTurno, SegundoTurno, SiguientesTurnos
from pyteg.server.juego.mapa import Mapa

J_FULANO = 1
J_MENGANO = 2


class TestPrimerTurno(unittest.TestCase):
    """Tests para PrimerTurno."""

    def test_jugador_actual(self) -> None:
        """Prueba obtener el jugador actual del primer turno."""
        primer_turno = PrimerTurno(J_FULANO)
        self.assertEqual(primer_turno.jugador_actual(), J_FULANO)

    def test_cant_unidades(self) -> None:
        """Prueba obtener la cantidad de unidades del primer turno."""
        primer_turno = PrimerTurno(J_FULANO)
        self.assertEqual(primer_turno.cant_unidades(), 6)

    def test_usar_unidad(self) -> None:
        """Prueba usar una unidad en el primer turno."""
        primer_turno = PrimerTurno(J_FULANO)
        primer_turno.usar_unidad()
        self.assertEqual(primer_turno.cant_unidades(), 5)

    def test_agregar_unidades_generales(self) -> None:
        """Prueba agregar unidades generales en el primer turno."""
        primer_turno = PrimerTurno(J_FULANO)
        cant_unidades = primer_turno.cant_unidades()
        primer_turno.agregar_unidades_generales(10)
        self.assertEqual(primer_turno.cant_unidades(), cant_unidades + 10)


class TestSegundoTurno(unittest.TestCase):
    """Tests para SegundoTurno."""

    def test_jugador_actual(self) -> None:
        """Prueba obtener el jugador actual del segundo turno."""
        segundo_turno = SegundoTurno(J_FULANO)
        self.assertEqual(segundo_turno.jugador_actual(), J_FULANO)

    def test_cant_unidades(self) -> None:
        """Prueba obtener la cantidad de unidades del segundo turno."""
        segundo_turno = SegundoTurno(J_FULANO)
        self.assertEqual(segundo_turno.cant_unidades(), 3)

    def test_usar_unidad(self) -> None:
        """Prueba usar una unidad en el segundo turno."""
        segundo_turno = SegundoTurno(J_FULANO)
        segundo_turno.usar_unidad()
        self.assertEqual(segundo_turno.cant_unidades(), 2)

    def test_agregar_unidades_generales(self) -> None:
        """Prueba agregar unidades generales en el segundo turno."""
        turno = SegundoTurno(J_FULANO)
        cant_unidades = turno.cant_unidades()
        turno.agregar_unidades_generales(10)
        self.assertEqual(turno.cant_unidades(), cant_unidades + 10)


class TestSiguientesTurnos(unittest.TestCase):
    """Tests para SiguientesTurnos."""

    def test_jugador_actual(self) -> None:
        """Prueba obtener el jugador actual de los siguientes turnos."""

        def build_mapa() -> dict[str, list[int | str | None]]:
            return {
                "Argentina": [5, "Africa", J_MENGANO],
                "Uruguay": [10, "Africa", J_FULANO],
                "Chile": [1, "America", None],
            }

        mapa = Mapa(build_mapa)
        siguientes_turnos = SiguientesTurnos(J_FULANO, mapa)
        self.assertEqual(siguientes_turnos.jugador_actual(), J_FULANO)

    def test_cant_unidades(self) -> None:
        """Prueba obtener la cantidad de unidades de los siguientes turnos."""

        def build_mapa() -> dict[str, list[int | str | None]]:
            return {
                "Argentina": [5, "Africa", J_MENGANO],
                "Uruguay": [10, "Africa", J_FULANO],
                "Chile": [1, "America", None],
            }

        mapa = Mapa(build_mapa)
        siguientes_turnos = SiguientesTurnos(J_FULANO, mapa)
        self.assertEqual(siguientes_turnos.cant_unidades(), 3)

    def test_usar_unidad(self) -> None:
        """Prueba usar una unidad en los siguientes turnos."""

        def build_mapa() -> dict[str, list[int | str | None]]:
            return {
                "Argentina": [5, "Africa", J_MENGANO],
                "Uruguay": [10, "Africa", J_FULANO],
                "Chile": [1, "America", None],
            }

        mapa = Mapa(build_mapa)
        siguientes_turnos = SiguientesTurnos(J_FULANO, mapa)
        siguientes_turnos.usar_unidad()
        self.assertEqual(siguientes_turnos.cant_unidades(), 2)

    def test_agregar_unidades_generales(self) -> None:
        """Prueba agregar unidades generales en los siguientes turnos."""

        def build_mapa() -> dict[str, list[int | str | None]]:
            return {
                "Argentina": [5, "Africa", J_MENGANO],
                "Uruguay": [10, "Africa", J_FULANO],
                "Chile": [1, "America", None],
            }

        mapa = Mapa(build_mapa)
        turno = SiguientesTurnos(J_FULANO, mapa)
        cant_unidades = turno.cant_unidades()
        turno.agregar_unidades_generales(10)
        self.assertEqual(turno.cant_unidades(), cant_unidades + 10)

    def test_usar_unidad_toda_africa_en_africa(self) -> None:
        """Prueba usar unidad de África cuando se tiene toda África."""

        def build_mapa() -> dict[str, list[int | str | None]]:
            return {
                "Argentina": [5, "Africa", J_FULANO],
                "Uruguay": [10, "Africa", J_FULANO],
                "Chile": [1, "America", None],
            }

        mapa = Mapa(build_mapa)
        siguientes_turnos = SiguientesTurnos(J_FULANO, mapa)
        unidades = siguientes_turnos.cant_unidades_por_continente("Africa")
        siguientes_turnos.usar_unidad_por_continente("Africa")
        self.assertEqual(
            siguientes_turnos.cant_unidades_por_continente("Africa"), unidades - 1
        )

    def test_usar_unidad_toda_europa_en_europa(self) -> None:
        """Prueba usar unidad de Europa cuando se tiene toda Europa."""

        def build_mapa() -> dict[str, list[int | str | None]]:
            return {
                "Argentina": [5, "Europa", J_FULANO],
                "Uruguay": [10, "Europa", J_FULANO],
                "Chile": [1, "America", None],
            }

        mapa = Mapa(build_mapa)
        siguientes_turnos = SiguientesTurnos(J_FULANO, mapa)
        unidades = siguientes_turnos.cant_unidades_por_continente("Europa")
        siguientes_turnos.usar_unidad_por_continente("Europa")
        self.assertEqual(
            siguientes_turnos.cant_unidades_por_continente("Europa"), unidades - 1
        )

    def test_usar_unidad_toda_oceania_en_oceania(self) -> None:
        """Prueba usar unidad de Oceanía cuando se tiene toda Oceanía."""

        def build_mapa() -> dict[str, list[int | str | None]]:
            return {
                "Argentina": [5, "Oceania", J_FULANO],
                "Uruguay": [10, "Oceania", J_FULANO],
                "Chile": [1, "America", None],
            }

        mapa = Mapa(build_mapa)
        siguientes_turnos = SiguientesTurnos(J_FULANO, mapa)
        unidades = siguientes_turnos.cant_unidades_por_continente("Oceania")
        siguientes_turnos.usar_unidad_por_continente("Oceania")
        self.assertEqual(
            siguientes_turnos.cant_unidades_por_continente("Oceania"), unidades - 1
        )

    def test_usar_unidad_toda_asia_en_asia(self) -> None:
        """Prueba usar unidad de Asia cuando se tiene toda Asia."""

        def build_mapa() -> dict[str, list[int | str | None]]:
            return {
                "Argentina": [5, "Asia", J_FULANO],
                "Uruguay": [10, "Asia", J_FULANO],
                "Chile": [1, "America", None],
            }

        mapa = Mapa(build_mapa)
        siguientes_turnos = SiguientesTurnos(J_FULANO, mapa)
        unidades = siguientes_turnos.cant_unidades_por_continente("Asia")
        siguientes_turnos.usar_unidad_por_continente("Asia")
        self.assertEqual(
            siguientes_turnos.cant_unidades_por_continente("Asia"), unidades - 1
        )

    def test_usar_unidad_toda_sudamerica_en_sudamerica(self) -> None:
        """Prueba usar unidad de Sudamérica cuando se tiene toda Sudamérica."""

        def build_mapa() -> dict[str, list[int | str | None]]:
            return {
                "Argentina": [5, "Sudamerica", J_FULANO],
                "Uruguay": [10, "Sudamerica", J_FULANO],
                "Chile": [1, "America", None],
            }

        mapa = Mapa(build_mapa)
        siguientes_turnos = SiguientesTurnos(J_FULANO, mapa)
        unidades = siguientes_turnos.cant_unidades_por_continente("Sudamerica")
        siguientes_turnos.usar_unidad_por_continente("Sudamerica")
        self.assertEqual(
            siguientes_turnos.cant_unidades_por_continente("Sudamerica"), unidades - 1
        )

    def test_usar_unidad_toda_norteamerica_en_norteamerica(self) -> None:
        """Prueba usar unidad de Norteamérica cuando se tiene toda Norteamérica."""

        def build_mapa() -> dict[str, list[int | str | None]]:
            return {
                "Argentina": [5, "Norteamerica", J_FULANO],
                "Uruguay": [10, "Norteamerica", J_FULANO],
                "Chile": [1, "America", None],
            }

        mapa = Mapa(build_mapa)
        siguientes_turnos = SiguientesTurnos(J_FULANO, mapa)
        unidades = siguientes_turnos.cant_unidades_por_continente("Norteamerica")
        siguientes_turnos.usar_unidad_por_continente("Norteamerica")
        self.assertEqual(
            siguientes_turnos.cant_unidades_por_continente("Norteamerica"), unidades - 1
        )


if __name__ == "__main__":
    unittest.main()
