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

    @unittest.skip("No terminado")
    def test_batalla_donde_siempre_gana_atacante(self):
        def build_mapa():
            return {'Argentina': [5, 'Africa', 'Mengano'],
                    'Uruguay': [10, 'Africa', 'Fulano'], 
                    'Chile': [1, 'America', None]}
        mapa = Mapa(build_mapa)
        Batalla.ataquen(mapa, 'Argentina', 'Uruguay')

