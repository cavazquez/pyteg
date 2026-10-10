"""El smoke debe usar al administrador real si TLS cambia el orden de ingreso."""

from __future__ import annotations

import unittest
from types import SimpleNamespace
from typing import TYPE_CHECKING, Any, cast
from unittest.mock import Mock, patch

from pyteg.client.app import Client
from scripts.smoke_qt_multiclient import (
    _start_match,  # noqa: PLC2701 -- regresión del smoke Qt.
)

if TYPE_CHECKING:
    from PySide6.QtWidgets import QApplication

    from pyteg.gui import Gui


class QtSmokeAdminTests(unittest.TestCase):
    """La posición de una ventana no determina los permisos de su jugador."""

    def test_shuffled_connections_use_the_confirmed_administrator(self) -> None:
        """Configura con la tercera ventana cuando las anteriores no son admin."""
        self._check_administrator(2)

    def test_first_window_still_works_when_it_is_the_administrator(self) -> None:
        """Mantiene el recorrido habitual cuando el primer cliente es admin."""
        self._check_administrator(0)

    def _check_administrator(self, position: int) -> None:
        windows: list[Any] = []
        for index in range(4):
            client = Client()
            client.asignar_admin(enabled=index == position)
            windows.append(
                SimpleNamespace(
                    client=client,
                    transmisor=Mock(),
                    estado_actual="Desconectado",
                )
            )
        admin = windows[position]
        admin.transmisor.empezar.side_effect = lambda **_kwargs: setattr(
            admin, "estado_actual", "EsperarJugadores"
        )

        def start() -> None:
            for window in windows:
                window.estado_actual = "JUGANDO"

        admin.transmisor.empezar_partida.side_effect = start

        def wait(_app: object, predicate: Any, _timeout: float, _label: str) -> None:
            self.assertTrue(predicate())

        with patch("scripts.smoke_qt_multiclient._wait_for", side_effect=wait):
            _start_match(cast("QApplication", object()), cast("list[Gui]", windows), 15)
        admin.transmisor.empezar.assert_called_once_with(
            segundos=120, paises_para_victoria=0
        )
        admin.transmisor.empezar_partida.assert_called_once_with()
        for window in windows:
            if window is not admin:
                window.transmisor.empezar.assert_not_called()
                window.transmisor.empezar_partida.assert_not_called()
