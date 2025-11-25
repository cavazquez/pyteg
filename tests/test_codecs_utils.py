import unittest

from src.codecs_utils import Utf8


class TestUtf8(unittest.TestCase):
    def test_encode_returns_utf8_bytes(self) -> None:
        data = "mensaje con ñ y 😊"
        esperado = data.encode("utf-8")
        self.assertEqual(Utf8.encode(data), esperado)

    def test_decode_returns_original_string(self) -> None:
        data = "hola μ"
        bytes_data = data.encode("utf-8")
        self.assertEqual(Utf8.decode(bytes_data), data)

    def test_roundtrip_preserves_content(self) -> None:
        original = "línea con salto\n次"
        self.assertEqual(Utf8.decode(Utf8.encode(original)), original)

    def test_decode_invalid_bytes_raises_unicode_decode_error(self) -> None:
        with self.assertRaises(UnicodeDecodeError):
            Utf8.decode(b"\xff\xfe")
