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
from pyteg.core.cartas.tarjeta_de_pais import _to_userid

if TYPE_CHECKING:
    from pyteg.core.cartas.mazo import Mazo
    from pyteg.core.cartas.tarjeta_de_pais import TarjetaDePais
    from pyteg.protocols import IClientProtocol, IJugador


_TURN_KEY_PARTS = 2


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
        # La elegibilidad es por jugador y por conquista, pero la recompensa
        # sólo puede cobrarse una vez por turno.  Guardar el identificador y
        # la clave del turno evita que dos objetos ``Client`` representando la
        # misma sesión vuelvan a habilitar el reclamo.
        self._jugadores_pueden_reclamar: dict[int, tuple[int, int]] = {}
        self._jugadores_reclamaron: dict[int, tuple[int, int]] = {}

    def inicializar_canjes(self, jugadores_userids: list[int]) -> None:
        """Inicializa el contador de canjes para los jugadores.

        Args:
            jugadores_userids: Lista de userids (int) de jugadores.

        """
        self._cant_canjes = dict.fromkeys(jugadores_userids, 0)
        self._jugadores_pueden_reclamar.clear()
        self._jugadores_reclamaron.clear()

    def _clave_turno(self) -> tuple[int, int]:
        """Devuelve una clave estable para el turno actual.

        Returns:
            Tupla ``(ronda, identidad lógica del turno)``.

        """
        clave_turno = getattr(self._turn_manager, "clave_turno", None)
        if callable(clave_turno):
            clave = clave_turno()
            if isinstance(clave, tuple) and len(clave) == _TURN_KEY_PARTS:
                return int(clave[0]), int(clave[1])
        return (
            int(self._turn_manager.num_ronda()),
            int(self._turn_manager.id_turno_actual()),
        )

    def dame_una_tarjeta(self, jugador: IClientProtocol) -> None:
        """Asigna una tarjeta a un jugador. Si tiene 5, fuerza un canje.

        Args:
            jugador: Jugador al que asignar la tarjeta.

        """
        cant_tarjetas_asignadas = self._mazo.cant_tarjetas_asignadas(jugador)
        if cant_tarjetas_asignadas == MAX_CARDS_BEFORE_FORCE_EXCHANGE:
            lista_3_tarjetas = self._mazo.dame_3_tarjetas_para_canje(jugador)
            self.canjear(jugador, lista_3_tarjetas)
        self._mazo.asignar_tarjeta(jugador)

    def cant_canjes(self, jugador: IJugador | int) -> int:
        """Obtiene la cantidad de canjes realizados por un jugador.

        Args:
            jugador: Jugador (con `userid()`) o userid (int).

        Returns:
            Cantidad de canjes realizados.

        """
        userid = _to_userid(jugador)
        return self._cant_canjes.get(userid, 0)

    def canjear(self, jugador: IJugador | int, tarjetas: list[TarjetaDePais]) -> None:
        """Realiza un canje de tarjetas por unidades.

        Args:
            jugador: Jugador (con `userid()`) o userid (int).
            tarjetas: Lista de tarjetas a canjear.

        """
        cant_canjes = self.cant_canjes(jugador)
        turno = self._turn_manager.turno_actual()
        cantidad_a_agregar = EXCHANGE_UNITS.get(
            cant_canjes, EXCHANGE_MULTIPLIER * cant_canjes
        )

        turno.agregar_unidades_generales(cantidad_a_agregar)
        self._mazo.desasignar_tarjetas(tarjetas)
        userid = _to_userid(jugador)
        self._cant_canjes[userid] = self._cant_canjes.get(userid, 0) + 1

    def transferir_tarjetas_al_conquistador(
        self, eliminado: IJugador | int, conquistador: IJugador | int
    ) -> int:
        """Transfiere las tarjetas del eliminado al jugador que lo conquistó.

        Política de eliminación: las tarjetas asignadas no vuelven al mazo ni se
        descartan. Permanecen asignadas y pasan al conquistador. ``Game`` llama
        este método una única vez, al registrar la pérdida del último país.

        Args:
            eliminado: Jugador que perdió su último país.
            conquistador: Jugador que conquistó ese país.

        Returns:
            Cantidad de tarjetas transferidas.

        """
        tarjetas = self._mazo.tarjetas_asignadas(eliminado)
        for tarjeta in tarjetas:
            tarjeta.asignar(conquistador)

        self.eliminar_jugador(eliminado)
        return len(tarjetas)

    def eliminar_jugador(self, jugador: IJugador | int) -> None:
        """Limpia el estado de canjes y reclamos de un jugador eliminado."""
        userid = _to_userid(jugador)
        self._cant_canjes.pop(userid, None)
        self._jugadores_pueden_reclamar.pop(userid, None)
        self._jugadores_reclamaron.pop(userid, None)

    def marcar_jugador_puede_reclamar(self, jugador: IClientProtocol) -> None:
        """Marca a un jugador como elegible para reclamar tarjeta.

        Args:
            jugador: Jugador a marcar como elegible.

        """
        userid = _to_userid(jugador)
        clave = self._clave_turno()
        # Una segunda conquista durante el mismo turno no genera una segunda
        # tarjeta, aunque el ataque vuelva a marcar al jugador como elegible.
        if self._jugadores_reclamaron.get(userid) == clave:
            return
        self._jugadores_pueden_reclamar[userid] = clave

    def puede_reclamar_tarjeta(self, jugador: IClientProtocol) -> bool:
        """Verifica si un jugador puede reclamar tarjeta.

        Args:
            jugador: Jugador a verificar.

        Returns:
            True si el jugador puede reclamar tarjeta, False en caso contrario.

        """
        userid = _to_userid(jugador)
        clave = self._clave_turno()
        return (
            self._jugadores_pueden_reclamar.get(userid) == clave
            and self._jugadores_reclamaron.get(userid) != clave
        )

    def reclamar_tarjeta_jugador(self, jugador: IClientProtocol) -> None:
        """Remueve al jugador de la lista de elegibles tras reclamar.

        Args:
            jugador: Jugador que reclamó la tarjeta.

        """
        userid = _to_userid(jugador)
        clave = self._clave_turno()
        if self._jugadores_pueden_reclamar.get(userid) == clave:
            self._jugadores_reclamaron[userid] = clave
            self._jugadores_pueden_reclamar.pop(userid, None)

    def limpiar_elegibilidad_reclamar(self) -> None:
        """Limpia la elegibilidad de reclamar tarjetas (al finalizar turno)."""
        self._jugadores_pueden_reclamar.clear()

    def mazo(self) -> Mazo:
        """Obtiene el mazo de tarjetas.

        Returns:
            El mazo de tarjetas.

        """
        return self._mazo
