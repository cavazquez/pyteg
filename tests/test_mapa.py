"""Tests para el módulo de mapa del servidor."""

import unittest

from pyteg.server_mapa import Mapa


class TestMap(unittest.TestCase):
    """Tests para la clase Mapa."""

    def test_creation_instance(self) -> None:
        """Prueba la creación de una instancia de Mapa."""

        def build_mapa() -> dict[str, list[int | str | list[str] | None]]:
            return {}

        self.assertTrue(Mapa(build_mapa))

    def test_cant_unidades(self) -> None:
        """Prueba obtener y agregar unidades."""

        def build_mapa() -> dict[str, list[int | str | list[str] | None]]:
            return {"Argentina": [1, "Pangea", None]}

        mapa = Mapa(build_mapa)
        self.assertEqual(mapa.cantidad_unidades("Argentina"), 1)
        mapa.agregar_una_unidad("Argentina")
        self.assertEqual(mapa.cantidad_unidades("Argentina"), 2)

    def test_restar_una_unidad(self) -> None:
        """Prueba restar una unidad de un país."""

        def build_mapa() -> dict[str, list[int | str | list[str] | None]]:
            return {"Argentina": [1, "Pangea", None]}

        mapa = Mapa(build_mapa)
        mapa.restar_una_unidad("Argentina")
        self.assertEqual(mapa.cantidad_unidades("Argentina"), 0)

    def test_set_unidades(self) -> None:
        """Prueba establecer unidades de un país."""

        def build_mapa() -> dict[str, list[int | str | list[str] | None]]:
            return {"Argentina": [1, "Pangea", None]}

        mapa = Mapa(build_mapa)
        mapa.set_unidades("Argentina", 5)
        self.assertEqual(mapa.cantidad_unidades("Argentina"), 5)

    def test_mover_unidades(self) -> None:
        """Prueba mover unidades entre países."""

        def build_mapa() -> dict[str, list[int | str | list[str] | None]]:
            return {"Argentina": [1, "Pangea", None], "Uruguay": [10, "Pangea", None]}

        mapa = Mapa(build_mapa)
        mapa.mover("Uruguay", "Argentina", 6)
        self.assertEqual(mapa.cantidad_unidades("Argentina"), 7)
        self.assertEqual(mapa.cantidad_unidades("Uruguay"), 4)

    def test_consultar_continente(self) -> None:
        """Prueba consultar el continente de un país."""

        def build_mapa() -> dict[str, list[int | str | list[str] | None]]:
            return {"Argentina": [1, "Pangea", None]}

        mapa = Mapa(build_mapa)
        self.assertEqual(mapa.continente("Argentina"), "Pangea")

    def test_ocupado_por(self) -> None:
        """Prueba consultar quién ocupa un país."""

        def build_mapa() -> dict[str, list[int | str | list[str] | None]]:
            return {"Argentina": [1, "Pangea", "Fulano"]}

        mapa = Mapa(build_mapa)
        self.assertEqual(mapa.ocupado_por("Argentina"), "Fulano")

    def test_paises(self) -> None:
        """Prueba obtener la lista de países."""

        def build_mapa() -> dict[str, list[int | str | list[str] | None]]:
            return {"Argentina": [1, "Pangea", None], "Uruguay": [10, "Pangea", None]}

        mapa = Mapa(build_mapa)
        self.assertCountEqual(mapa.paises(), ["Uruguay", "Argentina"])

    def test_cant_paises_por_continente(self) -> None:
        """Prueba contar países por continente."""

        def build_mapa() -> dict[str, list[int | str | list[str] | None]]:
            return {
                "Argentina": [1, "Pangea", None],
                "Uruguay": [10, "Pangea", None],
                "Chile": [1, "America", None],
            }

        mapa = Mapa(build_mapa)
        self.assertEqual(mapa.cantidad_de_paises_por_continente("Pangea"), 2)
        self.assertEqual(mapa.cantidad_de_paises_por_continente("America"), 1)

    def test_asignar_paises_2_jugadores_4_paises(self) -> None:
        """Prueba asignar países con 2 jugadores y 4 países."""

        def build_mapa() -> dict[str, list[int | str | list[str] | None]]:
            return {
                "Argentina": [1, "Pangea", None],
                "Uruguay": [1, "Pangea", None],
                "Chile": [1, "America", None],
                "Bolivia": [1, "America", None],
            }

        mapa = Mapa(build_mapa)
        jugadores = ["Fulano", "Mengano"]
        mapa.asignar_paises(jugadores)
        self.assertEqual(mapa.cantidad_de_paises_del_jugador("Fulano"), 2)
        self.assertEqual(mapa.cantidad_de_paises_del_jugador("Mengano"), 2)

    def test_asignar_paises_2_jugadores_5_paises(self) -> None:
        """Prueba asignar países con 2 jugadores y 5 países."""

        def build_mapa() -> dict[str, list[int | str | list[str] | None]]:
            return {
                "Argentina": [1, "Pangea", None],
                "Uruguay": [1, "Pangea", None],
                "Chile": [1, "America", None],
                "Bolivia": [1, "America", None],
                "Ecuador": [1, "America", None],
            }

        mapa = Mapa(build_mapa)
        jugadores = ["Fulano", "Mengano"]
        mapa.asignar_paises(jugadores)
        cant_fulano = mapa.cantidad_de_paises_del_jugador("Fulano")
        cant_mengano = mapa.cantidad_de_paises_del_jugador("Mengano")

        self.assertEqual(cant_fulano + cant_mengano, 5)
        self.assertGreaterEqual(cant_fulano, 5 // 2)
        self.assertGreaterEqual(cant_mengano, 5 // 2)

    def test_asignar_pais(self) -> None:
        """Prueba asignar un país a un jugador."""

        def build_mapa() -> dict[str, list[int | str | list[str] | None]]:
            return {"Argentina": [1, "Pangea", "Fulano"]}

        mapa = Mapa(build_mapa)
        mapa.asignar_pais("Mengano", "Argentina")
        self.assertEqual(mapa.ocupado_por("Argentina"), "Mengano")

    def test_cant_paises_de_jugador(self) -> None:
        """Prueba contar países de un jugador."""

        def build_mapa() -> dict[str, list[int | str | list[str] | None]]:
            return {
                "Argentina": [1, "Pangea", None],
                "Uruguay": [10, "Pangea", None],
                "Chile": [1, "America", None],
            }

        mapa = Mapa(build_mapa)
        mapa.asignar_pais("Mengano", "Argentina")
        mapa.asignar_pais("Mengano", "Chile")
        self.assertEqual(mapa.cantidad_de_paises_del_jugador("Mengano"), 2)
        self.assertEqual(mapa.cantidad_de_paises_del_jugador("Fulano"), 0)

    def test_cant_paises_del_jugador_por_continente(self) -> None:
        """Prueba contar países de un jugador por continente."""

        def build_mapa() -> dict[str, list[int | str | list[str] | None]]:
            return {
                "Argentina": [1, "Pangea", None],
                "Uruguay": [10, "Pangea", None],
                "Chile": [1, "America", None],
            }

        mapa = Mapa(build_mapa)
        mapa.asignar_pais("Mengano", "Argentina")
        mapa.asignar_pais("Mengano", "Uruguay")
        self.assertEqual(
            mapa.cantidad_de_paises_del_jugador_por_continente("Mengano", "Pangea"),
            2,
        )
        self.assertEqual(
            mapa.cantidad_de_paises_del_jugador_por_continente("Mengano", "America"),
            0,
        )

    def test_jugador_controla_continente_europa(self) -> None:
        """Prueba verificar si un jugador controla toda Europa."""

        def build_mapa() -> dict[str, list[int | str | list[str] | None]]:
            return {
                "Argentina": [1, "Europa", "Mengano"],
                "Uruguay": [10, "Europa", None],
                "Chile": [1, "America", None],
            }

        mapa = Mapa(build_mapa)
        self.assertFalse(mapa.jugador_controla_continente("Mengano", "Europa"))
        mapa.asignar_pais("Mengano", "Uruguay")
        self.assertTrue(mapa.jugador_controla_continente("Mengano", "Europa"))

    def test_jugador_controla_continente_asia(self) -> None:
        """Prueba verificar si un jugador controla toda Asia."""

        def build_mapa() -> dict[str, list[int | str | list[str] | None]]:
            return {
                "Argentina": [1, "Asia", "Mengano"],
                "Uruguay": [10, "Asia", None],
                "Chile": [1, "America", None],
            }

        mapa = Mapa(build_mapa)
        self.assertFalse(mapa.jugador_controla_continente("Mengano", "Asia"))
        mapa.asignar_pais("Mengano", "Uruguay")
        self.assertTrue(mapa.jugador_controla_continente("Mengano", "Asia"))

    def test_jugador_controla_continente_oceania(self) -> None:
        """Prueba verificar si un jugador controla toda Oceanía."""

        def build_mapa() -> dict[str, list[int | str | list[str] | None]]:
            return {
                "Argentina": [1, "Oceania", "Mengano"],
                "Uruguay": [10, "Oceania", None],
                "Chile": [1, "America", None],
            }

        mapa = Mapa(build_mapa)
        self.assertFalse(mapa.jugador_controla_continente("Mengano", "Oceania"))
        mapa.asignar_pais("Mengano", "Uruguay")
        self.assertTrue(mapa.jugador_controla_continente("Mengano", "Oceania"))

    def test_jugador_controla_continente_sudamerica(self) -> None:
        """Prueba verificar si un jugador controla toda América del Sur."""

        def build_mapa() -> dict[str, list[int | str | list[str] | None]]:
            return {
                "Argentina": [1, "Sudamerica", "Mengano"],
                "Uruguay": [10, "Sudamerica", None],
                "Chile": [1, "America", None],
            }

        mapa = Mapa(build_mapa)
        self.assertFalse(mapa.jugador_controla_continente("Mengano", "Sudamerica"))
        mapa.asignar_pais("Mengano", "Uruguay")
        self.assertTrue(mapa.jugador_controla_continente("Mengano", "Sudamerica"))

    def test_jugador_controla_continente_norteamerica(self) -> None:
        """Prueba verificar si un jugador controla toda América del Norte."""

        def build_mapa() -> dict[str, list[int | str | list[str] | None]]:
            return {
                "Argentina": [1, "Norteamerica", "Mengano"],
                "Uruguay": [10, "Norteamerica", None],
                "Chile": [1, "America", None],
            }

        mapa = Mapa(build_mapa)
        self.assertFalse(mapa.jugador_controla_continente("Mengano", "Norteamerica"))
        mapa.asignar_pais("Mengano", "Uruguay")
        self.assertTrue(mapa.jugador_controla_continente("Mengano", "Norteamerica"))

    def test_jugador_controla_continente_africa(self) -> None:
        """Prueba verificar si un jugador controla toda África."""

        def build_mapa() -> dict[str, list[int | str | list[str] | None]]:
            return {
                "Argentina": [1, "Africa", "Mengano"],
                "Uruguay": [10, "Africa", None],
                "Chile": [1, "America", None],
            }

        mapa = Mapa(build_mapa)
        self.assertFalse(mapa.jugador_controla_continente("Mengano", "Africa"))
        mapa.asignar_pais("Mengano", "Uruguay")
        self.assertTrue(mapa.jugador_controla_continente("Mengano", "Africa"))

    def test_str(self) -> None:
        """Prueba la representación en string del mapa."""

        def build_mapa() -> dict[str, list[int | str | list[str] | None]]:
            return {
                "Argentina": [1, "Africa", "Mengano"],
                "Uruguay": [10, "Africa", None],
            }

        mapa = Mapa(build_mapa)
        # Ahora incluye el campo de misiles (índice 4) inicializado en 0
        self.assertEqual(
            str(mapa),
            (
                '{"Argentina": [1, "Africa", "Mengano", [], 0], '
                '"Uruguay": [10, "Africa", null, [], 0]}'
            ),
        )

    def test_aplicar_resultado_batalla(self) -> None:
        """Prueba aplicar resultado de batalla."""

        def build_mapa() -> dict[str, list[int | str | list[str] | None]]:
            return {
                "Argentina": [4, "Africa", "Mengano"],
                "Uruguay": [2, "Africa", "Fulano"],
                "Chile": [1, "America", None],
            }

        resultado = {
            "atacante": "Argentina",
            "defensor": "Uruguay",
            "restar": ["Argentina"],
        }
        mapa = Mapa(build_mapa)
        mapa.aplicar_resultado_batalla(resultado)
        self.assertEqual(mapa.cantidad_unidades("Argentina"), 3)

    def test_aplicar_resultado_batalla_y_ocupar_pais(self) -> None:
        """Prueba aplicar resultado de batalla y ocupar país."""

        def build_mapa() -> dict[str, list[int | str | list[str] | None]]:
            return {
                "Argentina": [4, "Africa", "Mengano"],
                "Uruguay": [2, "Africa", "Fulano"],
                "Chile": [1, "America", None],
            }

        resultado = {
            "defensor": "Uruguay",
            "atacante": "Argentina",
            "restar": ["Uruguay", "Uruguay"],
        }
        mapa = Mapa(build_mapa)
        mapa.aplicar_resultado_batalla(resultado)
        self.assertEqual(mapa.cantidad_unidades("Uruguay"), 1)
        self.assertEqual(mapa.ocupado_por("Uruguay"), "Mengano")
