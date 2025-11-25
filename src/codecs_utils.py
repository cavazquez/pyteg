"""Utilidades simples para codificación UTF-8."""

from __future__ import annotations

import codecs


class Utf8:
    @staticmethod
    def encode(data: str) -> bytes:
        return codecs.encode(data, encoding="utf-8")

    @staticmethod
    def decode(data: bytes) -> str:
        return codecs.decode(data, encoding="utf-8")
