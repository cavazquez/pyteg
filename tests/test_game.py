import unittest

from src.game import Game
#from src.server import Server


class TestGame(unittest.TestCase):
    def test_create_instance(self):
        server = ""
        self.assertTrue(Game(server))
