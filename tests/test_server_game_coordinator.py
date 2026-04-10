"""Tests unitarios de ServerGameCoordinator (configuración y broadcast)."""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock

from pyteg.config import DEFAULT_TURN_SECONDS, VICTORY_ALL_COUNTRIES
from pyteg.server_game_coordinator import ServerGameCoordinator


class TestServerGameCoordinator(unittest.TestCase):
    """Setters y envío de configuración sin iniciar partida completa."""

    def setUp(self) -> None:
        """Construye coordinador con dependencias mockeadas."""
        self.mapa = MagicMock()
        self.mazo = MagicMock()
        self.objetivos = MagicMock()
        self.estado = MagicMock()
        self.broadcaster = MagicMock()
        self.color_manager = MagicMock()
        self.coordinator = ServerGameCoordinator(
            self.mapa,
            self.mazo,
            self.objetivos,
            self.estado,
            list,
            self.broadcaster,
            self.color_manager,
        )

    def test_defaults_turno_y_victoria(self) -> None:
        """Valores iniciales vía enviar_configuracion_partida."""
        self.coordinator.enviar_configuracion_partida()
        self.broadcaster.enviar_configuracion_partida.assert_called_once_with(
            DEFAULT_TURN_SECONDS,
            VICTORY_ALL_COUNTRIES,
            objetivos_secretos=False,
            misiles_habilitados=False,
        )

    def test_set_segundos_por_turno_ignora_no_positivo(self) -> None:
        """Solo acepta enteros > 0."""
        self.coordinator.set_segundos_por_turno(99)
        self.coordinator.enviar_configuracion_partida()
        self.broadcaster.enviar_configuracion_partida.assert_called_with(
            99,
            VICTORY_ALL_COUNTRIES,
            objetivos_secretos=False,
            misiles_habilitados=False,
        )
        self.broadcaster.reset_mock()
        self.coordinator.set_segundos_por_turno(0)
        self.coordinator.enviar_configuracion_partida()
        self.broadcaster.enviar_configuracion_partida.assert_called_with(
            99,
            VICTORY_ALL_COUNTRIES,
            objetivos_secretos=False,
            misiles_habilitados=False,
        )

    def test_set_paises_para_victoria(self) -> None:
        """Configura umbral de países para ganar."""
        self.coordinator.set_paises_para_victoria(25)
        self.coordinator.enviar_configuracion_partida()
        self.broadcaster.enviar_configuracion_partida.assert_called_with(
            DEFAULT_TURN_SECONDS,
            25,
            objetivos_secretos=False,
            misiles_habilitados=False,
        )

    def test_set_objetivos_y_misiles(self) -> None:
        """Flags de objetivos secretos y misiles."""
        self.coordinator.set_objetivos_secretos(activados=True)
        self.coordinator.set_misiles_habilitados(activados=True)
        self.assertTrue(self.coordinator.misiles_habilitados())
        self.coordinator.enviar_configuracion_partida()
        self.broadcaster.enviar_configuracion_partida.assert_called_with(
            DEFAULT_TURN_SECONDS,
            VICTORY_ALL_COUNTRIES,
            objetivos_secretos=True,
            misiles_habilitados=True,
        )

    def test_enviar_configuracion_partida_llama_broadcaster(self) -> None:
        """enviar_configuracion_partida reenvía parámetros al broadcaster."""
        self.coordinator.set_segundos_por_turno(30)
        self.coordinator.set_paises_para_victoria(40)
        self.coordinator.set_objetivos_secretos(activados=True)
        self.coordinator.set_misiles_habilitados(activados=False)
        self.coordinator.enviar_configuracion_partida()
        self.broadcaster.enviar_configuracion_partida.assert_called_once_with(
            30,
            40,
            objetivos_secretos=True,
            misiles_habilitados=False,
        )

    def test_game_none_hasta_empezar(self) -> None:
        """game() es None antes de empezar_partida."""
        self.assertIsNone(self.coordinator.game())
        self.assertIsNone(self.coordinator.turno_timer())
