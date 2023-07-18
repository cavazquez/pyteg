import unittest

from src.calculos import Calculos
from src.mapa import Mapa


class TestCalculos(unittest.TestCase):
    def test_calcular_unidades_generales_sin_paises(self):
        def build_mapa():
            return {"Argentina": [1, "Pangea", None], "Uruguay": [10, "Pangea", None]}

        mapa = Mapa(build_mapa)
        self.assertEqual(Calculos.calcular_unidades_generales(mapa, "Mengano"), 3)

    def test_calcular_unidades_generales_con_4_paises(self):
        def build_mapa():
            return {
                "Argentina": [1, "Pangea", "Mengano"],
                "Uruguay": [10, "Pangea", "Mengano"],
                "Chile": [10, "America", "Mengano"],
                "Brasil": [10, "Pangea", "Mengano"],
            }

        mapa = Mapa(build_mapa)
        self.assertEqual(Calculos.calcular_unidades_generales(mapa, "Mengano"), 3)

    def test_calcular_unidades_generales_con_8_paises(self):
        def build_mapa():
            return {
                "Argentina": [1, "Pangea", "Mengano"],
                "Uruguay": [10, "Pangea", "Mengano"],
                "Chile": [10, "Pangea", "Mengano"],
                "Brasil": [10, "America", "Mengano"],
                "Mexico": [10, "Pangea", "Mengano"],
                "Canada": [10, "Pangea", "Mengano"],
                "Francia": [10, "Europa", "Mengano"],
                "Italia": [10, "Europa", "Mengano"],
            }

        mapa = Mapa(build_mapa)
        self.assertEqual(Calculos.calcular_unidades_generales(mapa, "Mengano"), 4)

    def test_calcular_unidades_con_toda_europa(self):
        def build_mapa():
            return {
                "Argentina": [1, "Europa", "Mengano"],
                "Uruguay": [10, "Europa", "Mengano"],
                "Chile": [10, "America", "Mengano"],
                "Brasil": [10, "Pangea", "None"],
            }

        mapa = Mapa(build_mapa)
        self.assertEqual(Calculos.calcular_unidades_europa(mapa, "Mengano"), 5)

    def test_calcular_unidades_sin_toda_europa(self):
        def build_mapa():
            return {
                "Argentina": [1, "Europa", "Mengano"],
                "Uruguay": [10, "Europa", "Fulano"],
                "Chile": [10, "America", "Mengano"],
                "Brasil": [10, "Pangea", "None"],
            }

        mapa = Mapa(build_mapa)
        self.assertEqual(Calculos.calcular_unidades_europa(mapa, "Mengano"), 0)

    def test_calcular_unidades_con_toda_asia(self):
        def build_mapa():
            return {
                "Argentina": [1, "Asia", "Mengano"],
                "Uruguay": [10, "Asia", "Mengano"],
                "Chile": [10, "America", "Mengano"],
                "Brasil": [10, "Pangea", "None"],
            }

        mapa = Mapa(build_mapa)
        self.assertEqual(Calculos.calcular_unidades_asia(mapa, "Mengano"), 7)

    def test_calcular_unidades_sin_toda_asia(self):
        def build_mapa():
            return {
                "Argentina": [1, "Asia", "Mengano"],
                "Uruguay": [10, "Asia", "Fulano"],
                "Chile": [10, "America", "Mengano"],
                "Brasil": [10, "Pangea", "None"],
            }

        mapa = Mapa(build_mapa)
        self.assertEqual(Calculos.calcular_unidades_asia(mapa, "Mengano"), 0)

    def test_calcular_unidades_con_toda_africa(self):
        def build_mapa():
            return {
                "Argentina": [1, "Africa", "Mengano"],
                "Uruguay": [10, "Africa", "Mengano"],
                "Chile": [10, "America", "Mengano"],
                "Brasil": [10, "Pangea", "None"],
            }

        mapa = Mapa(build_mapa)
        self.assertEqual(Calculos.calcular_unidades_africa(mapa, "Mengano"), 3)

    def test_calcular_unidades_sin_toda_africa(self):
        def build_mapa():
            return {
                "Argentina": [1, "Africa", "Mengano"],
                "Uruguay": [10, "Africa", "Fulano"],
                "Chile": [10, "America", "Mengano"],
                "Brasil": [10, "Pangea", "None"],
            }

        mapa = Mapa(build_mapa)
        self.assertEqual(Calculos.calcular_unidades_africa(mapa, "Mengano"), 0)

    def test_calcular_unidades_con_toda_oceania(self):
        def build_mapa():
            return {
                "Argentina": [1, "Oceania", "Mengano"],
                "Uruguay": [10, "Oceania", "Mengano"],
                "Chile": [10, "America", "Mengano"],
                "Brasil": [10, "Pangea", "None"],
            }

        mapa = Mapa(build_mapa)
        self.assertEqual(Calculos.calcular_unidades_oceania(mapa, "Mengano"), 2)

    def test_calcular_unidades_sin_toda_ocenia(self):
        def build_mapa():
            return {
                "Argentina": [1, "Oceania", "Mengano"],
                "Uruguay": [10, "Oceania", "Fulano"],
                "Chile": [10, "America", "Mengano"],
                "Brasil": [10, "Pangea", "None"],
            }

        mapa = Mapa(build_mapa)
        self.assertEqual(Calculos.calcular_unidades_oceania(mapa, "Mengano"), 0)

    def test_calcular_unidades_con_toda_america_del_sur(self):
        def build_mapa():
            return {
                "Argentina": [1, "Sudamerica", "Mengano"],
                "Uruguay": [10, "Sudamerica", "Mengano"],
                "Chile": [10, "America", "Mengano"],
                "Brasil": [10, "Pangea", "None"],
            }

        mapa = Mapa(build_mapa)
        self.assertEqual(Calculos.calcular_unidades_america_del_sur(mapa, "Mengano"), 3)

    def test_calcular_unidades_sin_toda_america_del_sur(self):
        def build_mapa():
            return {
                "Argentina": [1, "Sudamerica", "Mengano"],
                "Uruguay": [10, "Sudamerica", "Fulano"],
                "Chile": [10, "America", "Mengano"],
                "Brasil": [10, "Pangea", "None"],
            }

        mapa = Mapa(build_mapa)
        self.assertEqual(Calculos.calcular_unidades_america_del_sur(mapa, "Mengano"), 0)

    def test_calcular_unidades_con_toda_america_del_norte(self):
        def build_mapa():
            return {
                "Argentina": [1, "Norteamerica", "Mengano"],
                "Uruguay": [10, "Norteamerica", "Mengano"],
                "Chile": [10, "America", "Mengano"],
                "Brasil": [10, "Pangea", "None"],
            }

        mapa = Mapa(build_mapa)
        self.assertEqual(
            Calculos.calcular_unidades_america_del_norte(mapa, "Mengano"), 5
        )

    def test_calcular_unidades_sin_toda_america_del_norte(self):
        def build_mapa():
            return {
                "Argentina": [1, "Norteamerica", "Mengano"],
                "Uruguay": [10, "Norteamerica", "Fulano"],
                "Chile": [10, "America", "Mengano"],
                "Brasil": [10, "Pangea", "None"],
            }

        mapa = Mapa(build_mapa)
        self.assertEqual(
            Calculos.calcular_unidades_america_del_norte(mapa, "Mengano"), 0
        )
