"""Tests del mixin `ToolBarActionsMixin` sin QApplication ni QToolBar real."""

# ruff: noqa: D102, SLF001, FBT003 — métodos privados del mixin y asserts sobre mocks.

from __future__ import annotations

import unittest
from types import SimpleNamespace
from typing import Any, cast
from unittest.mock import MagicMock

from pyteg.client.conexion.transmisor import ClientNullTransmisor
from pyteg.gui.toolbar.actions_mixin import ToolBarActionsMixin


class _FakeConnectedTransmisor:
    """Transmisor mínimo con sesión activa."""

    def esta_conectado(self) -> bool:
        """Indica que la sesión está activa.

        Returns:
            Siempre ``True``.

        """
        return True


class _DummyToolbar(ToolBarActionsMixin):
    """Implementación mínima para ejercitar solo el mixin."""

    def __init__(self, main_window: Any) -> None:
        self.main_window = main_window
        self.button_conectar = MagicMock()
        self.button_atacar = MagicMock()
        self.button_mover = MagicMock()
        self.button_finalizar_turno = MagicMock()


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

    def test_esta_conectado_null_transmisor(self) -> None:
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
        mw.client.userid.return_value = None
        mw.jugador_actual_id = None
        tb = _DummyToolbar(mw)
        tb._habilitar_botones_conectado()
        c, a, m = _btns(tb)
        c.setEnabled.assert_called_once_with(False)
        a.setEnabled.assert_called_once_with(False)
        m.setEnabled.assert_called_once_with(False)
        cast("MagicMock", tb.button_finalizar_turno).setEnabled.assert_called_once_with(
            False
        )

    def test_actualizar_botones_desconectado_no_toca_atacar_mover(self) -> None:
        mw = MagicMock()
        mw.transmisor = ClientNullTransmisor()
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

    def test_deshabilitar_acciones_juego(self) -> None:
        """El cierre de partida bloquea todas las acciones de turno."""
        tb = _DummyToolbar(MagicMock())

        tb.deshabilitar_acciones_juego()

        _, atacar, mover = _btns(tb)
        atacar.setEnabled.assert_called_once_with(False)
        mover.setEnabled.assert_called_once_with(False)
        cast("MagicMock", tb.button_finalizar_turno).setEnabled.assert_called_once_with(
            False
        )

    def test_finalizar_se_bloquea_durante_colocacion_y_explica_motivo(self) -> None:
        mw = SimpleNamespace(
            transmisor=_FakeConnectedTransmisor(),
            client=MagicMock(),
            jugador_actual_id=1,
            fase_actual="colocacion",
            unidades_pendientes_servidor=3,
            partida_finalizada=False,
        )
        mw.client.userid.return_value = 1
        tb = _DummyToolbar(mw)

        tb.actualizar_botones_turno(
            es_mi_turno=True,
            puede_finalizar_turno=False,
        )
        tb.actualizar_motivos_acciones(
            hay_dos_paises_seleccionados=False,
            puede_actuar=False,
            es_mi_turno=True,
        )

        cast("MagicMock", tb.button_finalizar_turno).setEnabled.assert_called_once_with(
            False
        )
        cast("MagicMock", tb.button_finalizar_turno).setToolTip.assert_called_once_with(
            "Colocá todas las unidades antes de finalizar el turno"
        )
        cast("MagicMock", tb.button_atacar).setToolTip.assert_called_once_with(
            "Colocá todas las unidades antes de atacar o mover"
        )
