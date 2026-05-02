"""Tests del mixin `ToolBarWindowMixin` con mocks (sin ventana real)."""

# ruff: noqa: FBT003

from __future__ import annotations

import unittest
from typing import cast
from unittest.mock import MagicMock, patch

from pyteg.gui.toolbar.window_mixin import ToolBarWindowMixin


class _Host(ToolBarWindowMixin):
    """Anfitrión mínimo para el mixin."""

    button_fullscreen: MagicMock

    def __init__(self) -> None:
        self.main_window = MagicMock()
        self.button_fullscreen = MagicMock()


class TestToolBarWindowMixin(unittest.TestCase):
    """Redimensionado y pantalla completa."""

    def test_resize_window_fullscreen_por_ceros(self) -> None:
        """width/height 0 delegan en showFullScreen."""
        h = _Host()
        h.resize_window(0, 0)
        h.main_window.showFullScreen.assert_called_once()
        cast("MagicMock", h.button_fullscreen.setChecked).assert_called_once_with(True)

    @patch("pyteg.gui.toolbar.window_mixin.center_window_on_screen")
    def test_resize_window_modo_normal(self, mock_center: MagicMock) -> None:
        """Tamaño explícito: ventana normal, resize y centrado."""
        h = _Host()
        h.resize_window(1024, 768)
        h.main_window.showNormal.assert_called_once()
        h.main_window.resize.assert_called_once_with(1024, 768)
        mock_center.assert_called_once_with(h.main_window)
        cast("MagicMock", h.button_fullscreen.setChecked).assert_called_once_with(False)
