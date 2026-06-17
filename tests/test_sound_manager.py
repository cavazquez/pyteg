"""Tests de lógica de `SoundManager` sin reproducir audio."""

from __future__ import annotations

import unittest

from pyteg.sound_manager import SoundManager


class TestSoundManager(unittest.TestCase):
    """Volumen, habilitación y rutas de sonido."""

    def test_volume_se_limita_entre_cero_y_uno(self) -> None:
        """`set_volume` clampea valores fuera de rango."""
        manager = SoundManager()

        manager.set_volume(2.5)
        self.assertEqual(manager.get_volume(), 1.0)

        manager.set_volume(-0.3)
        self.assertEqual(manager.get_volume(), 0.0)

    def test_play_con_sonido_deshabilitado_no_falla(self) -> None:
        """Con `_enabled=False`, `play` retorna sin crear reproductor."""
        manager = SoundManager()
        manager.set_enabled(False)

        manager.play("attack")

        self.assertFalse(manager.is_enabled())

    def test_get_sound_path_desconocido_devuelve_none(self) -> None:
        """Un nombre de evento inexistente no tiene archivo asociado."""
        manager = SoundManager()

        self.assertIsNone(manager._get_sound_path("no_existe"))  # noqa: SLF001


if __name__ == "__main__":
    unittest.main()
