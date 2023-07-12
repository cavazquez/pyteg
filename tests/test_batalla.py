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
            return {'Argentina': [5, 'Africa', 'Mengano'],
                    'Uruguay': [10, 'Africa', 'Fulano'], 
                    'Chile': [1, 'America', None]}
        mapa = Mapa(build_mapa)
        Batalla.ataquen(mapa, 'Argentina', 'Uruguay', [4,3,2], [3,2,1])
        self.assertEqual(mapa.cantidad_unidades('Argentina'), 5)
        self.assertEqual(mapa.cantidad_unidades('Uruguay'), 7)


    def test_batalla_donde_siempre_gana_defensor(self):
        def build_mapa():
            return {'Argentina': [5, 'Africa', 'Mengano'],
                    'Uruguay': [10, 'Africa', 'Fulano'], 
                    'Chile': [1, 'America', None]}
        mapa = Mapa(build_mapa)
        Batalla.ataquen(mapa, 'Argentina', 'Uruguay', [3,2,1], [4,3,2])
        self.assertEqual(mapa.cantidad_unidades('Argentina'), 2)
        self.assertEqual(mapa.cantidad_unidades('Uruguay'), 10)


    def test_batalla_atacan_2(self):
        def build_mapa():
            return {'Argentina': [3, 'Africa', 'Mengano'],
                    'Uruguay': [10, 'Africa', 'Fulano'], 
                    'Chile': [1, 'America', None]}
        mapa = Mapa(build_mapa)
        Batalla.ataquen(mapa, 'Argentina', 'Uruguay', [3,2], [4,3,2])
        self.assertEqual(mapa.cantidad_unidades('Argentina'), 1)
        self.assertEqual(mapa.cantidad_unidades('Uruguay'), 10)


    def test_batalla_defiende_2(self):
        def build_mapa():
            return {'Argentina': [4, 'Africa', 'Mengano'],
                    'Uruguay': [2, 'Africa', 'Fulano'], 
                    'Chile': [1, 'America', None]}
        mapa = Mapa(build_mapa)
        Batalla.ataquen(mapa, 'Argentina', 'Uruguay', [4,3,2], [3,2])
        self.assertEqual(mapa.cantidad_unidades('Argentina'), 4)
        self.assertEqual(mapa.cantidad_unidades('Uruguay'), 0)

