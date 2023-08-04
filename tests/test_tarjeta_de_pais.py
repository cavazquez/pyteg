import unittest

from src.tarjeta_de_pais import TarjetaDePais


class TestTarjetaDePais(unittest.TestCase):
    def test_creation_instance(self):
        tarjeta = TarjetaDePais("Argentina", "Galeon")
        self.assertEqual(tarjeta.dame_pais(), "Argentina")
        self.assertEqual(tarjeta.dame_simbolo(), "Galeon")
