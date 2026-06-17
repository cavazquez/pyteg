"""Tests del gestor de configuración de partida."""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock

from pyteg.gui.managers.config import ConfigManager


class TestConfigManager(unittest.TestCase):
    """ConfigManager conserva el objetivo secreto al actualizar la partida."""

    def test_set_configuracion_no_borra_objetivo_secreto(self) -> None:
        """Actualizar parámetros de partida no elimina el objetivo asignado."""
        manager = ConfigManager(MagicMock())
        manager.set_objetivo_secreto("obj_1", "Conquistar 30 países")

        manager.set_configuracion_partida(
            30,
            25,
            objetivos_secretos=True,
            misiles_habilitados=True,
        )

        self.assertEqual(manager.objetivo_secreto_id, "obj_1")
        self.assertEqual(manager.objetivo_secreto_descripcion, "Conquistar 30 países")
        self.assertTrue(manager.objetivos_secretos)


if __name__ == "__main__":
    unittest.main()
