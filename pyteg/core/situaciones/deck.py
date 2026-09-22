"""Mazo de cartas de situación con aleatoriedad inyectable."""

from __future__ import annotations

import random
from typing import TYPE_CHECKING

from pyteg.core.situaciones.model import NoSituationCard, SituationCard

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable


class SituationDeck:
    """Mazo independiente del mapa.

    La producción usa ``SystemRandom``. Las pruebas y simulaciones pueden pasar
    ``random.Random(seed)`` sin modificar las reglas del dominio.
    """

    def __init__(
        self,
        cards: Iterable[SituationCard] = (),
        *,
        rng: random.Random | random.SystemRandom | None = None,
    ) -> None:
        """Inicializa y mezcla el mazo.

        Args:
            cards: Cartas que componen el mazo.
            rng: Fuente de aleatoriedad del mazo.

        """
        self._cards = list(cards)
        self._discard: list[SituationCard] = []
        self._rng = rng if rng is not None else random.SystemRandom()
        self._shuffle(self._cards)

    def _shuffle(self, cards: list[SituationCard]) -> None:
        self._rng.shuffle(cards)

    def draw(
        self,
        *,
        predicate: Callable[[SituationCard], bool] | None = None,
    ) -> SituationCard:
        """Roba una carta válida y descarta las que no aplican.

        Returns:
            Carta robada o ``NoSituationCard`` si no queda una válida.

        """
        if predicate is None:

            def accept(_card: SituationCard) -> bool:
                return True

            predicate = accept

        total = len(self._cards) + len(self._discard)
        for _ in range(total):
            if not self._cards:
                self._cards = self._discard
                self._discard = []
                self._shuffle(self._cards)
            if not self._cards:
                return NoSituationCard()
            card = self._cards.pop()
            self._discard.append(card)
            if predicate(card):
                return card
        return NoSituationCard()

    def remaining(self) -> int:
        """Cantidad de cartas que aún no fueron robadas.

        Returns:
            Cantidad de cartas restantes.

        """
        return len(self._cards)

    def discarded(self) -> int:
        """Cantidad de cartas del descarte.

        Returns:
            Cantidad de cartas descartadas.

        """
        return len(self._discard)

    def total(self) -> int:
        """Cantidad total de cartas del mazo.

        Returns:
            Cantidad entre mazo y descarte.

        """
        return len(self._cards) + len(self._discard)
