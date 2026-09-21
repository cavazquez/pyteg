"""Tests de lógica de `SoundManager` sin reproducir audio."""

from __future__ import annotations

import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

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

    def test_todos_los_eventos_tienen_recurso_empaquetado(self) -> None:
        """Cada evento registrado apunta a un WAV disponible en el checkout."""
        manager = SoundManager()

        for sound_name in manager._sound_files:  # noqa: SLF001
            sound_path = manager._get_sound_path(sound_name)  # noqa: SLF001
            if sound_path is None:
                self.fail(f"No hay recurso para {sound_name}")
            self.assertTrue(sound_path.is_file(), sound_name)

    @patch("pyteg.sound_manager.get_resource_path")
    def test_recurso_faltante_no_interrumpe_el_juego(
        self, get_resource_path: MagicMock
    ) -> None:
        """Un WAV ausente se ignora y devuelve ``None`` con una advertencia."""
        manager = SoundManager()

        get_resource_path.return_value = Path("/definitely/missing/pyteg/attack.wav")
        self.assertIsNone(manager._get_sound_path("attack"))  # noqa: SLF001


if __name__ == "__main__":
    unittest.main()
