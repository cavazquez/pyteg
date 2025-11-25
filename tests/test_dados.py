import unittest

from src.dados import Dados


class TestDados(unittest.TestCase):
    def test_tirar_dados(self) -> None:
        tirada = Dados.tirar_dados(3)
        self.assertEqual(len(tirada), 3)
        self.assertTrue(all(n >= 1 and n <= 6 for n in tirada))

    def test_tirar_dados_ordenados(self) -> None:
        tirada = Dados.tirar_dados_ordenados(3)
        self.assertEqual(len(tirada), 3)
        self.assertTrue(all(n >= 1 and n <= 6 for n in tirada))
        self.assertListEqual(sorted(tirada, reverse=True), tirada)
