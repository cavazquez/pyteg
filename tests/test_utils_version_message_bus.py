"""Tests para pyteg.utils, pyteg.version y pyteg.message_bus."""

from __future__ import annotations

import unittest
from typing import Any, cast
from unittest.mock import MagicMock, patch

from pyteg.message_bus import (
    EventHandler,
    MessageBus,
    get_message_bus,
    reset_message_bus,
)
from pyteg.utils import BASE_DIR, get_resource_path
from pyteg.version import get_version, get_version_info


class TestGetResourcePath(unittest.TestCase):
    """Tests de get_resource_path."""

    def test_ruta_absoluta_y_sufijo(self) -> None:
        """get_resource_path devuelve ruta absoluta al recurso."""
        p = get_resource_path("themes/classic/paises.toml")
        self.assertTrue(p.is_absolute())
        self.assertEqual(p.name, "paises.toml")
        self.assertEqual(p.parent.name, "classic")

    def test_base_dir_es_padre_del_paquete(self) -> None:
        """BASE_DIR apunta a la raíz del repo."""
        self.assertTrue((BASE_DIR / "pyproject.toml").exists())


class TestGetVersion(unittest.TestCase):
    """Tests de lectura de versión."""

    @patch("pyteg.version.os.getenv")
    def test_prioriza_variable_entorno(self, mock_getenv: MagicMock) -> None:
        """PYTEG_VERSION tiene prioridad sobre pyproject."""
        mock_getenv.return_value = "9.9.9-test"
        self.assertEqual(get_version(), "9.9.9-test")

    @patch("pyteg.version.os.getenv", return_value=None)
    def test_lee_pyproject_en_desarrollo(self, _: object) -> None:
        """Sin env, se lee la versión desde pyproject.toml."""
        v = get_version()
        self.assertNotEqual(v, "unknown")
        self.assertRegex(v, r"^\d+\.\d+")

    def test_get_version_info(self) -> None:
        """get_version_info incluye name y version."""
        info = get_version_info()
        self.assertEqual(info["name"], "PyTeg")
        self.assertIn("version", info)
        self.assertIn("description", info)


class TestMessageBus(unittest.TestCase):
    """Tests del bus de mensajes."""

    def setUp(self) -> None:
        """Aísla el singleton entre tests."""
        reset_message_bus()

    def tearDown(self) -> None:
        """Limpia el singleton tras cada test."""
        reset_message_bus()

    def test_subscribe_publish(self) -> None:
        """El handler recibe el payload publicado."""
        bus = MessageBus()
        received: list[dict[str, Any]] = []

        def handler(data: dict[str, Any]) -> None:
            received.append(dict(data))

        bus.subscribe("game_event", cast("EventHandler", handler))
        bus.publish("game_event", {"a": 1})
        self.assertEqual(received, [{"a": 1}])

    def test_no_duplica_handler(self) -> None:
        """Subscribe idempotente para el mismo handler."""
        bus = MessageBus()
        calls: list[int] = []

        def handler(_data: dict[str, Any]) -> None:
            calls.append(1)

        bus.subscribe("e", cast("EventHandler", handler))
        bus.subscribe("e", cast("EventHandler", handler))
        bus.publish("e", {})
        self.assertEqual(calls, [1])

    def test_unsubscribe(self) -> None:
        """Unsubscribe elimina el handler."""
        bus = MessageBus()

        def handler(_data: dict[str, Any]) -> None:
            pass

        bus.subscribe("e", cast("EventHandler", handler))
        self.assertEqual(bus.get_subscriber_count("e"), 1)
        bus.unsubscribe("e", cast("EventHandler", handler))
        self.assertEqual(bus.get_subscriber_count("e"), 0)

    def test_publish_sin_suscriptores_no_falla(self) -> None:
        """Publish sin listeners no lanza."""
        bus = MessageBus()
        bus.publish("vacío", {})

    def test_disable_impide_publish(self) -> None:
        """Con bus deshabilitado no se invocan handlers."""
        bus = MessageBus()
        got: list[int] = []

        def handler(_data: dict[str, Any]) -> None:
            got.append(1)

        bus.subscribe("x", cast("EventHandler", handler))
        bus.disable()
        bus.publish("x", {})
        self.assertEqual(got, [])
        bus.enable()
        bus.publish("x", {})
        self.assertEqual(got, [1])

    def test_clear_y_clear_event(self) -> None:
        """clear_event y clear vacían suscriptores."""
        bus = MessageBus()

        def handler(_data: dict[str, Any]) -> None:
            pass

        bus.subscribe("a", cast("EventHandler", handler))
        bus.subscribe("b", cast("EventHandler", handler))
        bus.clear_event("a")
        self.assertEqual(bus.get_subscriber_count("a"), 0)
        self.assertEqual(bus.get_subscriber_count("b"), 1)
        bus.clear()
        self.assertEqual(bus.get_subscriber_count("b"), 0)

    def test_handler_que_lanza_no_rompe_siguiente(self) -> None:
        """Un handler con error no impide ejecutar el siguiente."""
        bus = MessageBus()
        second: list[int] = []

        def bad(_data: dict[str, Any]) -> None:
            msg = "fallo"
            raise RuntimeError(msg)

        def good(_data: dict[str, Any]) -> None:
            second.append(1)

        bus.subscribe("e", cast("EventHandler", bad))
        bus.subscribe("e", cast("EventHandler", good))
        with patch("pyteg.message_bus.LOGGER.exception"):
            bus.publish("e", {})
        self.assertEqual(second, [1])

    def test_get_message_bus_singleton(self) -> None:
        """get_message_bus devuelve la misma instancia."""
        reset_message_bus()
        a = get_message_bus()
        b = get_message_bus()
        self.assertIs(a, b)
