"""Utilidades de locale para tests que assertan cadenas traducidas."""

from __future__ import annotations

from pyteg.i18n import set_language


def use_spanish() -> None:
    """Fija el idioma de la app en español (msgid sin traducir)."""
    set_language("es")
