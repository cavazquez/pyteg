import unittest

from src.colores import Amarillo
from src.server_color import ServerColor


class TestServerColor(unittest.TestCase):
    def test_reservar_color(self):
        server_color = ServerColor()
        cant_colores_originales = len(server_color.colores_disponibles())
        un_color = server_color.colores_disponibles()[0]
        server_color.reservar_color(un_color)
        cant_colores = len(server_color.colores_disponibles())
        self.assertEqual(cant_colores_originales - 1, cant_colores)

    def test_liberar_color(self):
        server_color = ServerColor()
        cant_colores_originales = len(server_color.colores_disponibles())
        un_color = server_color.colores_disponibles()[0]
        server_color.reservar_color(un_color)
        server_color.liberar_color(un_color)
        cant_colores = len(server_color.colores_disponibles())
        self.assertEqual(cant_colores_originales, cant_colores)

    def test_obtener_color_de_hexrgb(self):
        server_color = ServerColor()
        un_color = server_color.obtener_color_de_hexrgb("#ffff00")
        self.assertEqual(Amarillo().to_hex(), un_color.to_hex())
        un_color = server_color.obtener_color_de_hexrgb("#123")
        self.assertIsNone(un_color)
