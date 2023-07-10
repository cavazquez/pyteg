import unittest

from src.mapa import Mapa


class TestMap(unittest.TestCase):
    def test_creation_instance(self):
        def build_mapa():
            return None
        self.assertTrue(Mapa(build_mapa))

    def test_cant_unidades(self):
        def build_mapa():
            return {'Argentina': [1, 'Pangea', None]}
        mapa = Mapa(build_mapa)
        self.assertEqual(mapa.cantidad_unidades('Argentina'), 1)
        mapa.agregar_una_unidad('Argentina')
        self.assertEqual(mapa.cantidad_unidades('Argentina'), 2)

    def test_set_unidades(self):
        def build_mapa():
            return {'Argentina': [1, 'Pangea', None]}
        mapa = Mapa(build_mapa)
        mapa.set_unidades('Argentina', 5)
        self.assertEqual(mapa.cantidad_unidades('Argentina'), 5)


    def test_mover_unidades(self):
        def build_mapa():
            return {'Argentina': [1, 'Pangea', None], 'Uruguay': [10, 'Pangea', None]}
        mapa = Mapa(build_mapa)
        mapa.mover('Uruguay','Argentina', 6)
        self.assertEqual(mapa.cantidad_unidades('Argentina'), 7)
        self.assertEqual(mapa.cantidad_unidades('Uruguay'), 4)

    def test_consultar_continente(self):
        def build_mapa():
            return {'Argentina': [1, 'Pangea', None]}
        mapa = Mapa(build_mapa)
        self.assertEqual(mapa.continente('Argentina'), 'Pangea')


    def test_ocupado_por(self):
        def build_mapa():
            return {'Argentina': [1, 'Pangea', 'Fulano']}
        mapa = Mapa(build_mapa)
        self.assertEqual(mapa.ocupado_por('Argentina'), 'Fulano')

    def test_paises(self):
        def build_mapa():
            return {'Argentina': [1, 'Pangea', None], 'Uruguay': [10, 'Pangea', None]}
        mapa = Mapa(build_mapa)
        self.assertSetEqual(set(mapa.paises()), set(['Uruguay','Argentina']))


    def test_cant_paises_por_continente(self):
        def build_mapa():
            return {'Argentina': [1, 'Pangea', None], 'Uruguay': [10, 'Pangea', None], 
                    'Chile': [1, 'America', None]}
        mapa = Mapa(build_mapa)
        self.assertEqual(mapa.cantidad_de_paises_por_continente('Pangea'), 2)
        self.assertEqual(mapa.cantidad_de_paises_por_continente('America'), 1)


    def test_asignar_pais(self):
        def build_mapa():
            return {'Argentina': [1, 'Pangea', 'Fulano']}
        mapa = Mapa(build_mapa)
        mapa.asignar_pais('Mengano','Argentina')
        self.assertEqual(mapa.ocupado_por('Argentina'), 'Mengano')


    def test_cant_paises_de_jugador(self):
        def build_mapa():
            return {'Argentina': [1, 'Pangea', None], 'Uruguay': [10, 'Pangea', None], 
                    'Chile': [1, 'America', None]}
        mapa = Mapa(build_mapa)
        mapa.asignar_pais('Mengano', 'Argentina')
        mapa.asignar_pais('Mengano', 'Chile')
        self.assertEqual(mapa.cantidad_de_paises_del_jugador('Mengano'), 2)
        self.assertEqual(mapa.cantidad_de_paises_del_jugador('Fulano'), 0)


    def test_cant_paises_del_jugador_por_continente(self):
        def build_mapa():
            return {'Argentina': [1, 'Pangea', None], 'Uruguay': [10, 'Pangea', None], 
                    'Chile': [1, 'America', None]}
        mapa = Mapa(build_mapa)
        mapa.asignar_pais('Mengano', 'Argentina')
        mapa.asignar_pais('Mengano', 'Uruguay')
        self.assertEqual(
                mapa.cantidad_de_paises_del_jugador_por_continente('Mengano','Pangea'), 2) # noqa: E501
        self.assertEqual(
                mapa.cantidad_de_paises_del_jugador_por_continente('Mengano','America'), 0) # noqa: E501


    def test_tiene_toda_europa(self):
        def build_mapa():
            return {'Argentina': [1, 'Europa', 'Mengano'],
                    'Uruguay': [10, 'Europa', None], 
                    'Chile': [1, 'America', None]}
        mapa = Mapa(build_mapa)
        self.assertFalse(mapa.tiene_toda_europa('Mengano'))
        mapa.asignar_pais('Mengano', 'Uruguay')
        self.assertTrue(mapa.tiene_toda_europa('Mengano'))


    def test_tiene_toda_asia(self):
        def build_mapa():
            return {'Argentina': [1, 'Asia', 'Mengano'],
                    'Uruguay': [10, 'Asia', None], 
                    'Chile': [1, 'America', None]}
        mapa = Mapa(build_mapa)
        self.assertFalse(mapa.tiene_toda_asia('Mengano'))
        mapa.asignar_pais('Mengano', 'Uruguay')


    def test_tiene_toda_oceania(self):
        def build_mapa():
            return {'Argentina': [1, 'Oceania', 'Mengano'],
                    'Uruguay': [10, 'Oceania', None], 
                    'Chile': [1, 'America', None]}
        mapa = Mapa(build_mapa)
        self.assertFalse(mapa.tiene_toda_oceania('Mengano'))
        mapa.asignar_pais('Mengano', 'Uruguay')

    def test_tiene_toda_america_del_sur(self):
        def build_mapa():
            return {'Argentina': [1, 'Sudamerica', 'Mengano'],
                    'Uruguay': [10, 'Sudamerica', None], 
                    'Chile': [1, 'America', None]}
        mapa = Mapa(build_mapa)
        self.assertFalse(mapa.tiene_toda_america_del_sur('Mengano'))
        mapa.asignar_pais('Mengano', 'Uruguay')

    def test_tiene_toda_america_del_norte(self):
        def build_mapa():
            return {'Argentina': [1, 'Norteamerica', 'Mengano'],
                    'Uruguay': [10, 'Norteamerica', None], 
                    'Chile': [1, 'America', None]}
        mapa = Mapa(build_mapa)
        self.assertFalse(mapa.tiene_toda_america_del_norte('Mengano'))
        mapa.asignar_pais('Mengano', 'Uruguay')


    def test_tiene_toda_africa(self):
        def build_mapa():
            return {'Argentina': [1, 'Africa', 'Mengano'],
                    'Uruguay': [10, 'Africa', None], 
                    'Chile': [1, 'America', None]}
        mapa = Mapa(build_mapa)
        self.assertFalse(mapa.tiene_toda_africa('Mengano'))
        mapa.asignar_pais('Mengano', 'Uruguay')

    def test_str(self):
        def build_mapa():
            return {'Argentina': [1, 'Africa', 'Mengano'],
                    'Uruguay': [10, 'Africa', None]
                    }
        mapa = Mapa(build_mapa)
        self.assertEqual(mapa.__str__(), '{"Argentina": [1, "Africa", "Mengano"], "Uruguay": [10, "Africa", null]}') # noqa: E501
