"""Tests para el módulo de tarjeta de país."""

import unittest

from pyteg.core.cartas.tarjeta_de_pais import TarjetaDePais

JUG1 = 1


class TestTarjetaDePais(unittest.TestCase):
    """Tests para la clase TarjetaDePais."""

    def test_creation_instance(self) -> None:
        """Prueba crear una instancia de TarjetaDePais."""
        tarjeta = TarjetaDePais("Argentina", "Galeon")
        self.assertEqual(tarjeta.pais, "Argentina")
        self.assertEqual(tarjeta.simbolo, "Galeon")
        self.assertFalse(tarjeta.fue_usada())
        self.assertTrue(tarjeta.se_puede_asignar())
        self.assertIsNone(tarjeta.jugador())

    def test_asignar_jugador(self) -> None:
        """Prueba asignar un jugador a la tarjeta."""
        tarjeta = TarjetaDePais("Argentina", "Galeon")
        tarjeta.asignar(JUG1)
        self.assertEqual(tarjeta.jugador(), JUG1)
        self.assertTrue(tarjeta.asignada())
        self.assertTrue(tarjeta.fue_usada())
        self.assertFalse(tarjeta.se_puede_asignar())

    def test_desasignar_jugador(self) -> None:
        """Prueba desasignar un jugador de la tarjeta."""
        tarjeta = TarjetaDePais("Argentina", "Galeon")
        tarjeta.asignar(JUG1)
        tarjeta.desasignar()
        self.assertIsNone(tarjeta.jugador())
        self.assertTrue(tarjeta.fue_usada())
        self.assertFalse(tarjeta.se_puede_asignar())

    def test_desusar_tarjeta(self) -> None:
        """Prueba desusar una tarjeta para que pueda ser asignada nuevamente."""
        tarjeta = TarjetaDePais("Argentina", "Galeon")
        tarjeta.asignar(JUG1)
        tarjeta.desasignar()
        self.assertIsNone(tarjeta.jugador())
        tarjeta.desusar()
        self.assertFalse(tarjeta.fue_usada())
        self.assertTrue(tarjeta.se_puede_asignar())
