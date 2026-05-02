"""Módulo para gestión de tarjetas y canjes del juego.

Este módulo encapsula la lógica de gestión de tarjetas y canjes,
separando esta responsabilidad del Game principal.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pyteg.config import (
    EXCHANGE_MULTIPLIER,
    EXCHANGE_UNITS,
    MAX_CARDS_BEFORE_FORCE_EXCHANGE,
)

if TYPE_CHECKING:
    from pyteg.core.cartas.mazo import Mazo
    from pyteg.core.cartas.tarjeta_de_pais import TarjetaDePais
    from pyteg.server.conexion.cliente import Client


class CardManager:
    """Gestiona las tarjetas y canjes del juego.

    Esta clase se encarga de toda la lógica relacionada con la gestión
    de tarjetas, incluyendo asignación, canjes y elegibilidad para reclamar.
    """

    def __init__(self, mazo: Mazo, turn_manager: Any) -> None:
        """Inicializa el gestor de tarjetas.

        Args:
            mazo: Instancia del mazo de tarjetas.
            turn_manager: Instancia del gestor de turnos.

        """
        self._mazo = mazo
        self._turn_manager = turn_manager
        self._cant_canjes: dict[int, int] = {}
        self._jugadores_pueden_reclamar: set[Client] = set()

    def inicializar_canjes(self, jugadores_userids: list[int]) -> None:
        """Inicializa el contador de canjes para los jugadores.

        Args:
            jugadores_userids: Lista de userids (int) de jugadores.

        """
        self._cant_canjes = dict.fromkeys(jugadores_userids, 0)

    def dame_una_tarjeta(self, jugador: Client) -> None:
        """Asigna una tarjeta a un jugador. Si tiene 5, fuerza un canje.

        Args:
            jugador: Jugador al que asignar la tarjeta.

        """
        cant_tarjetas_asignadas = self._mazo.cant_tarjetas_asignadas(jugador)
        if cant_tarjetas_asignadas == MAX_CARDS_BEFORE_FORCE_EXCHANGE:
            lista_3_tarjetas = self._mazo.dame_3_tarjetas_para_canje(jugador)
            self.canjear(jugador, lista_3_tarjetas)
        self._mazo.asignar_tarjeta(jugador)

    def cant_canjes(self, jugador: Client | int) -> int:
        """Obtiene la cantidad de canjes realizados por un jugador.

        Args:
            jugador: Cliente o userid (int) del jugador.

        Returns:
            Cantidad de canjes realizados.

        """
        userid = self._jugador_a_userid(jugador)
        return self._cant_canjes.get(userid, 0)

    def canjear(self, jugador: Client | int, tarjetas: list[TarjetaDePais]) -> None:
        """Realiza un canje de tarjetas por unidades.

        Args:
            jugador: Cliente o userid (int) del jugador.
            tarjetas: Lista de tarjetas a canjear.

        """
        cant_canjes = self.cant_canjes(jugador)
        turno = self._turn_manager.turno_actual()
        cantidad_a_agregar = EXCHANGE_UNITS.get(
            cant_canjes, EXCHANGE_MULTIPLIER * cant_canjes
        )

        turno.agregar_unidades_generales(cantidad_a_agregar)
        self._mazo.desasignar_tarjetas(tarjetas)
        userid = self._jugador_a_userid(jugador)
        self._cant_canjes[userid] = self._cant_canjes.get(userid, 0) + 1

    @staticmethod
    def _jugador_a_userid(jugador: Client | int) -> int:
        """Normaliza la entrada a un userid (int).

        Acepta un objeto cliente con método `userid()` o directamente el int.

        Args:
            jugador: Cliente con `userid()` o el userid directo.

        Returns:
            userid (int) del jugador.

        """
        if hasattr(jugador, "userid"):
            return int(jugador.userid())
        return int(jugador)

    def marcar_jugador_puede_reclamar(self, jugador: Client) -> None:
        """Marca a un jugador como elegible para reclamar tarjeta.

        Args:
            jugador: Jugador a marcar como elegible.

        """
        self._jugadores_pueden_reclamar.add(jugador)

    def puede_reclamar_tarjeta(self, jugador: Client) -> bool:
        """Verifica si un jugador puede reclamar tarjeta.

        Args:
            jugador: Jugador a verificar.

        Returns:
            True si el jugador puede reclamar tarjeta, False en caso contrario.

        """
        return jugador in self._jugadores_pueden_reclamar

    def reclamar_tarjeta_jugador(self, jugador: Client) -> None:
        """Remueve al jugador de la lista de elegibles tras reclamar.

        Args:
            jugador: Jugador que reclamó la tarjeta.

        """
        self._jugadores_pueden_reclamar.discard(jugador)

    def limpiar_elegibilidad_reclamar(self) -> None:
        """Limpia la elegibilidad de reclamar tarjetas (al finalizar turno)."""
        self._jugadores_pueden_reclamar.clear()

    def mazo(self) -> Mazo:
        """Obtiene el mazo de tarjetas.

        Returns:
            El mazo de tarjetas.

        """
        return self._mazo
