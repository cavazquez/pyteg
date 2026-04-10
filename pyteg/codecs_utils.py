"""Utilidades simples para codificación UTF-8."""

from __future__ import annotations

import codecs


class Utf8:
    """Utilidades para codificación y decodificación UTF-8."""

    @staticmethod
    def encode(data: str) -> bytes:
        """Codifica una cadena de texto a bytes UTF-8.

        Args:
            data: Cadena de texto a codificar.

        Returns:
            Bytes codificados en UTF-8.

        """
        return codecs.encode(data, encoding="utf-8")

    @staticmethod
    def decode(data: bytes) -> str:
        """Decodifica bytes UTF-8 a una cadena de texto.

        Args:
            data: Bytes a decodificar.

        Returns:
            Cadena de texto decodificada.

        """
        return codecs.decode(data, encoding="utf-8")
