"""Animaciones de refuerzos a partir de las transiciones públicas del mapa."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pyteg.gui.mapa.scene import QCustomGraphicsScene

type _CountryUnits = tuple[int | None, int, bool]


class CountryUnitAnimations:
    """Recuerda lo dibujado para distinguir refuerzos, conquistas y recargas."""

    def __init__(self) -> None:
        """Inicializa la comparación sin mantener un estado autoritativo."""
        self._scene: QCustomGraphicsScene | None = None
        self._previous: dict[str, _CountryUnits] = {}

    def update(
        self,
        scene: QCustomGraphicsScene | None,
        snapshot: dict[str, Any],
        names: set[str] | None = None,
        *,
        animate: bool = False,
    ) -> None:
        """Señala aumentos del mismo propietario sin animar sincronizaciones."""
        if scene is not self._scene:
            self._scene = scene
            self._previous.clear()
        countries = snapshot.get("countries")
        if scene is None or not isinstance(countries, dict):
            return
        for name, raw in countries.items():
            if names is not None and name not in names:
                continue
            if not isinstance(raw, dict) or not isinstance(raw.get("unidades"), int):
                continue
            country = scene.paises.get(name)
            if country is None:
                continue
            owner = raw.get("userid")
            current = (
                owner if isinstance(owner, int) else None,
                raw["unidades"],
                raw.get("compartido") is True,
            )
            gain = self._gain(self._previous.get(name), current)
            if animate and snapshot.get("estado") == "JUGANDO" and gain > 0:
                country.mostrar_refuerzo_flotante(gain)
            self._previous[name] = current

    @staticmethod
    def _gain(previous: _CountryUnits | None, current: _CountryUnits) -> int:
        if (
            previous is None
            or current[0] is None
            or previous[0] != current[0]
            or previous[2]
            or current[2]
        ):
            return 0
        return max(0, current[1] - previous[1])
