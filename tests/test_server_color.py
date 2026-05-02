"""Tests para el módulo de gestión de colores del servidor."""

import unittest

from pyteg.colores import Amarillo
from pyteg.server.juego.color import ServerColor


class TestServerColor(unittest.TestCase):
    """Tests para la clase ServerColor."""

    def test_reservar_color(self) -> None:
        """Prueba reservar un color."""
        server_color = ServerColor()
        cant_colores_originales = len(server_color.colores_disponibles())
        un_color = server_color.colores_disponibles()[0]
        server_color.reservar_color(un_color)
        cant_colores = len(server_color.colores_disponibles())
        self.assertEqual(cant_colores_originales - 1, cant_colores)

    def test_liberar_color(self) -> None:
        """Prueba liberar un color reservado."""
        server_color = ServerColor()
        cant_colores_originales = len(server_color.colores_disponibles())
        un_color = server_color.colores_disponibles()[0]
        server_color.reservar_color(un_color)
        server_color.liberar_color(un_color)
        cant_colores = len(server_color.colores_disponibles())
        self.assertEqual(cant_colores_originales, cant_colores)

    def test_obtener_color_de_hexrgb(self) -> None:
        """Prueba obtener un color a partir de su código hexadecimal RGB."""
        server_color = ServerColor()
        un_color = server_color.obtener_color_de_hexrgb("#ffff00")
        self.assertIsNotNone(un_color)
        if un_color is None:
            self.fail("No se encontró el color esperado")
        self.assertEqual(Amarillo().to_hex(), un_color.to_hex())
        un_color = server_color.obtener_color_de_hexrgb("#123")
        self.assertIsNone(un_color)
