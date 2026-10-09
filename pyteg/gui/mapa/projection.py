"""Proyección de un snapshot público sobre países del mapa, sin comandos."""

from __future__ import annotations

from typing import Any

from PySide6.QtGui import QColor


def country_color(value: object) -> QColor:
    """Convierte los colores públicos en colores Qt.

    Returns:
        Color RGB válido o gris si no hay propietario.

    """
    if isinstance(value, dict):
        return QColor(
            int(value.get("r", 136)), int(value.get("g", 136)), int(value.get("b", 136))
        )
    return QColor(value) if isinstance(value, str) else QColor("#888888")


def render_countries(
    scene: Any, snapshot: dict[str, Any], names: set[str] | None = None
) -> None:
    """Muestra unidades, propietarios, condominios y misiles de un estado."""
    countries = snapshot.get("countries")
    if scene is None or not isinstance(countries, dict):
        return
    players = {
        player["userid"]: player
        for player in snapshot.get("players", [])
        if isinstance(player, dict)
    }
    for name, raw in countries.items():
        if names is not None and name not in names:
            continue
        if not isinstance(raw, dict):
            continue
        country = scene.paises.get(name)
        if country is None:
            continue
        if isinstance(raw.get("unidades"), int):
            country.set_unidades(raw["unidades"])
        _render_ownership(country, raw, players)
        update_missiles = getattr(country, "actualizar_misiles", None)
        if isinstance(raw.get("misiles"), int) and callable(update_missiles):
            update_missiles(raw["misiles"])


def _render_ownership(
    country: Any, raw: dict[str, Any], players: dict[int, dict[str, Any]]
) -> None:
    update_occupants = getattr(country, "actualizar_ocupantes", None)
    if raw.get("compartido") is True and isinstance(raw.get("ocupantes"), list):
        occupants = [
            (
                str(players.get(item["userid"], {}).get("username") or item["userid"]),
                item["unidades"],
                country_color(players.get(item["userid"], {}).get("color")),
            )
            for item in raw["ocupantes"]
            if isinstance(item, dict)
            and isinstance(item.get("userid"), int)
            and isinstance(item.get("unidades"), int)
            and item["unidades"] > 0
        ]
        if callable(update_occupants):
            update_occupants(occupants)
    else:
        if callable(update_occupants):
            update_occupants(None)
        owner = raw.get("userid")
        player = players.get(owner, {}) if isinstance(owner, int) else {}
        country.set_color(country_color(player.get("color")))
