"""Modelo minimalista de cliente."""

from __future__ import annotations

from typing import Any


class Client:
    def __init__(self) -> None:
        self._username: str | None = None
        self._userid: Any = None
        self._es_admin = False

    def set_username(self, username: str) -> None:
        self._username = username

    def set_userid(self, userid: Any) -> None:
        self._userid = userid

    def username(self) -> str | None:
        return self._username

    def userid(self) -> Any:
        return self._userid

    def es_admin(self) -> bool:
        return self._es_admin

    def ahora_es_admin(self) -> None:
        self._es_admin = True
