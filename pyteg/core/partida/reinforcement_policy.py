"""Políticas de refuerzos aplicables al comenzar un turno."""

from __future__ import annotations

from typing import Protocol


class ReinforcementPolicy(Protocol):
    """Contrato para calcular refuerzos adicionales de un jugador."""

    def extra_for(self, player_id: int) -> int:
        """Devuelve los refuerzos adicionales del jugador."""
        ...


class NoExtraReinforcements:
    """Null Object para el modo clásico sin bonificaciones externas."""

    def extra_for(self, _player_id: int) -> int:
        """No agrega unidades al turno.

        Returns:
            Siempre cero.

        """
        return 0


NO_EXTRA_REINFORCEMENTS = NoExtraReinforcements()
