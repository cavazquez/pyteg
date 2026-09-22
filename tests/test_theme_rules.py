"""Pruebas del perfil de reglas por tema."""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock

from pyteg.core.partida.reglas import ThemeRulesError, _build_rules, load_theme_rules
from pyteg.core.partida.turn_manager import TurnManager
from pyteg.server.app import Server


class ThemeRulesTests(unittest.TestCase):
    """El perfil separa Classic y Revancha sin mezclar sus valores."""

    def test_revancha_profile_has_official_core_values(self) -> None:
        """Carga los valores oficiales que distinguen la edición."""
        rules = load_theme_rules("revancha")

        self.assertEqual(rules.victory_countries, 45)
        self.assertEqual((rules.first_turn_units, rules.second_turn_units), (8, 4))
        self.assertEqual(
            rules.continent_bonus_map,
            {
                "AmericaDelNorte": 8,
                "AmericaCentral": 8,
                "AmericaDelSur": 6,
                "Europa": 4,
                "Africa": 4,
                "Asia": 3,
                "Oceania": 3,
            },
        )
        self.assertEqual(rules.exchange_units, (6, 10))
        self.assertTrue(rules.exchange_tail_from_last)
        self.assertEqual(
            rules.continent_card_exchange_map["AmericaDelSur"],
            ("Avion", "Tanque"),
        )
        self.assertTrue(rules.missiles_enabled)
        self.assertEqual(rules.situation_ruleset, "revancha")

    def test_classic_profile_keeps_legacy_lobby_default(self) -> None:
        """Classic conserva el lobby histórico y declara objetivo 30."""
        rules = load_theme_rules("classic")
        self.assertEqual(rules.victory_countries, 30)
        self.assertEqual(rules.lobby_victory_countries, 0)

    def test_server_snapshot_publishes_same_profile(self) -> None:
        """El servidor publica el perfil que cargó para el tema."""
        server = Server(theme="revancha")
        try:
            snapshot = server.public_snapshot()
            self.assertEqual(snapshot["reglas"], server.reglas().to_public_dict())
            self.assertEqual(
                snapshot["configuracion"]["reglas"],
                server.reglas().to_public_dict(),
            )
        finally:
            server.detener()

    def test_turn_manager_uses_profile_initial_units(self) -> None:
        """Las primeras rondas usan 8 y 4 unidades en Revancha."""
        rules = load_theme_rules("revancha")
        manager = TurnManager(MagicMock(), rules=rules)
        manager.inicializar_turnos([1])
        self.assertEqual(manager.turno_actual().cant_unidades(), 8)
        manager.avanzar_turno()
        manager.iniciar_nueva_ronda([1], es_segundo_turno=True)
        self.assertEqual(manager.turno_actual().cant_unidades(), 4)

    def test_invalid_profile_is_rejected(self) -> None:
        """Un rango de misil incompatible impide arrancar el perfil."""
        with self.assertRaises(ThemeRulesError):
            _build_rules(
                "broken",
                {
                    "missiles": {
                        "max_distance": 4,
                        "damage_by_distance": [3, 2, 1],
                    }
                },
            )


if __name__ == "__main__":
    unittest.main()
