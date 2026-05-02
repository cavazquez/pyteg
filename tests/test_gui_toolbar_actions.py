"""Tests del mixin `ToolBarActionsMixin` sin QApplication ni QToolBar real."""

# ruff: noqa: D102, SLF001, FBT003 — métodos privados del mixin y asserts sobre mocks.

from __future__ import annotations

import unittest
from types import SimpleNamespace
from typing import Any, cast
from unittest.mock import MagicMock

from pyteg.gui_toolbar_actions import ToolBarActionsMixin


class ClientNullTransmisor:
    """Analogía del transmisor nulo del cliente (`ClientNullTransmisor`)."""


class _FakeConnectedTransmisor:
    """Transmisor con sesión activa (nombre distinto de *NullTransmisor)."""


class _DummyToolbar(ToolBarActionsMixin):
    """Implementación mínima para ejercitar solo el mixin."""

    def __init__(self, main_window: Any) -> None:
        self.main_window = main_window
        self.button_conectar = MagicMock()
        self.button_atacar = MagicMock()
        self.button_mover = MagicMock()


def _btns(tb: _DummyToolbar) -> tuple[MagicMock, MagicMock, MagicMock]:
    """Referencias a los `MagicMock` de las acciones (satisface a mypy).

    Returns:
        Tupla ``(conectar, atacar, mover)``.

    """
    return (
        cast("MagicMock", tb.button_conectar),
        cast("MagicMock", tb.button_atacar),
        cast("MagicMock", tb.button_mover),
    )


class TestToolbarActionsMixin(unittest.TestCase):
    """Estado de conexión y habilitación de botones."""

    def test_esta_conectado_sin_atributo_transmisor(self) -> None:
        mw = SimpleNamespace(scene=MagicMock())
        tb = _DummyToolbar(mw)
        self.assertFalse(tb._esta_conectado())

    def test_esta_conectado_transmisor_none(self) -> None:
        mw = MagicMock()
        mw.transmisor = None
        tb = _DummyToolbar(mw)
        self.assertFalse(tb._esta_conectado())

    def test_esta_conectado_null_transmisor_por_nombre_clase(self) -> None:
        mw = MagicMock()
        mw.transmisor = ClientNullTransmisor()
        tb = _DummyToolbar(mw)
        self.assertFalse(tb._esta_conectado())

    def test_esta_conectado_con_metodo_esta_conectado(self) -> None:
        mw = MagicMock()
        mw.transmisor = MagicMock()
        mw.transmisor.esta_conectado = MagicMock(return_value=True)
        tb = _DummyToolbar(mw)
        self.assertTrue(tb._esta_conectado())

    def test_esta_conectado_sin_metodo_usa_nombre_clase(self) -> None:
        mw = MagicMock()
        mw.transmisor = _FakeConnectedTransmisor()
        tb = _DummyToolbar(mw)
        self.assertTrue(tb._esta_conectado())

    def test_habilitar_solo_conectar(self) -> None:
        mw = MagicMock()
        tb = _DummyToolbar(mw)
        tb._habilitar_solo_conectar()
        c, a, m = _btns(tb)
        c.setEnabled.assert_called_once_with(True)
        a.setEnabled.assert_called_once_with(False)
        m.setEnabled.assert_called_once_with(False)

    def test_habilitar_botones_conectado(self) -> None:
        mw = MagicMock()
        tb = _DummyToolbar(mw)
        tb._habilitar_botones_conectado()
        c, a, m = _btns(tb)
        c.setEnabled.assert_called_once_with(False)
        a.setEnabled.assert_called_once_with(False)
        m.setEnabled.assert_called_once_with(False)

    def test_actualizar_botones_desconectado_no_toca_atacar_mover(self) -> None:
        mw = MagicMock()
        mw.transmisor = None
        tb = _DummyToolbar(mw)
        tb.actualizar_botones_seleccion(hay_dos_paises_seleccionados=True)
        _, a, m = _btns(tb)
        a.setEnabled.assert_not_called()
        m.setEnabled.assert_not_called()

    def test_actualizar_botones_conectado_habilita_segun_seleccion(self) -> None:
        mw = MagicMock()
        mw.transmisor = _FakeConnectedTransmisor()
        tb = _DummyToolbar(mw)
        tb.actualizar_botones_seleccion(hay_dos_paises_seleccionados=True)
        _, a, m = _btns(tb)
        a.setEnabled.assert_called_once_with(True)
        m.setEnabled.assert_called_once_with(True)
