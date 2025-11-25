"""Representación sencilla de un país."""

from __future__ import annotations


class Country:
    def __init__(self, name: str) -> None:
        self._name = name

    def get_name(self) -> str:
        return self._name
