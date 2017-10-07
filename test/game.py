import unittest

from src.game import Game


class TestGame(unittest.TestCase):
    def test_create_instance(self):
        self.assertTrue(Game())
