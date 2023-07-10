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

