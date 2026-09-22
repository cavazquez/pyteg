"""Regresiones para objetivos secretos y el objetivo común de Revancha."""

from __future__ import annotations

import unittest
from unittest.mock import Mock

from pyteg.colores import Azul, Rojo, Verde
from pyteg.core.partida.objetivos_secretos import ObjetivosSecretos
from pyteg.server.juego.mapa import Mapa
from pyteg.toml_reader import TomlReader


class _Client:
    """Cliente mínimo para resolver color y orden relativo."""

    def __init__(self, user_id: int, color: object) -> None:
        self._user_id = user_id
        self._color = color

    def userid(self) -> int:
        return self._user_id

    def username(self) -> str:
        return f"P{self._user_id}"

    def color_actual(self) -> object:
        return self._color


def _reader(objectives: dict[str, dict[str, object]]) -> Mock:
    reader = Mock()
    reader.get_objetivos_secretos.return_value = objectives
    reader.get_objetivo_secreto.side_effect = objectives.get
    return reader


def _mapa(
    paises: dict[str, tuple[str, int]], *, islas: list[str] | None = None
) -> Mapa:
    def build() -> dict[str, list[object]]:
        return {
            pais: [1, continente, propietario, []]
            for pais, (continente, propietario) in paises.items()
        }

    return Mapa(build, islas=islas)


class RevanchaObjectivesTests(unittest.TestCase):
    """Comprueba objetivos comunes, cuotas, islas y destrucción relativa."""

    def test_common_objective_is_public_and_never_assigned(self) -> None:
        """El objetivo común no entra en el reparto privado."""
        reader = TomlReader.from_theme("revancha", strict=True)
        objetivos = ObjetivosSecretos(reader)
        clients = [_Client(index, Rojo()) for index in range(1, 7)]

        objetivos.asignar_objetivos_aleatorios(clients)

        self.assertEqual(len(objetivos.objetivos_asignados), 6)
        self.assertNotIn("comun_45_paises", objetivos.objetivos_asignados.values())
        self.assertEqual(objetivos.get_objetivos_comunes()[0]["cantidad_paises"], 45)
        objetivos.objetivos_asignados[1] = "comun_45_paises"
        self.assertIsNone(objetivos.get_objetivo_jugador(1))

    def test_quotas_and_islands_use_exclusive_control(self) -> None:
        """Las cuotas e islas requieren control exclusivo."""
        objective = {
            "quota": {
                "id": "quota",
                "tipo": "conquistar_continentes",
                "continentes": ["A"],
                "cuotas_continentes": {"B": 2},
                "islas": 3,
                "continentes_minimos_islas": 2,
            }
        }
        reader = _reader(objective)
        evaluator = ObjetivosSecretos(reader)
        paises = {
            "a1": ("A", 1),
            "a2": ("A", 1),
            "b1": ("B", 1),
            "b2": ("B", 1),
            "c1": ("C", 1),
            "c2": ("C", 1),
        }
        mapa = _mapa(paises, islas=["a2", "b2", "c2"])
        evaluator.objetivos_asignados[1] = "quota"

        self.assertTrue(evaluator.verificar_condicion_victoria(1, mapa, Mock()))
        mapa.set_unidades("c2", 2)
        mapa.crear_condominio("c2", {1: 1, 2: 1})
        self.assertFalse(evaluator.verificar_condicion_victoria(1, mapa, Mock()))

    def test_relative_destruction_follows_active_order(self) -> None:
        """La alternativa destruye al jugador de la derecha del orden actual."""
        objective: dict[str, dict[str, object]] = {
            "left": {
                "id": "left",
                "tipo": "destruir_jugador",
                "objetivo_relativo": "derecha",
            }
        }
        evaluator = ObjetivosSecretos(_reader(objective))
        evaluator.objetivos_asignados[1] = "left"
        evaluator.set_player_order(lambda: [1, 2, 3])
        mapa = _mapa({"a": ("A", 1), "b": ("A", 2), "c": ("A", 3)})
        server = Mock()
        server.dame_clientes.return_value = [
            _Client(1, Rojo()),
            _Client(2, Azul()),
            _Client(3, Verde()),
        ]

        self.assertFalse(evaluator.verificar_condicion_victoria(1, mapa, server))
        mapa.asignar_pais(3, "b")
        mapa.asignar_pais(1, "c")
        self.assertTrue(evaluator.verificar_condicion_victoria(1, mapa, server))

    def test_condominium_does_not_satisfy_country_quota(self) -> None:
        """Un condominio no suma como país controlado en exclusiva."""
        objective = {
            "countries": {
                "id": "countries",
                "tipo": "conquistar_paises",
                "cantidad_paises": 2,
            }
        }
        evaluator = ObjetivosSecretos(_reader(objective))
        evaluator.objetivos_asignados[1] = "countries"
        mapa = _mapa({"a": ("A", 1), "b": ("A", 2)})
        mapa.set_unidades("b", 2)
        mapa.crear_condominio("b", {1: 1, 2: 1})

        self.assertFalse(evaluator.verificar_condicion_victoria(1, mapa, Mock()))


if __name__ == "__main__":
    unittest.main()
