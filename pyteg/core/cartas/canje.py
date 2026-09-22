"""Reglas de equivalencia para canjes de cartas.

La validación vive fuera del servidor para que el contrato sea reutilizable por
el cliente, el simulador y futuras interfaces. El servidor sigue siendo la
autoridad que decide si las cartas seleccionadas pertenecen al jugador.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

    from pyteg.core.cartas.tarjeta_de_pais import TarjetaDePais

WILDCARD_SYMBOL = "Soldado"
SUPER_CARD_SYMBOL = "Supertarjeta"


def _symbol_tokens(symbol: str) -> tuple[str, ...]:
    """Descompone una representación de uno o varios símbolos.

    Returns:
        Símbolos normalizados.

    """
    if symbol == SUPER_CARD_SYMBOL:
        return (SUPER_CARD_SYMBOL,)
    normalized = symbol.replace("/", "+").replace(",", "+")
    return tuple(token.strip() for token in normalized.split("+") if token.strip())


def es_supertarjeta(tarjeta: TarjetaDePais) -> bool:
    """Indica si una tarjeta equivale por sí sola a un canje.

    Returns:
        ``True`` para una supertarjeta.

    """
    if tarjeta.tipo == "especial" or tarjeta.simbolo == SUPER_CARD_SYMBOL:
        return True
    tokens = _symbol_tokens(tarjeta.simbolo)
    return set(tokens) == {"Avion", "Barco", "Tanque"}


def _variables_tarjeta(
    tarjeta: TarjetaDePais,
    equivalencias: Mapping[str, Sequence[str]],
) -> tuple[str, ...] | None:
    """Obtiene las variables que aporta una tarjeta.

    ``None`` representa una tarjeta de continente completa, que equivale a un
    canje sin combinarla con cartas de país.

    Returns:
        Variables equivalentes, o ``None`` para un canje completo.

    """
    if tarjeta.tipo == "continente":
        if tarjeta.continente is None or tarjeta.continente not in equivalencias:
            return ()
        symbols = tuple(equivalencias[tarjeta.continente])
        return symbols or None
    if tarjeta.tipo != "pais":
        return ()
    if es_supertarjeta(tarjeta):
        return (SUPER_CARD_SYMBOL,)
    return _symbol_tokens(tarjeta.simbolo)


def seleccion_valida(  # noqa: PLR0911
    tarjetas: Sequence[TarjetaDePais],
    *,
    equivalencias: Mapping[str, Sequence[str]] | None = None,
    cantidad_variables: int = 3,
) -> bool:
    """Valida una selección de cartas para un único canje.

    Las cartas de país forman tres variables homogéneas o distintas; ``Soldado``
    es comodín. Las cartas de continente aportan las variables declaradas en el
    perfil y las de los tres continentes grandes completan un canje por sí solas.

    Returns:
        ``True`` cuando la selección representa exactamente un canje.

    """
    if not tarjetas or cantidad_variables <= 0:
        return False
    equivalencias = equivalencias or {}
    if len(tarjetas) == 1 and es_supertarjeta(tarjetas[0]):
        return True

    variables: list[str] = []
    for tarjeta in tarjetas:
        tokens = _variables_tarjeta(tarjeta, equivalencias)
        if tokens is None:
            return len(tarjetas) == 1
        if not tokens:
            return False
        if SUPER_CARD_SYMBOL in tokens:
            return False
        variables.extend(tokens)

    if len(variables) != cantidad_variables:
        return False
    fixed = [symbol for symbol in variables if symbol != WILDCARD_SYMBOL]
    distinct = len(fixed) == len(set(fixed))
    same = len(set(fixed)) <= 1
    return distinct or same


__all__ = [
    "SUPER_CARD_SYMBOL",
    "WILDCARD_SYMBOL",
    "es_supertarjeta",
    "seleccion_valida",
]
