import unittest

from src.batalla import Batalla
from src.mapa import Mapa


class TestBatalla(unittest.TestCase):
    def test_calcular_dados_atacante_si_tengo_2(self):
        self.assertEqual(Batalla.calcular_cant_dados_atacante(2), 1)

    def test_calcular_dados_atacante_si_tengo_4(self):
        self.assertEqual(Batalla.calcular_cant_dados_atacante(4), 3)

    def test_calcular_dados_defensor_si_tengo_2(self):
        self.assertEqual(Batalla.calcular_cant_dados_defensor(2), 2)

    def test_calcular_dados_defensor_si_tengo_4(self):
        self.assertEqual(Batalla.calcular_cant_dados_atacante(4), 3)

    def test_batalla_donde_siempre_gana_atacante(self):
        def build_mapa():
            return {
                "Argentina": [5, "Africa", "Mengano"],
                "Uruguay": [10, "Africa", "Fulano"],
                "Chile": [1, "America", None],
            }

        mapa = Mapa(build_mapa)
        resultado = Batalla.ataquen(mapa, "Argentina", "Uruguay", [4, 3, 2], [3, 2, 1])
        self.assertCountEqual(resultado['restar'], ['Uruguay', 'Uruguay', 'Uruguay'])

    def test_batalla_donde_siempre_gana_defensor(self):
        def build_mapa():
            return {
                "Argentina": [5, "Africa", "Mengano"],
                "Uruguay": [10, "Africa", "Fulano"],
                "Chile": [1, "America", None],
            }

        mapa = Mapa(build_mapa)
        resultado = Batalla.ataquen(mapa, "Argentina", "Uruguay", [3, 2, 1], [4, 3, 2])
        self.assertCountEqual(
                resultado['restar'], ['Argentina', 'Argentina', 'Argentina'])
        self.assertEqual(resultado['atacante'], 'Argentina')
        self.assertEqual(resultado['defensor'], 'Uruguay')

    def test_batalla_atacan_2(self):
        def build_mapa():
            return {
                "Argentina": [3, "Africa", "Mengano"],
                "Uruguay": [10, "Africa", "Fulano"],
                "Chile": [1, "America", None],
            }

        mapa = Mapa(build_mapa)
        resultado = Batalla.ataquen(mapa, "Argentina", "Uruguay", [3, 2], [4, 3, 2])
        self.assertCountEqual(resultado['restar'], ['Argentina', 'Argentina'])


    def test_batalla_defiende_2(self):
        def build_mapa():
            return {
                "Argentina": [4, "Africa", "Mengano"],
                "Uruguay": [2, "Africa", "Fulano"],
                "Chile": [1, "America", None],
            }

        mapa = Mapa(build_mapa)
        resultado = Batalla.ataquen(mapa, "Argentina", "Uruguay", [4, 3, 2], [3, 2])
        self.assertCountEqual(resultado['restar'], ['Uruguay', 'Uruguay'])


    def test_batalla_uno_y_uno(self):
        def build_mapa():
            return {
                "Argentina": [4, "Africa", "Mengano"],
                "Uruguay": [2, "Africa", "Fulano"],
                "Chile": [1, "America", None],
            }

        mapa = Mapa(build_mapa)
        resultado = Batalla.ataquen(mapa, "Argentina", "Uruguay", [6, 3, 2], [5, 4])
        self.assertCountEqual(resultado['restar'], ['Argentina', 'Uruguay'])

