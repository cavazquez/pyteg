import unittest

from src.tarjeta_de_pais import TarjetaDePais


class TestTarjetaDePais(unittest.TestCase):
    def test_creation_instance(self) -> None:
        tarjeta = TarjetaDePais("Argentina", "Galeon")
        self.assertEqual(tarjeta.pais, "Argentina")
        self.assertEqual(tarjeta.simbolo, "Galeon")
        self.assertFalse(tarjeta.fue_usada())
        self.assertTrue(tarjeta.se_puede_asignar())
        self.assertIsNone(tarjeta.jugador())

    def test_asignar_jugador(self) -> None:
        tarjeta = TarjetaDePais("Argentina", "Galeon")
        tarjeta.asignar("jug1")
        self.assertEqual(tarjeta.jugador(), "jug1")
        self.assertTrue(tarjeta.asignada())
        self.assertTrue(tarjeta.fue_usada())
        self.assertFalse(tarjeta.se_puede_asignar())

    def test_desasignar_jugador(self) -> None:
        tarjeta = TarjetaDePais("Argentina", "Galeon")
        tarjeta.asignar("jug1")
        tarjeta.desasignar()
        self.assertIsNone(tarjeta.jugador())
        self.assertTrue(tarjeta.fue_usada())
        self.assertFalse(tarjeta.se_puede_asignar())

    def test_desusar_tarjeta(self) -> None:
        tarjeta = TarjetaDePais("Argentina", "Galeon")
        tarjeta.asignar("jug1")
        tarjeta.desasignar()
        self.assertIsNone(tarjeta.jugador())
        tarjeta.desusar()
        self.assertFalse(tarjeta.fue_usada())
        self.assertTrue(tarjeta.se_puede_asignar())
