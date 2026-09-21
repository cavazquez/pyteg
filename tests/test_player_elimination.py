"""Regresiones para la eliminación de jugadores durante una partida."""

from __future__ import annotations

import unittest
from typing import TYPE_CHECKING, Any, cast
from unittest.mock import patch

from pyteg.core.cartas.mazo import Mazo
from pyteg.exceptions import PlayerEliminatedError
from pyteg.server.juego.game import Game
from pyteg.server.juego.mapa import Mapa
from tests.test_game import FakePlayer

if TYPE_CHECKING:
    from pyteg.server.app import Server


class _GameServer:
    """Servidor mínimo que registra las notificaciones de eliminación."""

    def __init__(self) -> None:
        """Inicializa los registros de eventos enviados por el juego."""
        self.objetivos_secretos = None
        self.color = None
        self.mensajes_sistema: list[str] = []
        self.actualizaciones_colores = 0
        self.finalizada = False
        self.victorias: list[tuple[int, str]] = []

    def enviar_sistema(self, mensaje: str) -> None:
        """Registra un mensaje que debería recibir cada cliente."""
        self.mensajes_sistema.append(mensaje)

    def enviar_colores_asignados(self) -> None:
        """Registra la sincronización de la lista activa de jugadores."""
        self.actualizaciones_colores += 1

    def finalizar_partida(self) -> bool:
        """Cierra la partida una única vez.

        Returns:
            ``True`` al cerrar por primera vez; ``False`` si ya estaba cerrada.

        """
        if self.finalizada:
            return False
        self.finalizada = True
        return True

    def enviar_victoria(self, jugador_id: int, nombre: str) -> None:
        """Registra la victoria difundida por el juego."""
        self.victorias.append((jugador_id, nombre))


def _mapa_de_eliminacion() -> Mapa:
    """Construye un mapa pequeño con un país atacable y una reserva.

    Returns:
        Mapa apto para forzar una eliminación en una sola conquista.

    """

    def build() -> dict[str, list[Any]]:
        return {
            "Origen": [3, "America", None, ["Destino"]],
            "Destino": [1, "America", None, ["Origen"]],
            "Reserva": [1, "America", None, []],
        }

    return Mapa(build)


def _tarjeta_no_nula(tarjeta: object) -> object:
    """Estrecha la tarjeta aleatoria del mazo para el test.

    Returns:
        La misma tarjeta cuando no es ``None``.

    Raises:
        AssertionError: Si el mazo no pudo entregar una tarjeta disponible.

    """
    if tarjeta is None:
        msg = "Se esperaba una tarjeta disponible"
        raise AssertionError(msg)
    return tarjeta


class TestPlayerElimination(unittest.TestCase):
    """Eliminación, orden de turnos, cartas y victoria final."""

    def _crear_partida(
        self, cantidad_jugadores: int = 3
    ) -> tuple[_GameServer, Mapa, Mazo, list[FakePlayer], Game]:
        """Crea una partida con jugadores y umbral imposible de victoria.

        Returns:
            Servidor, mapa, mazo, jugadores y juego preparados para el test.

        """
        server = _GameServer()
        mapa = _mapa_de_eliminacion()
        mazo = Mazo(mapa.paises(), ["Globo", "Galeon", "Cañon"])
        jugadores = [
            FakePlayer(
                jugador_id,
                f"Jugador {jugador_id}",
                cast("Server", server),
            )
            for jugador_id in range(1, cantidad_jugadores + 1)
        ]
        game = Game(
            mapa,
            mazo,
            jugadores,
            cast("Server", server),
            paises_para_victoria=99,
        )
        game.empezar()
        return server, mapa, mazo, jugadores, game

    @staticmethod
    def _preparar_mapa(
        mapa: Mapa,
        atacante_id: int,
        defensor_id: int,
        reserva_id: int,
    ) -> None:
        """Deja al defensor con un único país y al atacante con fuerza suficiente."""
        mapa.asignar_pais(atacante_id, "Origen")
        mapa.set_unidades("Origen", 3)
        mapa.asignar_pais(defensor_id, "Destino")
        mapa.set_unidades("Destino", 1)
        mapa.asignar_pais(reserva_id, "Reserva")
        mapa.set_unidades("Reserva", 1)

    @staticmethod
    def _conquistar_ultimo_pais(game: Game, defensor_id: int) -> dict[str, Any]:
        """Fuerza una conquista que elimina al dueño de ``Destino``.

        Returns:
            El resultado de batalla devuelto por ``Game.atacar``.

        """
        with patch(
            "pyteg.server.juego.game.Batalla.ataquen",
            return_value={"restar": [str(defensor_id)]},
        ):
            return game.atacar("Origen", "Destino", 1)

    def test_eliminacion_retira_turnos_transfiere_cartas_y_es_idempotente(
        self,
    ) -> None:
        """Un eliminado no recibe turnos, cartas ni una segunda transferencia."""
        server, mapa, mazo, jugadores, game = self._crear_partida()
        atacante, defensor, reserva = jugadores
        self._preparar_mapa(
            mapa,
            atacante.userid(),
            defensor.userid(),
            reserva.userid(),
        )
        tarjetas_defensor = [
            _tarjeta_no_nula(mazo.asignar_tarjeta(defensor)) for _ in range(3)
        ]
        game.marcar_jugador_puede_reclamar(defensor)

        resultado = self._conquistar_ultimo_pais(game, defensor.userid())

        self.assertTrue(resultado["conquistado"])
        self.assertTrue(game.jugador_esta_eliminado(defensor))
        self.assertEqual(game.cant_jugadores(), 2)
        self.assertEqual(game.lista_jugadores(), jugadores)
        self.assertEqual(game.lista_jugadores_orden_turno(), [1, 3])
        self.assertEqual([turno.jugador_actual() for turno in game.turnos()], [1, 3])
        self.assertEqual(mazo.cant_tarjetas_asignadas(defensor), 0)
        self.assertEqual(mazo.cant_tarjetas_asignadas(atacante), len(tarjetas_defensor))
        self.assertFalse(game.puede_reclamar_tarjeta(defensor))
        self.assertEqual(
            server.mensajes_sistema,
            ["Jugador 2 fue eliminado de la partida."],
        )
        self.assertEqual(server.actualizaciones_colores, 1)

        with self.assertRaises(PlayerEliminatedError):
            game.dame_una_tarjeta(defensor)

        self.assertFalse(
            game._eliminar_jugador(defensor.userid(), atacante.userid())  # noqa: SLF001
        )
        self.assertEqual(mazo.cant_tarjetas_asignadas(atacante), len(tarjetas_defensor))
        self.assertEqual(
            server.mensajes_sistema, ["Jugador 2 fue eliminado de la partida."]
        )
        self.assertEqual(server.actualizaciones_colores, 1)

        game.finalizar_turno()
        game.finalizar_turno()
        self.assertNotIn(
            defensor.userid(),
            [turno.jugador_actual() for turno in game.turnos()],
        )

    def test_eliminacion_conserva_el_turno_en_inicio_medio_y_final(self) -> None:
        """Retirar cualquier posición del orden no salta al atacante activo."""
        casos = (
            ("inicio", 3, 1, 2, 2, [2, 3], 3),
            ("medio", 1, 2, 3, 0, [1, 3], 3),
            ("final", 1, 3, 2, 0, [1, 2], 2),
        )

        for (
            nombre,
            atacante_id,
            defensor_id,
            reserva_id,
            avances,
            orden,
            siguiente,
        ) in casos:
            with self.subTest(posicion=nombre):
                _, mapa, _, jugadores, game = self._crear_partida()
                atacante = jugadores[atacante_id - 1]
                self._preparar_mapa(mapa, atacante_id, defensor_id, reserva_id)
                for _ in range(avances):
                    game.finalizar_turno()

                self.assertEqual(
                    game.turno_actual().jugador_actual(), atacante.userid()
                )
                self._conquistar_ultimo_pais(game, defensor_id)

                self.assertEqual(game.lista_jugadores_orden_turno(), orden)
                self.assertEqual(
                    game.turno_actual().jugador_actual(), atacante.userid()
                )

                game.finalizar_turno()
                self.assertEqual(game.turno_actual().jugador_actual(), siguiente)
                self.assertNotIn(
                    defensor_id,
                    [turno.jugador_actual() for turno in game.turnos()],
                )

    def test_ultimo_superviviente_finaliza_aunque_el_umbral_no_se_cumpla(self) -> None:
        """El último jugador activo gana al eliminar al único rival restante."""
        server, mapa, _, jugadores, game = self._crear_partida(cantidad_jugadores=2)
        atacante, defensor = jugadores
        self._preparar_mapa(
            mapa,
            atacante.userid(),
            defensor.userid(),
            atacante.userid(),
        )

        self._conquistar_ultimo_pais(game, defensor.userid())

        self.assertTrue(server.finalizada)
        self.assertFalse(game.empezo())
        self.assertEqual(server.victorias, [(atacante.userid(), atacante.username())])
        self.assertEqual(
            server.mensajes_sistema,
            ["Jugador 2 fue eliminado de la partida."],
        )

        turno_final = game.id_turno_actual()
        game.finalizar_turno()
        self.assertEqual(game.id_turno_actual(), turno_final)


if __name__ == "__main__":
    unittest.main()
