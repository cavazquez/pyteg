"""Estrategias que implementan los efectos de las cartas de situación."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

from pyteg.exceptions import InvalidActionError

if TYPE_CHECKING:
    from pyteg.core.situaciones.model import SituationContext, SituationState


class DiceSource(Protocol):
    """Fuente mínima de un dado para efectos que necesitan azar."""

    def roll(self) -> int:
        """Devuelve un resultado de dado entre uno y seis."""
        ...


class SituationEffect:
    """Estrategia base con comportamiento neutro.

    Los métodos tienen valores seguros para que el runtime pueda componer
    políticas pequeñas sin comprobar si una carta implementa cada capacidad.
    ``NoSituationEffect`` hace explícito el Null Object usado por defecto.
    """

    effect_id = "none"

    def is_applicable(self, _context: SituationContext) -> bool:
        """Indica si la carta puede usarse con los jugadores actuales.

        Returns:
            ``True`` para la política neutra.

        """
        return True

    def begin_round(
        self,
        _context: SituationContext,
        state: SituationState,
        dice_source: DiceSource,
    ) -> None:
        """Inicializa el estado de la carta para una ronda."""

    def attack_dice(self, base: int, _context: SituationContext) -> int:
        """Modifica la cantidad base de dados del atacante.

        Returns:
            La cantidad base sin cambios.

        """
        return base

    def defense_dice(self, base: int, _context: SituationContext) -> int:
        """Modifica la cantidad base de dados del defensor.

        Returns:
            La cantidad base sin cambios.

        """
        return base

    def validate_attack(
        self,
        origin: str,
        destination: str,
        _context: SituationContext,
    ) -> None:
        """Valida restricciones de frontera para un ataque."""

    def validate_action(
        self,
        _player_id: int,
        _action: str,
        _player_color: str | None,
        _context: SituationContext,
    ) -> None:
        """Valida restricciones de acciones para un jugador."""

    def extra_reinforcements(
        self,
        _player_id: int,
        _context: SituationContext,
    ) -> int:
        """Devuelve refuerzos adicionales para el jugador.

        Returns:
            Cero cuando no hay una carta de refuerzos extras.

        """
        return 0

    def can_claim_country_card(
        self,
        player_id: int,
        _context: SituationContext,
        state: SituationState,
    ) -> bool:
        """Indica si el jugador puede reclamar la tarjeta de país.

        Returns:
            ``True`` cuando el jugador no está bloqueado por Crisis.

        """
        return int(player_id) not in state.blocked_card_claims


class NoSituationEffect(SituationEffect):
    """Null Object: mantiene todas las reglas base sin una carta activa."""

    effect_id = "none"


class ClassicCombatEffect(NoSituationEffect):
    """Carta visible que conserva el combate clásico."""

    effect_id = "classic_combat"


class SnowEffect(SituationEffect):
    """El defensor recibe un dado adicional, con máximo de cuatro."""

    effect_id = "snow"

    def defense_dice(self, base: int, _context: SituationContext) -> int:
        """Añade un dado al defensor, sin superar cuatro.

        Returns:
            Cantidad de dados del defensor.

        """
        return min(base + 1, 4)


class TailwindEffect(SituationEffect):
    """El atacante recibe un dado adicional, con máximo de cuatro."""

    effect_id = "tailwind"

    def attack_dice(self, base: int, _context: SituationContext) -> int:
        """Añade un dado al atacante, sin superar cuatro.

        Returns:
            Cantidad de dados del atacante.

        """
        return min(base + 1, 4)


class CrisisEffect(SituationEffect):
    """El resultado mínimo de dados pierde el reclamo de tarjeta de país."""

    effect_id = "crisis"

    def begin_round(
        self,
        context: SituationContext,
        state: SituationState,
        dice_source: DiceSource,
    ) -> None:
        """Tira un dado por jugador y registra los resultados mínimos."""
        if not context.player_ids:
            return
        state.crisis_rolls = {
            int(player_id): dice_source.roll() for player_id in context.player_ids
        }
        lowest = min(state.crisis_rolls.values())
        state.blocked_card_claims = {
            player_id
            for player_id, result in state.crisis_rolls.items()
            if result == lowest
        }


class ExtraReinforcementsEffect(SituationEffect):
    """Añade la mitad entera de los países ocupados al turno."""

    effect_id = "extra_reinforcements"

    def extra_reinforcements(
        self,
        player_id: int,
        context: SituationContext,
    ) -> int:
        """Calcula la mitad entera de los países ocupados.

        Returns:
            Refuerzos adicionales del jugador.

        """
        return context.countries_owned_by(player_id) // 2


class OpenBordersEffect(SituationEffect):
    """Sólo permite ataques entre continentes diferentes."""

    effect_id = "open_borders"

    def validate_attack(
        self,
        origin: str,
        destination: str,
        context: SituationContext,
    ) -> None:
        """Rechaza ataques entre países del mismo continente.

        Raises:
            InvalidActionError: Si los países están en el mismo continente.

        """
        if context.mapa.continente(origin) == context.mapa.continente(destination):
            msg = "Con fronteras abiertas sólo puedes atacar entre continentes"
            raise InvalidActionError(msg)


class ClosedBordersEffect(SituationEffect):
    """Sólo permite ataques dentro del mismo continente."""

    effect_id = "closed_borders"

    def validate_attack(
        self,
        origin: str,
        destination: str,
        context: SituationContext,
    ) -> None:
        """Rechaza ataques entre continentes distintos.

        Raises:
            InvalidActionError: Si los países están en continentes distintos.

        """
        if context.mapa.continente(origin) != context.mapa.continente(destination):
            msg = "Con fronteras cerradas sólo puedes atacar dentro del continente"
            raise InvalidActionError(msg)


class RestEffect(SituationEffect):
    """El color indicado sólo puede colocar refuerzos."""

    effect_id = "rest"

    def __init__(self, color_key: str) -> None:
        """Crea una carta de descanso para un color RGB hexadecimal."""
        self.color_key = color_key.lower()

    def is_applicable(self, context: SituationContext) -> bool:
        """Indica si el color está presente entre los jugadores.

        Returns:
            ``True`` si al menos un jugador usa el color.

        """
        return self.color_key in context.color_keys()

    def validate_action(
        self,
        player_id: int,  # noqa: ARG002
        action: str,
        player_color: str | None,
        _context: SituationContext,
    ) -> None:
        """Bloquea ataque y movimiento del jugador en descanso.

        Raises:
            InvalidActionError: Si el jugador intenta atacar o reagrupar.

        """
        if (
            isinstance(player_color, str)
            and player_color.lower() == self.color_key
            and action in {"atacar", "mover_unidad"}
        ):
            msg = "El jugador está en descanso y sólo puede colocar refuerzos"
            raise InvalidActionError(msg)
