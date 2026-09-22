"""Pruebas del consenso de eventos después de una reconexión."""

# ruff: noqa: D102

from __future__ import annotations

from unittest import TestCase
from unittest.mock import MagicMock

from scripts.simulate_game import Bot, Simulation


class SimulationConsensusTests(TestCase):
    """La resincronización no exige repetir eventos históricos."""

    def test_reconexion_compara_resultados_de_misil_desde_la_nueva_epoca(self) -> None:
        event = {
            "mensaje": "resultado_misil",
            "pais_origen": "Origen",
            "pais_destino": "Destino",
        }
        active = Bot(MagicMock(), userid=1)
        active.state_model.snapshot = {
            "countries": {
                "Origen": {"userid": 1, "unidades": 2, "misiles": 0},
            }
        }
        active.missile_results = [event]
        active.missile_results_consensus_offset = 1

        replacement = Bot(MagicMock(), userid=2)
        replacement.state_model.snapshot = {
            "countries": {
                "Origen": {"userid": 1, "unidades": 2, "misiles": 0},
            }
        }

        simulation = Simulation.__new__(Simulation)
        simulation.bots = [active, replacement]
        simulation.continents = {"Origen": "Test"}

        simulation.assert_consensus()
