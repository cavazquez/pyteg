import unittest

from src.server_client import Client
from src.game import Game


class TestEjecutarMensaje(unittest.TestCase):

    def test_asignar_username(self):
        data = {'mensaje':'username', 'nombre': 'Fulano'}
        game = Game()
        cliente = Client(1, "conn", "server")
        cliente.ejecutar_mensaje(data, game)
        self.assertEqual(game.jugadores()[1], 'Fulano')


    def test_no_permitir_asignar_2_veces_username(self):
        data = {'mensaje':'username', 'nombre': 'Fulano'}
        game = Game()
        cliente = Client(1, "conn", "server")
        cliente.ejecutar_mensaje(data, game)
        data = {'mensaje':'username', 'nombre': 'Mengano'}
        cliente.ejecutar_mensaje(data, game)
        self.assertEqual(game.jugadores()[1], 'Fulano')


