import unittest

from src.mazo import Mazo


class TestMazo(unittest.TestCase):
    def test_mazo(self):
        self.assertTrue(Mazo(["Argentina"], ["Globo"]))

    def test_cantidad_tarjetas_de_paises(self):
        simbolos = ["Galeon", "Globo"]

        mazo = Mazo(["Argentina", "Brazil", "Uruguay"], simbolos)
        self.assertEqual(mazo.cantidad_tarjetas(), 3)

    def test_cada_tarjeta_es_un_pais(self):
        simbolos = ["Galeon", "Globo"]
        paises = ["Argentina", "Uruguay", "Chile"]
        mazo = Mazo(paises, simbolos)
        self.assertTrue(
            all([tarjeta.dame_pais() in paises for tarjeta in mazo.tarjetas()])
        )

    def test_cada_pais_tiene_una_tarjeta(self):
        simbolos = ["Galeon", "Globo"]
        paises = ["Argentina", "Uruguay", "Chile"]
        mazo = Mazo(paises, simbolos)
        paises_en_tarjetas = [tarjeta.dame_pais() for tarjeta in mazo.tarjetas()]
        self.assertTrue(all([pais in paises_en_tarjetas for pais in paises]))

    def test_cada_tarjeta_tiene_un_simbolo(self):
        simbolos = ["Galeon", "Globo"]
        paises = ["Argentina", "Uruguay", "Chile"]
        mazo = Mazo(paises, simbolos)
        self.assertTrue(
            all([tarjeta.dame_simbolo() in simbolos for tarjeta in mazo.tarjetas()])
        )

    def test_simbolos_alternados(self):
        simbolos = ["Galeon", "Globo"]
        paises = ["Argentina", "Uruguay", "Chile"]
        tarjetas = Mazo(paises, simbolos).tarjetas()
        self.assertEqual(tarjetas[0].dame_simbolo(), "Galeon")
        self.assertEqual(tarjetas[1].dame_simbolo(), "Globo")
        self.assertEqual(tarjetas[2].dame_simbolo(), "Galeon")

    def test_cantidad_de_tarjetas(self):
        simbolos = ["Galeon", "Globo"]
        paises = ["Argentina", "Uruguay", "Chile"]
        mazo = Mazo(paises, simbolos)
        self.assertEqual(mazo.tarjetas_asignadas("jug1"), 0)

    def test_asignar_una_tarjeta(self):
        simbolos = ["Galeon", "Globo"]
        paises = ["Argentina", "Uruguay", "Chile"]
        mazo = Mazo(paises, simbolos)
        mazo.asignar_tarjeta("jug1")
        self.assertEqual(mazo.tarjetas_asignadas("jug1"), 1)

    def test_asignar_otra_tarjeta(self):
        simbolos = ["Galeon", "Globo"]
        paises = ["Argentina", "Uruguay", "Chile"]
        mazo = Mazo(paises, simbolos)
        mazo.asignar_tarjeta("jug1")
        mazo.asignar_tarjeta("jug1")
        mazo.asignar_tarjeta("jug2")
        self.assertEqual(mazo.tarjetas_asignadas("jug1"), 2)
        self.assertEqual(mazo.tarjetas_asignadas("jug2"), 1)

    def test_sin_tarjeta_para_asignar(self):
        simbolos = ["Galeon", "Globo"]
        paises = ["Argentina"]
        mazo = Mazo(paises, simbolos)
        mazo.asignar_tarjeta("jug1")
        mazo.asignar_tarjeta("jug1")
        self.assertEqual(mazo.tarjetas_asignadas("jug1"), 1)

    def test_no_asignar_tarjetas_usadas(self):
        simbolos = ["Galeon", "Globo"]
        paises = ["Argentina", "Brasil"]
        mazo = Mazo(paises, simbolos)
        # print(mazo)
        tarjeta1 = mazo.asignar_tarjeta("jug1")
        # print(mazo)
        mazo.liberar(tarjeta1)
        # print(mazo)
        # print(mazo.asignada(tarjeta1))
        # print(mazo.fue_usada(tarjeta1))
        tarjeta2 = mazo.asignar_tarjeta("jug1", mezclar=lambda x, y: x)
        # print(mazo)
        self.assertNotEqual(tarjeta2.pais, tarjeta1.pais)

    def test_fue_usada(self):
        simbolos = ["Galeon", "Globo"]
        paises = ["Argentina"]
        mazo = Mazo(paises, simbolos)
        tarjeta = mazo.tarjetas()[0]
        self.assertFalse(mazo.fue_usada(tarjeta))
        mazo.asignar_tarjeta("jug1")
        mazo.liberar(tarjeta)
        self.assertTrue(mazo.fue_usada(tarjeta))

    def test_cantidad_tarjetas_usadas(self):
        simbolos = ["Galeon", "Globo"]
        paises = ["Argentina"]
        mazo = Mazo(paises, simbolos)
        tarjeta = mazo.asignar_tarjeta("jug1")
        mazo.liberar(tarjeta)
        self.assertEqual(mazo.cantidad_tarjetas_usadas(), 1)

    def test_liberar_tarjetas_usadas(self):
        simbolos = ["Galeon", "Globo"]
        paises = ["Argentina", "Brasil"]
        mazo = Mazo(paises, simbolos)
        tarjeta1 = mazo.asignar_tarjeta("jug1")
        tarjeta2 = mazo.asignar_tarjeta("jug1")
        mazo.liberar(tarjeta1)
        mazo.liberar(tarjeta2)
        mazo.asignar_tarjeta("jug1")
        self.assertEqual(mazo.cantidad_tarjetas_usadas(), 1)
