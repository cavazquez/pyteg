"""Pruebas de integración del sonido con tareas que reciben eventos del servidor."""

# ruff: noqa: D102

from __future__ import annotations

import unittest
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

from pyteg.client.tasks.battle import ClientTaskResultadoBatalla
from pyteg.client.tasks.cards_missiles import ClientTaskTarjetasJugador
from pyteg.client.tasks.lobby.chat import ClientTaskError

if TYPE_CHECKING:
    from pyteg.client.tasks.types import TarjetaItem


class ClientTaskSoundEventsTests(unittest.TestCase):
    """Cada evento relevante dispara el efecto de sonido correspondiente."""

    def test_resultado_de_batalla_reproduce_ataque_y_dados(self) -> None:
        main_window = MagicMock()
        main_window.client.username.return_value = "Ana"
        task = ClientTaskResultadoBatalla({
            "mensaje": "resultado_batalla",
            "atacante": "Ana",
            "defensor": "Beto",
            "origen": "Argentina",
            "destino": "Brasil",
            "dados_atacante": [6, 4],
            "dados_defensor": [3],
            "resultado": {"restar": []},
            "conquistado": False,
        })

        task.run(main_window)

        main_window.sound_manager.play_attack.assert_called_once()
        main_window.sound_manager.play_dice.assert_called_once()

    def test_actualizacion_de_tarjetas_reproduce_sonido_solo_si_cambia(self) -> None:
        main_window = MagicMock()
        main_window.tarjetas_jugador = []
        tarjetas: list[TarjetaItem] = [
            {
                "pais": "Argentina",
                "simbolo": "Galeon",
            }
        ]

        ClientTaskTarjetasJugador({
            "mensaje": "tarjetas_jugador",
            "tarjetas": tarjetas,
        }).run(main_window)
        ClientTaskTarjetasJugador({
            "mensaje": "tarjetas_jugador",
            "tarjetas": tarjetas,
        }).run(main_window)

        main_window.sound_manager.play_card.assert_called_once()

    @patch("pyteg.client.tasks.lobby.chat.QMessageBox")
    def test_error_del_servidor_reproduce_sonido(
        self, message_box_cls: MagicMock
    ) -> None:
        main_window = MagicMock()
        main_window.chat = None

        ClientTaskError({
            "mensaje": "error",
            "error_type": "invalid_command",
            "message": "Comando inválido",
        }).run(main_window)

        main_window.sound_manager.play_error.assert_called_once()
        message_box_cls.return_value.exec.assert_called_once()


if __name__ == "__main__":
    unittest.main()
