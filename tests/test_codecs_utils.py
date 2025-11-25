"""Tests para el módulo de utilidades de codificación UTF-8."""

import unittest

from src.codecs_utils import Utf8


class TestUtf8(unittest.TestCase):
    """Tests para la clase Utf8."""

    def test_encode_returns_utf8_bytes(self) -> None:
        """Prueba que encode retorne bytes UTF-8."""
        data = "mensaje con ñ y 😊"
        esperado = data.encode("utf-8")
        self.assertEqual(Utf8.encode(data), esperado)

    def test_decode_returns_original_string(self) -> None:
        """Prueba que decode retorne la cadena original."""
        data = "hola μ"
        bytes_data = data.encode("utf-8")
        self.assertEqual(Utf8.decode(bytes_data), data)

    def test_roundtrip_preserves_content(self) -> None:
        """Prueba que encode/decode preserve el contenido."""
        original = "línea con salto\n次"
        self.assertEqual(Utf8.decode(Utf8.encode(original)), original)

    def test_decode_invalid_bytes_raises_unicode_decode_error(self) -> None:
        """Prueba que decode con bytes inválidos lance UnicodeDecodeError."""
        with self.assertRaises(UnicodeDecodeError):
            Utf8.decode(b"\xff\xfe")
