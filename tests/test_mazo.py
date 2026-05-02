"""Tests para el módulo de mazo."""

import unittest

from pyteg.config import MIN_CARDS_SAME_SYMBOL_FOR_EXCHANGE
from pyteg.core.cartas.mazo import Mazo


class TestMazo(unittest.TestCase):
    """Tests para la clase Mazo."""

    def test_mazo(self) -> None:
        """Prueba la creación de un mazo."""
        self.assertTrue(Mazo(["Argentina"], ["Globo"]))

    def test_cantidad_tarjetas_de_paises(self) -> None:
        """Prueba contar tarjetas de países."""
        simbolos = ["Galeon", "Globo"]

        mazo = Mazo(["Argentina", "Brazil", "Uruguay"], simbolos)
        self.assertEqual(mazo.cantidad_tarjetas(), 3)

    def test_cada_tarjeta_es_un_pais(self) -> None:
        """Prueba que cada tarjeta corresponde a un país."""
        simbolos = ["Galeon", "Globo"]
        paises = ["Argentina", "Uruguay", "Chile"]
        mazo = Mazo(paises, simbolos)
        self.assertTrue(all(tarjeta.pais in paises for tarjeta in mazo.tarjetas()))

    def test_cada_pais_tiene_una_tarjeta(self) -> None:
        """Prueba que cada país tiene una tarjeta."""
        simbolos = ["Galeon", "Globo"]
        paises = ["Argentina", "Uruguay", "Chile"]
        mazo = Mazo(paises, simbolos)
        paises_en_tarjetas = [tarjeta.pais for tarjeta in mazo.tarjetas()]
        self.assertTrue(all(pais in paises_en_tarjetas for pais in paises))

    def test_cada_tarjeta_tiene_un_simbolo(self) -> None:
        """Prueba que cada tarjeta tiene un símbolo."""
        simbolos = ["Galeon", "Globo"]
        paises = ["Argentina", "Uruguay", "Chile"]
        mazo = Mazo(paises, simbolos)
        self.assertTrue(all(tarjeta.simbolo in simbolos for tarjeta in mazo.tarjetas()))

    def test_simbolos_alternados(self) -> None:
        """Prueba que los símbolos se alternan correctamente."""
        simbolos = ["Galeon", "Globo"]
        paises = ["Argentina", "Uruguay", "Chile"]
        tarjetas = Mazo(paises, simbolos).tarjetas()
        self.assertEqual(tarjetas[0].simbolo, "Galeon")
        self.assertEqual(tarjetas[1].simbolo, "Globo")
        self.assertEqual(tarjetas[2].simbolo, "Galeon")

    def test_cantidad_de_tarjetas(self) -> None:
        """Prueba contar tarjetas asignadas a un jugador."""
        simbolos = ["Galeon", "Globo"]
        paises = ["Argentina", "Uruguay", "Chile"]
        mazo = Mazo(paises, simbolos)
        self.assertEqual(mazo.cant_tarjetas_asignadas("jug1"), 0)

    def test_asignar_una_tarjeta(self) -> None:
        """Prueba asignar una tarjeta a un jugador."""
        simbolos = ["Galeon", "Globo"]
        paises = ["Argentina", "Uruguay", "Chile"]
        mazo = Mazo(paises, simbolos)
        mazo.asignar_tarjeta("jug1")
        self.assertEqual(mazo.cant_tarjetas_asignadas("jug1"), 1)
        self.assertEqual(mazo.cantidad_tarjetas_asignadas(), 1)

    def test_asignar_otra_tarjeta(self) -> None:
        """Prueba asignar múltiples tarjetas a diferentes jugadores."""
        simbolos = ["Galeon", "Globo"]
        paises = ["Argentina", "Uruguay", "Chile"]
        mazo = Mazo(paises, simbolos)
        mazo.asignar_tarjeta("jug1")
        mazo.asignar_tarjeta("jug1")
        mazo.asignar_tarjeta("jug2")
        self.assertEqual(mazo.cant_tarjetas_asignadas("jug1"), 2)
        self.assertEqual(mazo.cant_tarjetas_asignadas("jug2"), 1)
        self.assertEqual(mazo.cantidad_tarjetas_asignadas(), 3)

    def test_sin_tarjeta_para_asignar(self) -> None:
        """Prueba cuando no hay tarjetas disponibles para asignar."""
        simbolos = ["Galeon", "Globo"]
        paises = ["Argentina"]
        mazo = Mazo(paises, simbolos)
        mazo.asignar_tarjeta("jug1")
        mazo.asignar_tarjeta("jug1")
        self.assertEqual(mazo.cant_tarjetas_asignadas("jug1"), 1)

    def test_no_asignar_tarjetas_usadas(self) -> None:
        """Prueba que no se asignen tarjetas ya usadas."""
        simbolos = ["Galeon", "Globo"]
        paises = ["Argentina", "Brasil"]
        mazo = Mazo(paises, simbolos)
        tarjeta1 = mazo.asignar_tarjeta("jug1")
        self.assertIsNotNone(tarjeta1)
        tarjeta1.desasignar()  # type: ignore[union-attr]
        tarjeta2 = mazo.asignar_tarjeta("jug1", mezclar=lambda x, _: x)
        self.assertIsNotNone(tarjeta2)
        self.assertNotEqual(tarjeta2.pais, tarjeta1.pais)  # type: ignore[union-attr]

    def test_cantidad_tarjetas_usadas(self) -> None:
        """Prueba contar tarjetas usadas."""
        simbolos = ["Galeon", "Globo"]
        paises = ["Argentina"]
        mazo = Mazo(paises, simbolos)
        tarjeta = mazo.asignar_tarjeta("jug1")
        self.assertIsNotNone(tarjeta)
        tarjeta.desasignar()  # type: ignore[union-attr]
        self.assertEqual(mazo.cantidad_tarjetas_usadas(), 1)

    def test_liberar_tarjetas_usadas(self) -> None:
        """Prueba liberar tarjetas usadas y reasignarlas."""
        simbolos = ["Galeon", "Globo"]
        paises = ["Argentina", "Brasil"]
        mazo = Mazo(paises, simbolos)
        tarjeta1 = mazo.asignar_tarjeta("jug1")
        tarjeta2 = mazo.asignar_tarjeta("jug1")
        self.assertIsNotNone(tarjeta1)
        self.assertIsNotNone(tarjeta2)
        tarjeta1.desasignar()  # type: ignore[union-attr]
        tarjeta2.desasignar()  # type: ignore[union-attr]
        mazo.asignar_tarjeta("jug1")
        self.assertEqual(mazo.cantidad_tarjetas_usadas(), 1)

    def test_dame_simbolos(self) -> None:
        """Prueba obtener los símbolos del mazo."""
        simbolos = ["Galeon", "Globo"]
        paises = ["Argentina", "Brasil"]
        mazo = Mazo(paises, simbolos)

        simbolos_result = mazo.dame_simbolos()
        self.assertSetEqual({"Galeon", "Globo"}, simbolos_result)

    def test_existen_3_simbolos_en_tarjeta(self) -> None:
        """Prueba detectar cuando un jugador tiene 3 tarjetas del mismo símbolo."""
        simbolos = ["Galeon"]
        paises = ["Argentina", "Brasil", "Uruguay"]
        mazo = Mazo(paises, simbolos)
        jugador = "Fulano"

        self.assertListEqual(mazo.simbolo_asignado_almenos_3_tarjetas(jugador), [])
        mazo.asignar_tarjeta(jugador)
        mazo.asignar_tarjeta(jugador)
        mazo.asignar_tarjeta(jugador)
        self.assertListEqual(
            mazo.simbolo_asignado_almenos_3_tarjetas(jugador),
            [("Galeon", 3)],
        )

    def test_no_existen_3_simbolos_en_tarjeta(self) -> None:
        """Prueba cuando un jugador no tiene 3 tarjetas del mismo símbolo."""
        simbolos = ["Galeon", "Cañon"]
        paises = ["Argentina", "Brasil", "Uruguay"]
        mazo = Mazo(paises, simbolos)
        jugador = "Fulano"

        mazo.asignar_tarjeta(jugador)
        mazo.asignar_tarjeta(jugador)
        mazo.asignar_tarjeta(jugador)
        self.assertFalse(
            mazo.simbolo_asignado_almenos_3_tarjetas(jugador)[0][1]
            >= MIN_CARDS_SAME_SYMBOL_FOR_EXCHANGE
        )

    def test_dame_3_tarjetas_mismo_simbolo(self) -> None:
        """Prueba obtener 3 tarjetas del mismo símbolo para canje."""
        simbolos = ["Galeon"]
        paises = ["Argentina", "Brasil", "Uruguay"]
        mazo = Mazo(paises, simbolos)
        jugador = "Fulano"

        mazo.asignar_tarjeta(jugador)
        mazo.asignar_tarjeta(jugador)
        mazo.asignar_tarjeta(jugador)
        self.assertEqual(len(mazo.dame_3_tarjetas_para_canje(jugador)), 3)
