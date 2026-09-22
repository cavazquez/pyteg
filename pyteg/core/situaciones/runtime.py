"""Estado de ejecución de las cartas de situación."""

from __future__ import annotations

import random
from typing import TYPE_CHECKING

from pyteg.core.situaciones.catalog import (
    card_is_applicable,
    create_effect,
)
from pyteg.core.situaciones.deck import SituationDeck
from pyteg.core.situaciones.effects import (
    DiceSource,
    NoSituationEffect,
    SituationEffect,
)
from pyteg.core.situaciones.model import (
    NoSituationCard,
    SituationCard,
    SituationContext,
    SituationState,
)

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

    from pyteg.protocols.mapa import IMapProtocol


class _SystemDice:
    """Fuente de dados del servidor cuando no se inyecta una de pruebas."""

    def roll(self) -> int:
        return random.SystemRandom().randint(1, 6)


class _RandomDice:
    """Adaptador de ``random.Random`` al protocolo de dados."""

    def __init__(self, rng: random.Random | random.SystemRandom) -> None:
        """Inicializa el adaptador con una fuente inyectada."""
        self._rng = rng

    def roll(self) -> int:
        """Devuelve un dado reproducible para tests y simulaciones.

        Returns:
            Resultado entre uno y seis.

        """
        return self._rng.randint(1, 6)


class SituationRuntime:
    """Coordina el mazo y delega las políticas de la carta activa."""

    def __init__(
        self,
        mapa: IMapProtocol,
        deck: SituationDeck | None = None,
        *,
        dice_source: DiceSource | None = None,
        dice_rng: random.Random | random.SystemRandom | None = None,
    ) -> None:
        """Inicializa el runtime con mapa, mazo y fuentes inyectables.

        Args:
            mapa: Mapa cuyos países se consultan para los efectos.
            deck: Mazo de la partida; ``None`` instala el mazo nulo.
            dice_source: Fuente de dados para cartas como Crisis.
            dice_rng: Fuente aleatoria adaptable para dados reproducibles.

        """
        self._mapa = mapa
        self._deck = deck if deck is not None else SituationDeck()
        self._dice_source = (
            dice_source
            if dice_source is not None
            else _RandomDice(dice_rng)
            if dice_rng is not None
            else _SystemDice()
        )
        self._active_card: SituationCard = NoSituationCard()
        self._active_effect: SituationEffect = NoSituationEffect()
        self._state = SituationState()
        self._round_number = 1
        self._rounds_started: set[int] = set()
        self._context = SituationContext(mapa)

    @classmethod
    def none(cls, mapa: IMapProtocol) -> SituationRuntime:
        """Crea un runtime con Null Object y sin cartas.

        Returns:
            Runtime que conserva las reglas base.

        """
        return cls(mapa)

    def reset(self) -> None:
        """Restablece el estado temporal antes de una partida nueva."""
        self._active_card = NoSituationCard()
        self._active_effect = NoSituationEffect()
        self._state = SituationState()
        self._round_number = 1
        self._rounds_started.clear()

    def begin_round(
        self,
        round_number: int,
        player_ids: Sequence[int],
        player_colors: Mapping[int, str | None],
    ) -> SituationCard:
        """Revela una única carta para una ronda.

        La clave de ronda hace la operación idempotente frente a reintentos y
        reconexiones. La carta se revela antes de preparar el primer turno.

        Returns:
            Carta activa de la ronda.

        """
        round_number = int(round_number)
        if round_number in self._rounds_started:
            return self._active_card

        context = SituationContext(
            self._mapa,
            round_number,
            tuple(int(player_id) for player_id in player_ids),
            dict(player_colors),
        )
        card = self._deck.draw(predicate=lambda item: card_is_applicable(item, context))
        effect = create_effect(card)
        state = SituationState()
        effect.begin_round(context, state, self._dice_source)
        self._context = context
        self._state = state
        self._active_card = card
        self._active_effect = effect
        self._round_number = round_number
        self._rounds_started.add(round_number)
        return card

    def active_card(self) -> SituationCard:
        """Devuelve la carta pública activa.

        Returns:
            Carta activa o ``NoSituationCard``.

        """
        return self._active_card

    def active_effect(self) -> SituationEffect:
        """Devuelve la estrategia activa para composición interna.

        Returns:
            Estrategia actualmente instalada.

        """
        return self._active_effect

    def public_snapshot(self) -> dict[str, str | int | None]:
        """Serializa sólo el estado público de la carta.

        Returns:
            Payload de carta y ronda para snapshots.

        """
        return self._active_card.to_public_dict(self._round_number)

    def attack_dice(self, base: int) -> int:
        """Aplica la modificación de dados del atacante.

        Returns:
            Cantidad de dados resultante.

        """
        return self._active_effect.attack_dice(base, self._context)

    def defense_dice(self, base: int) -> int:
        """Aplica la modificación de dados del defensor.

        Returns:
            Cantidad de dados resultante.

        """
        return self._active_effect.defense_dice(base, self._context)

    def validate_attack(self, origin: str, destination: str) -> None:
        """Valida la relación de continentes de un ataque."""
        self._active_effect.validate_attack(origin, destination, self._context)

    def validate_action(
        self,
        player_id: int,
        action: str,
        player_color: str | None,
    ) -> None:
        """Valida una acción antes de modificar el dominio."""
        self._active_effect.validate_action(
            int(player_id), action, player_color, self._context
        )

    def extra_reinforcements(self, player_id: int) -> int:
        """Calcula el bonus adicional con el mapa vigente.

        Returns:
            Cantidad de unidades adicionales.

        """
        return max(
            0,
            int(
                self._active_effect.extra_reinforcements(int(player_id), self._context)
            ),
        )

    def extra_for(self, player_id: int) -> int:
        """Adapta el runtime al protocolo de política de refuerzos.

        Returns:
            Refuerzos adicionales de la carta activa.

        """
        return self.extra_reinforcements(player_id)

    def can_claim_country_card(self, player_id: int) -> bool:
        """Comprueba si la carta activa permite el reclamo.

        Returns:
            ``True`` cuando el reclamo está permitido.

        """
        return self._active_effect.can_claim_country_card(
            int(player_id), self._context, self._state
        )

    def crisis_rolls(self) -> dict[int, int]:
        """Copia los resultados de Crisis para auditoría y tests.

        Returns:
            Resultados indexados por jugador.

        """
        return dict(self._state.crisis_rolls)
