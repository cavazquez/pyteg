import unittest

from src.server_mapa import Mapa
from src.turnos import PrimerTurno, SegundoTurno, SiguientesTurnos


class TestPrimerTurno(unittest.TestCase):
    def test_jugador_actual(self):
        primer_turno = PrimerTurno("Fulano")
        self.assertEqual(primer_turno.jugador_actual(), "Fulano")

    def test_cant_unidades(self):
        primer_turno = PrimerTurno("Fulano")
        self.assertEqual(primer_turno.cant_unidades(), 6)

    def test_usar_unidad(self):
        primer_turno = PrimerTurno("Fulano")
        primer_turno.usar_unidad()
        self.assertEqual(primer_turno.cant_unidades(), 5)

    def test_agregar_unidades_generales(self):
        primer_turno = PrimerTurno("Fulano")
        cant_unidades = primer_turno.cant_unidades()
        primer_turno.agregar_unidades_generales(10)
        self.assertEqual(primer_turno.cant_unidades(), cant_unidades + 10)


class TestSegundoTurno(unittest.TestCase):
    def test_jugador_actual(self):
        segundo_turno = SegundoTurno("Fulano")
        self.assertEqual(segundo_turno.jugador_actual(), "Fulano")

    def test_cant_unidades(self):
        segundo_turno = SegundoTurno("Fulano")
        self.assertEqual(segundo_turno.cant_unidades(), 3)

    def test_usar_unidad(self):
        segundo_turno = SegundoTurno("Fulano")
        segundo_turno.usar_unidad()
        self.assertEqual(segundo_turno.cant_unidades(), 2)

    def test_agregar_unidades_generales(self):
        turno = SegundoTurno("Fulano")
        cant_unidades = turno.cant_unidades()
        turno.agregar_unidades_generales(10)
        self.assertEqual(turno.cant_unidades(), cant_unidades + 10)


class TestSiguientesTurnos(unittest.TestCase):
    def test_jugador_actual(self):
        def build_mapa():
            return {
                "Argentina": [5, "Africa", "Mengano"],
                "Uruguay": [10, "Africa", "Fulano"],
                "Chile": [1, "America", None],
            }

        mapa = Mapa(build_mapa)
        siguientes_turnos = SiguientesTurnos("Fulano", mapa)
        self.assertEqual(siguientes_turnos.jugador_actual(), "Fulano")

    def test_cant_unidades(self):
        def build_mapa():
            return {
                "Argentina": [5, "Africa", "Mengano"],
                "Uruguay": [10, "Africa", "Fulano"],
                "Chile": [1, "America", None],
            }

        mapa = Mapa(build_mapa)
        siguientes_turnos = SiguientesTurnos("Fulano", mapa)
        self.assertEqual(siguientes_turnos.cant_unidades(), 3)

    def test_usar_unidad(self):
        def build_mapa():
            return {
                "Argentina": [5, "Africa", "Mengano"],
                "Uruguay": [10, "Africa", "Fulano"],
                "Chile": [1, "America", None],
            }

        mapa = Mapa(build_mapa)
        siguientes_turnos = SiguientesTurnos("Fulano", mapa)
        siguientes_turnos.usar_unidad()
        self.assertEqual(siguientes_turnos.cant_unidades(), 2)

    def test_agregar_unidades_generales(self):
        def build_mapa():
            return {
                "Argentina": [5, "Africa", "Mengano"],
                "Uruguay": [10, "Africa", "Fulano"],
                "Chile": [1, "America", None],
            }

        mapa = Mapa(build_mapa)
        turno = SiguientesTurnos("Fulano", mapa)
        cant_unidades = turno.cant_unidades()
        turno.agregar_unidades_generales(10)
        self.assertEqual(turno.cant_unidades(), cant_unidades + 10)

    def test_usar_unidad_toda_africa_en_africa(self):
        def build_mapa():
            return {
                "Argentina": [5, "Africa", "Fulano"],
                "Uruguay": [10, "Africa", "Fulano"],
                "Chile": [1, "America", None],
            }

        mapa = Mapa(build_mapa)
        siguientes_turnos = SiguientesTurnos("Fulano", mapa)
        unidades = siguientes_turnos.cant_unidades_africa()
        siguientes_turnos.usar_unidad_africa()
        self.assertEqual(siguientes_turnos.cant_unidades_africa(), unidades - 1)

    def test_usar_unidad_toda_europa_en_europa(self):
        def build_mapa():
            return {
                "Argentina": [5, "Europa", "Fulano"],
                "Uruguay": [10, "Europa", "Fulano"],
                "Chile": [1, "America", None],
            }

        mapa = Mapa(build_mapa)
        siguientes_turnos = SiguientesTurnos("Fulano", mapa)
        unidades = siguientes_turnos.cant_unidades_europa()
        siguientes_turnos.usar_unidad_europa()
        self.assertEqual(siguientes_turnos.cant_unidades_europa(), unidades - 1)

    def test_usar_unidad_toda_oceania_en_oceania(self):
        def build_mapa():
            return {
                "Argentina": [5, "Oceania", "Fulano"],
                "Uruguay": [10, "Oceania", "Fulano"],
                "Chile": [1, "America", None],
            }

        mapa = Mapa(build_mapa)
        siguientes_turnos = SiguientesTurnos("Fulano", mapa)
        unidades = siguientes_turnos.cant_unidades_oceania()
        siguientes_turnos.usar_unidad_oceania()
        self.assertEqual(siguientes_turnos.cant_unidades_oceania(), unidades - 1)

    def test_usar_unidad_toda_asia_en_asia(self):
        def build_mapa():
            return {
                "Argentina": [5, "Asia", "Fulano"],
                "Uruguay": [10, "Asia", "Fulano"],
                "Chile": [1, "America", None],
            }

        mapa = Mapa(build_mapa)
        siguientes_turnos = SiguientesTurnos("Fulano", mapa)
        unidades = siguientes_turnos.cant_unidades_asia()
        siguientes_turnos.usar_unidad_asia()
        self.assertEqual(siguientes_turnos.cant_unidades_asia(), unidades - 1)

    def test_usar_unidad_toda_sudamerica_en_sudamerica(self):
        def build_mapa():
            return {
                "Argentina": [5, "Sudamerica", "Fulano"],
                "Uruguay": [10, "Sudamerica", "Fulano"],
                "Chile": [1, "America", None],
            }

        mapa = Mapa(build_mapa)
        siguientes_turnos = SiguientesTurnos("Fulano", mapa)
        unidades = siguientes_turnos.cant_unidades_sudamerica()
        siguientes_turnos.usar_unidad_sudamerica()
        self.assertEqual(siguientes_turnos.cant_unidades_sudamerica(), unidades - 1)

    def test_usar_unidad_toda_norteamerica_en_norteamerica(self):
        def build_mapa():
            return {
                "Argentina": [5, "Norteamerica", "Fulano"],
                "Uruguay": [10, "Norteamerica", "Fulano"],
                "Chile": [1, "America", None],
            }

        mapa = Mapa(build_mapa)
        siguientes_turnos = SiguientesTurnos("Fulano", mapa)
        unidades = siguientes_turnos.cant_unidades_norteamerica()
        siguientes_turnos.usar_unidad_norteamerica()
        self.assertEqual(siguientes_turnos.cant_unidades_norteamerica(), unidades - 1)
