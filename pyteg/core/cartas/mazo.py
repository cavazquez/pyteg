"""Módulo para manejar el mazo de tarjetas del juego."""

from __future__ import annotations

from collections import Counter
from itertools import cycle
from random import sample
from typing import TYPE_CHECKING

from pyteg.config import CARDS_FOR_EXCHANGE, MIN_CARDS_SAME_SYMBOL_FOR_EXCHANGE
from pyteg.core.cartas.tarjeta_de_pais import TarjetaDePais, _to_userid

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping, Sequence

    from pyteg.protocols import IJugador


class Mazo:
    """Representa el mazo de tarjetas de países."""

    def __init__(
        self,
        paises: list[str],
        simbolos: list[str],
        *,
        simbolos_por_pais: Mapping[str, str] | None = None,
        cartas_extra: Sequence[tuple[str, str, str, str | None]] = (),
    ) -> None:
        """Inicializa el mazo con tarjetas de países.

        Args:
            paises: Lista de nombres de países.
            simbolos: Lista de símbolos para las tarjetas.
            simbolos_por_pais: Símbolo explícito de cada país, si el tema lo
                declara.
            cartas_extra: Cartas adicionales como ``(id, símbolo, tipo,
                continente)``.

        """
        tarjetas = self.build_tarjetas_de_paises(
            paises,
            simbolos,
            simbolos_por_pais=simbolos_por_pais,
        )
        self._paises = list(paises)
        self._simbolos = list(simbolos)
        self._simbolos_por_pais = dict(simbolos_por_pais or {})
        self._cartas_extra = list(cartas_extra)
        self.mazo: dict[str, TarjetaDePais] = {}
        for tarjeta in tarjetas:
            self.mazo[tarjeta.pais] = tarjeta
        for card_id, simbolo, tipo, continente in self._cartas_extra:
            self.mazo[card_id] = TarjetaDePais(
                card_id,
                simbolo,
                tipo=tipo,
                continente=continente,
            )

    def reiniciar(self) -> None:
        """Recrea las tarjetas para una revancha sin estado heredado."""
        self.mazo = {
            tarjeta.pais: tarjeta
            for tarjeta in self.build_tarjetas_de_paises(
                self._paises,
                self._simbolos,
                simbolos_por_pais=self._simbolos_por_pais or None,
            )
        }
        for card_id, simbolo, tipo, continente in self._cartas_extra:
            self.mazo[card_id] = TarjetaDePais(
                card_id,
                simbolo,
                tipo=tipo,
                continente=continente,
            )

    def build_tarjetas_de_paises(
        self,
        paises: list[str],
        simbolos: list[str],
        *,
        simbolos_por_pais: Mapping[str, str] | None = None,
    ) -> list[TarjetaDePais]:
        """Construye tarjetas de países con símbolos cíclicos.

        Args:
            paises: Lista de nombres de países.
            simbolos: Lista de símbolos (se repiten cíclicamente).
            simbolos_por_pais: Símbolo explícito por país, opcional.

        Returns:
            Lista de tarjetas de países.

        Raises:
            ValueError: Si falta el símbolo explícito de algún país.

        """
        if simbolos_por_pais is not None:
            missing = [pais for pais in paises if pais not in simbolos_por_pais]
            if missing:
                msg = f"Faltan símbolos explícitos para: {', '.join(missing)}"
                raise ValueError(msg)
            return [TarjetaDePais(pais, simbolos_por_pais[pais]) for pais in paises]
        return list(map(TarjetaDePais, paises, cycle(simbolos)))

    def cantidad_tarjetas(self) -> int:
        """Obtiene la cantidad total de tarjetas.

        Returns:
            Cantidad total de tarjetas.

        """
        return len(self.tarjetas())

    def cantidad_tarjetas_usadas(self) -> int:
        """Obtiene la cantidad de tarjetas usadas.

        Returns:
            Cantidad de tarjetas usadas.

        """
        return sum(1 for tarjeta in self.tarjetas() if tarjeta.fue_usada() is True)

    def cantidad_tarjetas_asignadas(self) -> int:
        """Obtiene la cantidad de tarjetas asignadas.

        Returns:
            Cantidad de tarjetas asignadas.

        """
        return sum(1 for tarjeta in self.tarjetas() if tarjeta.asignada() is True)

    def tarjetas(self) -> list[TarjetaDePais]:
        """Obtiene todas las tarjetas del mazo.

        Returns:
            Lista de todas las tarjetas.

        """
        return list(self.mazo.values())

    def tarjetas_asignadas(self, jugador: IJugador | int) -> list[TarjetaDePais]:
        """Obtiene las tarjetas asignadas a un jugador.

        Args:
            jugador: Jugador (con `userid()`) o `userid` (int).

        Returns:
            Lista de tarjetas asignadas al jugador.

        """
        userid = _to_userid(jugador)
        return [tarjeta for tarjeta in self.tarjetas() if tarjeta.jugador() == userid]

    def tarjetas_por_tipo(self, tipo: str) -> list[TarjetaDePais]:
        """Devuelve las cartas del mazo que pertenecen a un tipo.

        Returns:
            Cartas cuyo tipo coincide con ``tipo``.

        """
        return [tarjeta for tarjeta in self.tarjetas() if tarjeta.tipo == tipo]

    def cant_tarjetas_asignadas(
        self, jugador: IJugador | int, *, tipo: str | None = None
    ) -> int:
        """Obtiene la cantidad de tarjetas asignadas a un jugador.

        Args:
            jugador: Jugador (con `userid()`) o `userid` (int).
            tipo: Filtra por tipo de tarjeta cuando se especifica.

        Returns:
            Cantidad de tarjetas asignadas al jugador.

        """
        return sum(
            1
            for tarjeta in self.tarjetas_asignadas(jugador)
            if tipo is None or tarjeta.tipo == tipo
        )

    def simbolo_asignado_almenos_3_tarjetas(
        self, jugador: IJugador | int
    ) -> list[tuple[str, int]]:
        """Obtiene el símbolo más común de las tarjetas del jugador.

        Args:
            jugador: Jugador (con `userid()`) o `userid` (int).

        Returns:
            Lista con tupla (símbolo, cantidad) del símbolo más común.

        """
        return Counter(
            tarjeta.simbolo
            for tarjeta in self.tarjetas_asignadas(jugador)
            if tarjeta.tipo == "pais"
        ).most_common(1)

    def dame_3_tarjetas_para_canje(
        self, jugador: IJugador | int
    ) -> list[TarjetaDePais]:
        """Obtiene 3 tarjetas para canje de un jugador.

        Si tiene 3 o más del mismo símbolo, retorna 3 de ese símbolo.
        Si no, retorna 3 tarjetas con símbolos diferentes.

        Args:
            jugador: Jugador (con `userid()`) o `userid` (int).

        Returns:
            Lista de 3 tarjetas para canje.

        """
        simbolos = self.simbolo_asignado_almenos_3_tarjetas(jugador)
        if not simbolos:
            return []
        simbolo = simbolos[0]
        if simbolo[1] >= MIN_CARDS_SAME_SYMBOL_FOR_EXCHANGE:
            return [
                tarjeta
                for tarjeta in self.tarjetas_asignadas(jugador)
                if tarjeta.tipo == "pais" and tarjeta.simbolo == simbolo[0]
            ][:CARDS_FOR_EXCHANGE]
        acum: set[str] = set()
        res: list[TarjetaDePais] = []
        for tarjeta in self.tarjetas_asignadas(jugador):
            if tarjeta.tipo != "pais":
                continue
            simbolo_tarjeta = tarjeta.simbolo
            if simbolo_tarjeta not in acum:
                res.append(tarjeta)
                acum.add(simbolo_tarjeta)
        return res[:3]

    def dame_simbolos(self) -> set[str]:
        """Obtiene todos los símbolos únicos del mazo.

        Returns:
            Conjunto de símbolos únicos.

        """
        return {tarjeta.simbolo for tarjeta in self.tarjetas()}

    def liberar_tarjetas_usadas(self) -> None:
        """Libera las tarjetas usadas que no están asignadas."""
        for tarjeta in self.tarjetas():
            if tarjeta.fue_usada() and not tarjeta.asignada():
                tarjeta.desusar()

    def asignar_tarjeta(
        self,
        jugador: IJugador | int,
        mezclar: Callable[[list[TarjetaDePais], int], list[TarjetaDePais]] = sample,
        *,
        tipo: str = "pais",
        continente: str | None = None,
    ) -> TarjetaDePais | None:
        """Asigna una tarjeta disponible a un jugador.

        Args:
            jugador: Jugador (con `userid()`) o `userid` (int).
            mezclar: Función para mezclar las tarjetas (por defecto sample).
            tipo: Tipo de tarjeta a asignar.
            continente: Limita la asignación a un continente concreto.

        Returns:
            La tarjeta asignada o None si no hay tarjetas disponibles.

        """
        disponibles = [
            tarjeta
            for tarjeta in self.tarjetas_por_tipo(tipo)
            if continente is None or tarjeta.continente == continente
        ]
        if disponibles and all(tarjeta.fue_usada() for tarjeta in disponibles):
            self.liberar_tarjetas_usadas()
            disponibles = [
                tarjeta for tarjeta in disponibles if tarjeta.se_puede_asignar()
            ]
        tarjetas = mezclar(disponibles, len(disponibles))
        for tarjeta in tarjetas:
            if tarjeta.se_puede_asignar():
                tarjeta.asignar(jugador)
                return tarjeta
        return None

    def desasignar_tarjetas(self, tarjetas: list[TarjetaDePais]) -> None:
        """Desasigna una lista de tarjetas.

        Args:
            tarjetas: Lista de tarjetas a desasignar.

        """
        for tarjeta in tarjetas:
            tarjeta.desasignar()

    def __str__(self) -> str:
        """Retorna representación en string del mazo.

        Returns:
            String con los nombres de los países del mazo.

        """
        res = ""
        for elem in self.mazo:
            res = res + elem + "\n"
        return res
