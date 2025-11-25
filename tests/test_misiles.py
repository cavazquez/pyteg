"""Tests para la funcionalidad de misiles en el mapa."""

import unittest

from src.server_mapa import Mapa


class TestMisiles(unittest.TestCase):
    """Tests para la funcionalidad de misiles en el mapa."""

    def test_inicializacion_misiles(self) -> None:
        """Verifica que los misiles se inicializan en 0 para todos los países."""

        def build_mapa() -> dict[str, list[int | str | list[str]]]:
            return {
                "Argentina": [5, "Sudamerica", "Jugador1", ["Brasil"]],
                "Brasil": [3, "Sudamerica", "Jugador2", ["Argentina"]],
            }

        mapa = Mapa(build_mapa)
        self.assertEqual(mapa.cantidad_misiles("Argentina"), 0)
        self.assertEqual(mapa.cantidad_misiles("Brasil"), 0)

    def test_agregar_misil(self) -> None:
        """Verifica que se puede agregar un misil a un país."""

        def build_mapa() -> dict[str, list[int | str | list[str]]]:
            return {
                "Argentina": [5, "Sudamerica", "Jugador1", ["Brasil"]],
            }

        mapa = Mapa(build_mapa)
        self.assertEqual(mapa.cantidad_misiles("Argentina"), 0)

        mapa.agregar_misil("Argentina")
        self.assertEqual(mapa.cantidad_misiles("Argentina"), 1)

        mapa.agregar_misil("Argentina")
        self.assertEqual(mapa.cantidad_misiles("Argentina"), 2)

    def test_usar_misil(self) -> None:
        """Verifica que se puede usar un misil de un país."""

        def build_mapa() -> dict[str, list[int | str | list[str]]]:
            return {
                "Argentina": [5, "Sudamerica", "Jugador1", ["Brasil"]],
            }

        mapa = Mapa(build_mapa)
        mapa.agregar_misil("Argentina")
        mapa.agregar_misil("Argentina")
        self.assertEqual(mapa.cantidad_misiles("Argentina"), 2)

        mapa.usar_misil("Argentina")
        self.assertEqual(mapa.cantidad_misiles("Argentina"), 1)

        mapa.usar_misil("Argentina")
        self.assertEqual(mapa.cantidad_misiles("Argentina"), 0)

    def test_usar_misil_sin_misiles_disponibles(self) -> None:
        """Verifica que no se pueden usar misiles si no hay disponibles."""

        def build_mapa() -> dict[str, list[int | str | list[str]]]:
            return {
                "Argentina": [5, "Sudamerica", "Jugador1", ["Brasil"]],
            }

        mapa = Mapa(build_mapa)
        self.assertEqual(mapa.cantidad_misiles("Argentina"), 0)

        # Intentar usar un misil cuando no hay disponibles no debería causar error
        mapa.usar_misil("Argentina")
        self.assertEqual(mapa.cantidad_misiles("Argentina"), 0)

    def test_cantidad_misiles_pais_inexistente(self) -> None:
        """Verifica que retorna 0 para países inexistentes."""

        def build_mapa() -> dict[str, list[int | str | list[str]]]:
            return {
                "Argentina": [5, "Sudamerica", "Jugador1", ["Brasil"]],
            }

        mapa = Mapa(build_mapa)
        self.assertEqual(mapa.cantidad_misiles("PaisInexistente"), 0)

    def test_calcular_distancia_paises_adyacentes(self) -> None:
        """Verifica cálculo de distancia entre países adyacentes (distancia 1)."""

        def build_mapa() -> dict[str, list[int | str | list[str]]]:
            return {
                "Argentina": [5, "Sudamerica", "Jugador1", ["Brasil", "Chile"]],
                "Brasil": [3, "Sudamerica", "Jugador2", ["Argentina", "Uruguay"]],
                "Chile": [2, "Sudamerica", "Jugador1", ["Argentina"]],
                "Uruguay": [4, "Sudamerica", "Jugador3", ["Brasil"]],
            }

        mapa = Mapa(build_mapa)
        self.assertEqual(mapa.calcular_distancia("Argentina", "Brasil"), 1)
        self.assertEqual(mapa.calcular_distancia("Argentina", "Chile"), 1)
        self.assertEqual(mapa.calcular_distancia("Brasil", "Uruguay"), 1)

    def test_calcular_distancia_dos_saltos(self) -> None:
        """Verifica cálculo de distancia de 2 saltos."""

        def build_mapa() -> dict[str, list[int | str | list[str]]]:
            return {
                "Argentina": [5, "Sudamerica", "Jugador1", ["Brasil"]],
                "Brasil": [3, "Sudamerica", "Jugador2", ["Argentina", "Uruguay"]],
                "Uruguay": [4, "Sudamerica", "Jugador3", ["Brasil"]],
            }

        mapa = Mapa(build_mapa)
        self.assertEqual(mapa.calcular_distancia("Argentina", "Uruguay"), 2)

    def test_calcular_distancia_tres_saltos(self) -> None:
        """Verifica cálculo de distancia de 3 saltos."""

        def build_mapa() -> dict[str, list[int | str | list[str]]]:
            return {
                "A": [5, "Cont", "J1", ["B"]],
                "B": [3, "Cont", "J2", ["A", "C"]],
                "C": [2, "Cont", "J1", ["B", "D"]],
                "D": [4, "Cont", "J3", ["C"]],
            }

        mapa = Mapa(build_mapa)
        self.assertEqual(mapa.calcular_distancia("A", "D"), 3)

    def test_calcular_distancia_mismo_pais(self) -> None:
        """Verifica que la distancia del mismo país a sí mismo es 0."""

        def build_mapa() -> dict[str, list[int | str | list[str]]]:
            return {
                "Argentina": [5, "Sudamerica", "Jugador1", ["Brasil"]],
            }

        mapa = Mapa(build_mapa)
        self.assertEqual(mapa.calcular_distancia("Argentina", "Argentina"), 0)

    def test_calcular_distancia_sin_camino(self) -> None:
        """Verifica que retorna -1 cuando no hay camino entre países."""

        def build_mapa() -> dict[str, list[int | str | list[str]]]:
            return {
                "Argentina": [5, "Sudamerica", "Jugador1", ["Brasil"]],
                "Brasil": [3, "Sudamerica", "Jugador2", ["Argentina"]],
                "Australia": [2, "Oceania", "Jugador3", []],  # País aislado
            }

        mapa = Mapa(build_mapa)
        self.assertEqual(mapa.calcular_distancia("Argentina", "Australia"), -1)

    def test_calcular_distancia_pais_inexistente(self) -> None:
        """Verifica que retorna -1 para países inexistentes."""

        def build_mapa() -> dict[str, list[int | str | list[str]]]:
            return {
                "Argentina": [5, "Sudamerica", "Jugador1", ["Brasil"]],
            }

        mapa = Mapa(build_mapa)
        self.assertEqual(mapa.calcular_distancia("Argentina", "Inexistente"), -1)
        self.assertEqual(mapa.calcular_distancia("Inexistente", "Argentina"), -1)

    def test_calcular_dano_misil_distancia_1(self) -> None:
        """Verifica que el daño a distancia 1 es 3 unidades."""

        def build_mapa() -> dict[str, list[int | str | list[str]]]:
            return {}

        mapa = Mapa(build_mapa)
        self.assertEqual(mapa.calcular_dano_misil(1), 3)

    def test_calcular_dano_misil_distancia_2(self) -> None:
        """Verifica que el daño a distancia 2 es 2 unidades."""

        def build_mapa() -> dict[str, list[int | str | list[str]]]:
            return {}

        mapa = Mapa(build_mapa)
        self.assertEqual(mapa.calcular_dano_misil(2), 2)

    def test_calcular_dano_misil_distancia_3(self) -> None:
        """Verifica que el daño a distancia 3 es 1 unidad."""

        def build_mapa() -> dict[str, list[int | str | list[str]]]:
            return {}

        mapa = Mapa(build_mapa)
        self.assertEqual(mapa.calcular_dano_misil(3), 1)

    def test_calcular_dano_misil_fuera_de_rango(self) -> None:
        """Verifica que el daño fuera de rango (>3) es 0."""

        def build_mapa() -> dict[str, list[int | str | list[str]]]:
            return {}

        mapa = Mapa(build_mapa)
        self.assertEqual(mapa.calcular_dano_misil(0), 0)
        self.assertEqual(mapa.calcular_dano_misil(4), 0)
        self.assertEqual(mapa.calcular_dano_misil(5), 0)
        self.assertEqual(mapa.calcular_dano_misil(-1), 0)

    def test_calcular_distancia_grafo_complejo(self) -> None:
        """Verifica BFS en un grafo más complejo con múltiples caminos."""

        def build_mapa() -> dict[str, list[int | str | list[str]]]:
            return {
                "A": [1, "C1", "J1", ["B", "C"]],
                "B": [1, "C1", "J2", ["A", "D"]],
                "C": [1, "C1", "J1", ["A", "D", "E"]],
                "D": [1, "C2", "J3", ["B", "C", "F"]],
                "E": [1, "C2", "J1", ["C", "F"]],
                "F": [1, "C2", "J2", ["D", "E"]],
            }

        mapa = Mapa(build_mapa)
        # Hay múltiples caminos de A a F, pero el más corto es A->C->E->F (3)
        # o A->C->D->F (3)
        self.assertEqual(mapa.calcular_distancia("A", "F"), 3)

        # Verificar que encuentra el camino más corto, no el más largo
        # A->B->D->F también es de longitud 3
        self.assertEqual(mapa.calcular_distancia("A", "F"), 3)

    def test_transferencia_misiles_con_conquista(self) -> None:
        """Verifica que los misiles permanecen en el país cuando es conquistado.

        (Los misiles pasan al nuevo dueño automáticamente ya que son parte del país).
        """

        def build_mapa() -> dict[str, list[int | str | list[str]]]:
            return {
                "Argentina": [5, "Sudamerica", "Jugador1", ["Brasil"]],
                "Brasil": [3, "Sudamerica", "Jugador2", ["Argentina"]],
            }

        mapa = Mapa(build_mapa)

        # Jugador1 tiene Argentina con 2 misiles
        mapa.agregar_misil("Argentina")
        mapa.agregar_misil("Argentina")
        self.assertEqual(mapa.cantidad_misiles("Argentina"), 2)
        self.assertEqual(mapa.ocupado_por("Argentina"), "Jugador1")

        # Jugador2 conquista Argentina
        mapa.asignar_pais("Jugador2", "Argentina")

        # Los misiles siguen en Argentina (ahora pertenecen a Jugador2)
        self.assertEqual(mapa.cantidad_misiles("Argentina"), 2)
        self.assertEqual(mapa.ocupado_por("Argentina"), "Jugador2")
