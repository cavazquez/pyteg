import unittest

from src.game import Game
from src.mapa import Mapa


class TestGame(unittest.TestCase):
    def test_create_instance(self):
        def build_mapa():
            return None
        mapa = Mapa(build_mapa)
        self.assertTrue(Game(mapa))
