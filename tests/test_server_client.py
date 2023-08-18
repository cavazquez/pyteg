import unittest

from src.game import Game
from src.mapa import Mapa
from src.server_client import Client


class TestEjecutarMensaje(unittest.TestCase):
    def test_mensaje_inexistente(self):
        data = {"mensaje": "noexiste"}
        game = Game(Mapa(lambda: None), None)
        cliente = Client(1, "conn", "server")
        with self.assertRaises(Exception):
            cliente.ejecutar_mensaje(data, game)

    def test_asignar_username(self):
        game = Game(Mapa(lambda: None), None)
        data = {"mensaje": "username", "nombre": "Fulano"}
        cliente = Client(1, "conn", "server")
        cliente.ejecutar_mensaje(data, game)
        self.assertEqual(game.jugadores().get(1), "Fulano")
        self.assertEqual(cliente.username(), "Fulano")

    def test_no_permitir_asignar_2_veces_username(self):
        game = Game(Mapa(lambda: None), None)
        data = {"mensaje": "username", "nombre": "Fulano"}
        cliente = Client(1, "conn", "server")
        cliente.ejecutar_mensaje(data, game)
        data = {"mensaje": "username", "nombre": "Mengano"}
        cliente.ejecutar_mensaje(data, game)
        self.assertEqual(game.jugadores().get(1), "Fulano")
        self.assertEqual(cliente.username(), "Fulano")

    def test_agregar_2_jugadores(self):
        game = Game(Mapa(lambda: None), None)
        data = {"mensaje": "username", "nombre": "Fulano"}
        cliente = Client(1, "conn", "server")
        cliente.ejecutar_mensaje(data, game)
        data = {"mensaje": "username", "nombre": "Mengano"}
        cliente2 = Client(2, "conn", "server")
        cliente2.ejecutar_mensaje(data, game)
        self.assertEqual(game.jugadores().get(1), "Fulano")
        self.assertEqual(game.jugadores().get(2), "Mengano")

    def test_enviar_chat(self):
        data = {"mensaje": "chat", "chat": "Hola"}
        msg = data["chat"]
        cliente = Client(1, "conn", "server")
        self.assertEqual(f"{cliente.username()}: {msg}", cliente.mensaje_chat(msg))
