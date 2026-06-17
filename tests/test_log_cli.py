"""Tests para resolución de niveles de logging CLI."""

from __future__ import annotations

import argparse
import logging
import unittest

from pyteg.log_cli import resolve_log_levels


class TestResolveLogLevels(unittest.TestCase):
    """Comprueba la prioridad de flags de logging."""

    def _args(self, **kwargs: object) -> argparse.Namespace:
        defaults: dict[str, object] = {
            "verbose": False,
            "quiet": False,
            "log_level": None,
        }
        defaults.update(kwargs)
        return argparse.Namespace(**defaults)

    def test_default_info(self) -> None:
        """Sin flags, consola y archivo quedan en INFO."""
        console, file_ = resolve_log_levels(self._args())
        self.assertEqual(console, logging.INFO)
        self.assertEqual(file_, logging.INFO)

    def test_verbose_debug(self) -> None:
        """-v activa DEBUG en consola y archivo."""
        console, file_ = resolve_log_levels(self._args(verbose=True))
        self.assertEqual(console, logging.DEBUG)
        self.assertEqual(file_, logging.DEBUG)

    def test_quiet_error(self) -> None:
        """--quiet deja solo ERROR en consola."""
        console, file_ = resolve_log_levels(self._args(quiet=True))
        self.assertEqual(console, logging.ERROR)
        self.assertEqual(file_, logging.INFO)

    def test_log_level_overrides_flags(self) -> None:
        """--log-level tiene prioridad sobre -v y --quiet."""
        console, file_ = resolve_log_levels(
            self._args(verbose=True, quiet=True, log_level="WARNING")
        )
        self.assertEqual(console, logging.WARNING)
        self.assertEqual(file_, logging.INFO)


if __name__ == "__main__":
    unittest.main()
