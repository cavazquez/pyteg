"""Tests de tareas del servidor: canjear y lanzar misiles."""

from __future__ import annotations

import unittest
from typing import TYPE_CHECKING, Any, cast
from unittest.mock import MagicMock

from pyteg.core.turnos.turnos import PrimerTurno
from pyteg.server.juego.estado import Estado
from pyteg.server.juego.mapa import Mapa
from pyteg.server.juego.state_validator import ServerStateValidator
from pyteg.server.tasks.cards_missiles.canjear_misil import ServerTaskCanjearMisil
from pyteg.server.tasks.cards_missiles.lanzar_misil import ServerTaskLanzarMisil

if TYPE_CHECKING:
    from pyteg.protocols import IClientProtocol
    from pyteg.server.tasks.types import CanjearMisilTaskData, LanzarMisilTaskData


def _mapa_dos_paises() -> Mapa:
    """Mapa mínimo Argentina-Brasil para tests de misiles.

    Returns:
        Instancia de `Mapa` con dos países adyacentes.

    """

    def build() -> dict[str, list[int | str | list[str] | None]]:
        return {
            "Argentina": [6, "America", 1, ["Brasil"]],
            "Brasil": [4, "America", 2, ["Argentina"]],
        }

    return Mapa(build)


class _FakeClient:
    """Cliente mínimo conforme a lo que usan las tareas de misil."""

    def __init__(self, user_id: int, server: _FakeServer) -> None:
        self._user_id = user_id
        self._name = f"Jugador{user_id}"
        self.server = server
        self.transmisor = MagicMock()

    def userid(self) -> int:
        return self._user_id

    def username(self) -> str:
        return self._name


class _FakeGame:
    """Juego mínimo: turno del jugador 1."""

    def __init__(self, jugador_id: int) -> None:
        self._turno = PrimerTurno(jugador_id)

    def turno_actual(self) -> PrimerTurno:
        return self._turno


class _FakeServer:
    """Servidor mínimo para `GameContext` y validación de estado."""

    def __init__(self, mapa: Mapa, *, misiles: bool = True) -> None:
        self.mapa = mapa
        self.game = _FakeGame(1)
        self.estado = Estado()
        self.estado.esperar_jugadores()
        self.estado.empezar_partida()
        self._misiles = misiles
        self.misiles_agregados: list[tuple[str, int]] = []
        self.resultados_misil: list[dict[str, Any]] = []
        self.sent_map = False

    def set_misiles_habilitados(self, *, activados: bool) -> None:
        self._misiles = activados

    def misiles_habilitados(self) -> bool:
        return self._misiles

    def enviar_misil_agregado(self, pais: str, cantidad: int) -> None:
        self.misiles_agregados.append((pais, cantidad))

    def enviar_resultado_misil(self, data: dict[str, Any]) -> None:
        self.resultados_misil.append(data)

    def enviar_mapa(self) -> None:
        self.sent_map = True


class TestServerTaskCanjearMisil(unittest.TestCase):
    """Canje de unidades por misil en un país propio."""

    def setUp(self) -> None:
        """Cliente 1 dueño de Argentina con unidades suficientes."""
        self.mapa = _mapa_dos_paises()
        self.server = _FakeServer(self.mapa)
        self.client = _FakeClient(1, self.server)

    def _run_canjear(self, payload: CanjearMisilTaskData) -> None:
        task = ServerTaskCanjearMisil(payload)
        task._validator = ServerStateValidator()  # noqa: SLF001
        task.run(cast("IClientProtocol", self.client))

    def test_canje_exitoso_resta_unidades_y_agrega_misil(self) -> None:
        """Un canje válido consume 6 unidades y suma un misil."""
        unidades_antes = self.mapa.cantidad_unidades("Argentina")

        self._run_canjear({"mensaje": "canjear_misil", "pais": "Argentina"})

        self.assertEqual(
            self.mapa.cantidad_unidades("Argentina"),
            unidades_antes - 6,
        )
        self.assertEqual(self.mapa.cantidad_misiles("Argentina"), 1)
        self.client.transmisor.enviar_sistema.assert_called_once()
        self.assertTrue(self.server.sent_map)

    def test_canje_rechazado_si_misiles_desactivados(self) -> None:
        """Sin misiles habilitados, se envía error al chat."""
        self.server.set_misiles_habilitados(activados=False)

        self._run_canjear({"mensaje": "canjear_misil", "pais": "Argentina"})

        self.client.transmisor.enviar_error_chat.assert_called_once()
        self.assertEqual(self.mapa.cantidad_misiles("Argentina"), 0)


class TestServerTaskLanzarMisil(unittest.TestCase):
    """Lanzamiento de misil entre países."""

    def setUp(self) -> None:
        """Argentina (j1) con misil; Brasil pertenece al jugador 2."""
        self.mapa = _mapa_dos_paises()
        self.mapa.agregar_misil("Argentina")
        self.server = _FakeServer(self.mapa)
        self.client = _FakeClient(1, self.server)

    def _run_lanzar(self, payload: LanzarMisilTaskData) -> None:
        task = ServerTaskLanzarMisil(payload)
        task._validator = ServerStateValidator()  # noqa: SLF001
        task.run(cast("IClientProtocol", self.client))

    def test_lanzamiento_exitoso_aplica_dano_y_notifica(self) -> None:
        """Un misil adyacente daña Brasil y consume el misil."""
        unidades_antes = self.mapa.cantidad_unidades("Brasil")

        self._run_lanzar({
            "mensaje": "lanzar_misil",
            "pais_origen": "Argentina",
            "pais_destino": "Brasil",
        })

        self.assertLess(self.mapa.cantidad_unidades("Brasil"), unidades_antes)
        self.assertEqual(self.mapa.cantidad_misiles("Argentina"), 0)
        self.assertEqual(len(self.server.resultados_misil), 1)
        self.assertTrue(self.server.sent_map)

    def test_lanzamiento_a_propio_pais_falla(self) -> None:
        """No se puede lanzar un misil a un país propio."""
        self.mapa.asignar_pais(1, "Brasil")

        self._run_lanzar({
            "mensaje": "lanzar_misil",
            "pais_origen": "Argentina",
            "pais_destino": "Brasil",
        })

        self.client.transmisor.enviar_error_chat.assert_called_once()
        self.assertEqual(self.mapa.cantidad_misiles("Argentina"), 1)


if __name__ == "__main__":
    unittest.main()
