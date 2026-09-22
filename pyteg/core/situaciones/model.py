"""Modelos inmutables y contexto de las cartas de situación.

Las cartas describen reglas de una ronda, no países concretos.  El contexto
expone sólo las capacidades que un efecto necesita para que las mismas reglas
funcionen con cualquier mapa compatible.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pyteg.protocols.mapa import IMapProtocol


@dataclass(frozen=True, slots=True)
class SituationCard:
    """Descripción pública de una carta del mazo.

    ``effect_id`` se resuelve mediante el registro de efectos.  ``parameter``
    se usa para variantes parametrizadas, como el color de una carta Descanso.
    """

    card_id: str
    name: str
    effect_id: str
    parameter: str | None = None

    def to_public_dict(self, round_number: int) -> dict[str, str | int | None]:
        """Serializa la carta activa sin exponer estado privado.

        Returns:
            Payload JSON-serializable para el snapshot público.

        """
        return {
            "id": self.card_id,
            "nombre": self.name,
            "efecto": self.effect_id,
            "parametro": self.parameter,
            "ronda": round_number,
        }


@dataclass(frozen=True, slots=True)
class NoSituationCard(SituationCard):
    """Carta nula para partidas sin mazo o mazos agotados."""

    card_id: str = "none"
    name: str = "Sin situación"
    effect_id: str = "none"
    parameter: str | None = None


@dataclass(frozen=True, slots=True)
class SituationContext:
    """Vista de sólo lectura que reciben las estrategias."""

    mapa: IMapProtocol
    round_number: int = 1
    player_ids: tuple[int, ...] = ()
    player_colors: Mapping[int, str | None] = field(default_factory=dict)

    def color_keys(self) -> frozenset[str]:
        """Devuelve colores presentes en la ronda, sin valores nulos.

        Returns:
            Conjunto de colores normalizados en minúsculas.

        """
        return frozenset(
            color.lower()
            for color in self.player_colors.values()
            if isinstance(color, str) and color
        )

    def countries_owned_by(self, player_id: int) -> int:
        """Cuenta países ocupados por un jugador usando el mapa vigente.

        Returns:
            Cantidad de países que posee el jugador.

        """
        return sum(
            self.mapa.ocupado_por(country) == int(player_id)
            for country in self.mapa.paises()
        )


@dataclass(slots=True)
class SituationState:
    """Estado temporal creado al revelar una carta."""

    blocked_card_claims: set[int] = field(default_factory=set)
    crisis_rolls: dict[int, int] = field(default_factory=dict)


PlayerColors = Mapping[int, str | None]
PlayerIds = Sequence[int]
