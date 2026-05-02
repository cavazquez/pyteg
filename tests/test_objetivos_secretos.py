"""Tests para el módulo de objetivos secretos."""

import unittest
from typing import cast
from unittest.mock import Mock, patch

from pyteg.core.partida.objetivos_secretos import ObjetivosSecretos


class TestObjetivosSecretos(unittest.TestCase):
    """Tests para la clase ObjetivosSecretos."""

    def setUp(self) -> None:
        """Configuración inicial para los tests."""
        self.mock_toml_reader = Mock()
        self.objetivos_data: dict[str, dict[str, object]] = {
            "obj_1": {
                "id": "obj_1",
                "tipo": "conquistar_paises",
                "descripcion": "Conquistar 30 países",
                "cantidad_paises": 30,
            },
            "obj_2": {
                "id": "obj_2",
                "tipo": "destruir_jugador",
                "descripcion": "Destruir al jugador rojo o conquistar 24 países",
                "color_objetivo": "rojo",
                "paises_alternativos": 24,
            },
        }
        self.mock_toml_reader.get_objetivos_secretos.return_value = self.objetivos_data

        def mock_get_objetivo_secreto(objetivo_id: str) -> dict[str, object] | None:
            return self.objetivos_data.get(objetivo_id)

        self.mock_toml_reader.get_objetivo_secreto.side_effect = (
            mock_get_objetivo_secreto
        )
        self.mock_toml_reader.get_paises.return_value = ["usa", "canada", "mexico"]

        self.objetivos_secretos = ObjetivosSecretos(self.mock_toml_reader)

    def test_asignar_objetivos_aleatorios(self) -> None:
        """Test de asignación aleatoria de objetivos."""
        jugadores = []
        for i in range(3):
            mock_jugador = Mock()
            uid = i + 1
            mock_jugador.userid.return_value = uid
            mock_jugador.username.return_value = f"Player{i + 1}"
            jugadores.append(mock_jugador)

        self.objetivos_secretos.asignar_objetivos_aleatorios(jugadores)

        for jugador in jugadores:
            self.assertIn(
                int(jugador.userid()),
                self.objetivos_secretos.objetivos_asignados,
            )

    def test_get_objetivo_jugador(self) -> None:
        """Test de obtención de objetivo de un jugador."""
        jugador_id = 123

        objetivo = self.objetivos_secretos.get_objetivo_jugador(jugador_id)
        self.assertIsNone(objetivo)

        self.objetivos_secretos.objetivos_asignados[jugador_id] = "obj_1"
        objetivo = self.objetivos_secretos.get_objetivo_jugador(jugador_id)
        self.assertIsNotNone(objetivo)
        objetivo_dict = cast("dict[str, object]", objetivo)
        self.assertEqual(objetivo_dict["tipo"], "conquistar_paises")

    def test_verificar_condicion_victoria_conquistar_paises(self) -> None:
        """Test de verificación de victoria por conquista de países."""
        jugador_id = 42
        self.objetivos_secretos.objetivos_asignados[jugador_id] = "obj_1"

        mock_mapa: dict[str, list[object]] = {
            "pais1": ["continente1", "coords", jugador_id, 1],
            "pais2": ["continente1", "coords", jugador_id, 2],
        }

        with patch.object(
            self.objetivos_secretos, "_contar_paises_jugador", return_value=30
        ):
            resultado = self.objetivos_secretos.verificar_condicion_victoria(
                jugador_id, mock_mapa, Mock()
            )
            self.assertTrue(resultado)

        with patch.object(
            self.objetivos_secretos, "_contar_paises_jugador", return_value=25
        ):
            resultado = self.objetivos_secretos.verificar_condicion_victoria(
                jugador_id, mock_mapa, Mock()
            )
            self.assertFalse(resultado)

    def test_verificar_condicion_victoria_destruir_jugador(self) -> None:
        """Test de verificación de victoria por destruir jugador."""
        jugador_id = 10
        self.objetivos_secretos.objetivos_asignados[jugador_id] = "obj_2"

        mock_mapa: dict[str, list[object]] = {}

        mock_rojo = Mock()
        mock_rojo.userid.return_value = 55
        mock_azul = Mock()
        mock_azul.userid.return_value = jugador_id

        mock_colores = Mock()
        mock_colores.dame_clientes.return_value = [mock_rojo, mock_azul]
        mock_colores.get_color_name.side_effect = lambda c: (
            "rojo" if c is mock_rojo else "azul"
        )
        mock_colores.get_color_name_by_client_id.return_value = "azul"

        resultado = self.objetivos_secretos.verificar_condicion_victoria(
            jugador_id, mock_mapa, mock_colores
        )
        self.assertTrue(resultado)

    def test_verificar_condicion_victoria_conquistar_continentes(self) -> None:
        """Test de verificación de victoria por conquista de continentes."""
        jugador_id = 77

        objetivo_continentes: dict[str, object] = {
            "id": "obj_3",
            "tipo": "conquistar_continentes",
            "descripcion": "Conquistar America del Norte y Africa",
            "continentes": ["America del Norte", "Africa"],
        }
        self.objetivos_data["obj_3"] = objetivo_continentes
        self.objetivos_secretos.objetivos_asignados[jugador_id] = "obj_3"

        mock_mapa: dict[str, list[object]] = {
            "usa": ["America del Norte", "coords", jugador_id, 1],
            "canada": ["America del Norte", "coords", jugador_id, 1],
            "mexico": ["America del Norte", "coords", jugador_id, 1],
            "egipto": ["Africa", "coords", jugador_id, 1],
            "sudafrica": ["Africa", "coords", jugador_id, 2],
            "nigeria": ["Africa", "coords", jugador_id, 1],
        }

        def mock_get_paises(continente: str) -> list[str]:
            if continente == "America del Norte":
                return ["usa", "canada", "mexico"]
            if continente == "Africa":
                return ["egipto", "sudafrica", "nigeria"]
            return []

        self.mock_toml_reader.get_paises.side_effect = mock_get_paises

        resultado = self.objetivos_secretos.verificar_condicion_victoria(
            jugador_id, mock_mapa, Mock()
        )
        self.assertTrue(resultado)

    def test_contar_paises_jugador(self) -> None:
        """Test del conteo de países de un jugador."""
        jugador_id = 5

        mock_mapa = {
            "pais1": ["continente1", "coords", jugador_id, 1],
            "pais2": ["continente1", "coords", jugador_id, 2],
            "pais3": ["continente2", "coords", 99, 1],
        }

        count = self.objetivos_secretos._contar_paises_jugador(jugador_id, mock_mapa)  # noqa: SLF001
        self.assertEqual(count, 2)

    def test_sin_objetivo_asignado(self) -> None:
        """Test cuando un jugador no tiene objetivo asignado."""
        jugador_id = 88

        resultado = self.objetivos_secretos.verificar_condicion_victoria(
            jugador_id, {}, Mock()
        )
        self.assertFalse(resultado)


if __name__ == "__main__":
    unittest.main()
