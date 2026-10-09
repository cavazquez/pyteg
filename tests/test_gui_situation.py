"""Regresiones de la carta visible y su resincronización desde el servidor."""

from __future__ import annotations

import unittest
from types import SimpleNamespace
from typing import TYPE_CHECKING, Any, ClassVar, cast

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from pyteg.client.app import Client
from pyteg.client.state_adapter import QtClientStateAdapter
from pyteg.client.state_model import ClientStateModel
from pyteg.gui import Gui
from pyteg.gui.widgets.situation import SituationBanner
from pyteg.i18n import get_current_language, set_language
from tests.qt_fixtures import dispose_widget

if TYPE_CHECKING:
    from pyteg.gui.managers.protocols import MainWindowProtocol


def _state() -> dict[str, Any]:
    return {
        "mensaje": "snapshot",
        "snapshot_version": 1,
        "revision": 0,
        "estado": "JUGANDO",
        "configuracion": {"situation_ruleset": "revancha"},
        "players": [
            {"userid": 1, "username": "Ana"},
            {"userid": 2, "username": "Luis"},
            {"userid": 3, "username": "Eva"},
        ],
        "situacion": {
            "id": "crisis_1",
            "nombre": "Crisis",
            "efecto": "crisis",
            "ronda": 2,
            "jugadores_afectados": [1, 3],
            "tiradas_crisis": {"1": 2, "2": 5, "3": 2},
        },
    }


class SituationBannerTests(unittest.TestCase):
    """La franja explica efectos y descarta datos de rondas anteriores."""

    app: ClassVar[QApplication]

    @classmethod
    def setUpClass(cls) -> None:
        """Crea una sola aplicación Qt para la clase."""
        cls.app = cast("QApplication", QApplication.instance() or QApplication([]))

    def setUp(self) -> None:
        """Fija el idioma de las comprobaciones y crea la franja."""
        self.previous_language = get_current_language()
        set_language("es")
        self.banner = SituationBanner()
        self.addCleanup(self.banner.close)
        self.addCleanup(set_language, self.previous_language)

    def test_crisis_names_tied_players_and_reports_all_dice(self) -> None:
        """El mínimo empatado y los dados coinciden con el estado autoritativo."""
        self.banner.update_snapshot(_state(), 1)
        self.assertFalse(self.banner.isHidden())
        self.assertIn("Crisis", self.banner.title_label.text())
        self.assertIn("Ana (vos), Eva", self.banner.details_label.text())
        self.assertIn("Luis: 5", self.banner.details_label.text())
        self.assertIn("Ana (vos): 2", self.banner.details_label.text())

    def test_resync_replaces_card_and_removes_stale_crisis_results(self) -> None:
        """Un resync de la misma revisión reemplaza Crisis por la carta actual."""
        model = ClientStateModel()
        model.local_userid = 1
        window = SimpleNamespace(situation_banner=self.banner)
        adapter = QtClientStateAdapter(cast("MainWindowProtocol", window), model)
        first = _state()
        adapter.apply(first, model.apply_event(first))
        second = _state()
        second["resync"] = True
        second["situacion"] = {
            "id": "snow_1",
            "efecto": "snow",
            "ronda": 3,
            "jugadores_afectados": [1, 2, 3],
            "tiradas_crisis": {},
        }
        adapter.apply(second, model.apply_event(second))
        self.assertIn("Nieve", self.banner.title_label.text())
        self.assertNotIn("Dados:", self.banner.details_label.text())
        adapter.apply(first, model.apply_event(first))
        self.assertIn("Nieve", self.banner.title_label.text())

    def test_lobby_and_disconnect_do_not_revive_the_previous_card(self) -> None:
        """Cambiar de idioma después de limpiar no vuelve a mostrar la carta."""
        self.banner.update_snapshot(_state(), 1)
        lobby = _state()
        lobby["estado"] = "EsperarJugadores"
        self.banner.update_snapshot(lobby, 1)
        self.assertTrue(self.banner.isHidden())
        self.banner.update_snapshot(_state(), 1)
        self.banner.clear()
        self.banner.update_language("es")
        self.assertTrue(self.banner.isHidden())

    def test_disabled_situations_hide_banner_and_first_round_explains_wait(
        self,
    ) -> None:
        """El banner no ocupa espacio con el módulo de situaciones apagado."""
        state = _state()
        state["situacion"] = {"efecto": "none", "ronda": 1}
        self.banner.update_snapshot(state, 1)
        self.assertFalse(self.banner.isHidden())
        self.assertIn("segunda", self.banner.effect_label.text())
        state["configuracion"]["situation_ruleset"] = "none"
        self.banner.update_snapshot(state, 1)
        self.assertTrue(self.banner.isHidden())

    def test_language_change_preserves_data_and_player_names_are_plain_text(
        self,
    ) -> None:
        """Traducir conserva dados y no interpreta nombres como HTML."""
        state = _state()
        state["players"][0]["username"] = "<b>Ana</b>"
        self.banner.update_snapshot(state, 1)
        set_language("en")
        self.banner.update_language("en")
        self.assertIn("Round 2", self.banner.title_label.text())
        self.assertIn("<b>Ana</b>", self.banner.details_label.text())
        self.assertEqual(
            self.banner.details_label.textFormat(), Qt.TextFormat.PlainText
        )

    def test_round_without_applicable_card_explains_the_current_rules(self) -> None:
        """Un mazo sin carta aplicable no se presenta como primera ronda."""
        state = _state()
        state["situacion"] = {"efecto": "none", "ronda": 4}
        self.banner.update_snapshot(state, 1)
        self.assertIn("No hay una carta aplicable", self.banner.effect_label.text())

    def test_active_card_wraps_and_leaves_map_space_in_small_windows(self) -> None:
        """La carta se puede leer y el mapa sigue accesible en tamaños pequeños."""
        window = Gui(Client())
        self.addCleanup(dispose_widget, window)
        banner = window.situation_banner
        if banner is None:
            self.fail("No se construyó la franja de situación")
        banner.update_snapshot(_state(), 1)
        for width, height in ((1024, 600), (720, 480)):
            with self.subTest(width=width, height=height):
                window.resize(width, height)
                self.app.processEvents()
                self.assertLessEqual(banner.width(), window.width())
                self.assertGreaterEqual(
                    banner.effect_label.height(),
                    banner.effect_label.heightForWidth(banner.effect_label.width()),
                )
                view = window.view
                if view is None:
                    self.fail("No se construyó la vista del mapa")
                self.assertGreater(view.viewport().height(), height // 3)
