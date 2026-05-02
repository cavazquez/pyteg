"""Tests para el módulo de objetivos secretos."""

import unittest
from typing import cast
from unittest.mock import Mock, patch

from pyteg.core.partida.objetivos_secretos import ObjetivosSecretos


class TestObjetivosSecretos(unittest.TestCase):
    """Tests para la clase ObjetivosSecretos."""

    def setUp(self) -> None:
        """Configuración inicial para los tests."""
        # Mock del TomlReader con objetivos de prueba
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

        # Configure mock to return specific objective data based on ID

        def mock_get_objetivo_secreto(objetivo_id: str) -> dict[str, object] | None:
            return self.objetivos_data.get(objetivo_id)

        self.mock_toml_reader.get_objetivo_secreto.side_effect = (
            mock_get_objetivo_secreto
        )
        self.mock_toml_reader.get_paises.return_value = ["usa", "canada", "mexico"]

        self.objetivos_secretos = ObjetivosSecretos(self.mock_toml_reader)

    def test_asignar_objetivos_aleatorios(self) -> None:
        """Test de asignación aleatoria de objetivos."""
        # Crear mocks de jugadores con userid() method
        jugadores = []
        for i in range(3):
            mock_jugador = Mock()
            user_id = f"jugador{i + 1}"
            mock_jugador.userid.return_value = user_id
            mock_jugador.username.return_value = f"Player{i + 1}"
            jugadores.append(mock_jugador)

        self.objetivos_secretos.asignar_objetivos_aleatorios(jugadores)

        # Verificar que todos los jugadores tienen objetivos asignados
        for jugador in jugadores:
            self.assertIn(jugador.userid(), self.objetivos_secretos.objetivos_asignados)

    def test_get_objetivo_jugador(self) -> None:
        """Test de obtención de objetivo de un jugador."""
        jugador = "test_player"

        # Sin objetivo asignado
        objetivo = self.objetivos_secretos.get_objetivo_jugador(jugador)
        self.assertIsNone(objetivo)

        # Con objetivo asignado
        self.objetivos_secretos.objetivos_asignados[jugador] = "obj_1"
        objetivo = self.objetivos_secretos.get_objetivo_jugador(jugador)
        self.assertIsNotNone(objetivo)
        objetivo_dict = cast("dict[str, object]", objetivo)
        self.assertEqual(objetivo_dict["tipo"], "conquistar_paises")

    def test_verificar_condicion_victoria_conquistar_paises(self) -> None:
        """Test de verificación de victoria por conquista de países."""
        jugador = "test_player"
        self.objetivos_secretos.objetivos_asignados[jugador] = "obj_1"

        # Crear mock de jugador
        mock_jugador = Mock()
        mock_jugador.userid.return_value = jugador

        # Mock del mapa con países controlados (formato: continente, coords, dueño, unidades)  # noqa: E501
        mock_mapa: dict[str, list[object]] = {
            "pais1": ["continente1", "coords", mock_jugador, 1],
            "pais2": ["continente1", "coords", mock_jugador, 2],
        }

        # Simular que el jugador tiene 30 países
        with patch.object(
            self.objetivos_secretos, "_contar_paises_jugador", return_value=30
        ):
            resultado = self.objetivos_secretos.verificar_condicion_victoria(
                jugador, mock_mapa, Mock()
            )
            self.assertTrue(resultado)

        # Simular que el jugador tiene menos de 30 países
        with patch.object(
            self.objetivos_secretos, "_contar_paises_jugador", return_value=25
        ):
            resultado = self.objetivos_secretos.verificar_condicion_victoria(
                jugador, mock_mapa, Mock()
            )
            self.assertFalse(resultado)

    def test_verificar_condicion_victoria_destruir_jugador(self) -> None:
        """Test de verificación de victoria por destruir jugador."""
        jugador = "test_player"
        self.objetivos_secretos.objetivos_asignados[jugador] = "obj_2"

        mock_mapa: dict[str, list[object]] = {}
        mock_colores = Mock()
        mock_colores.dame_clientes.return_value = ["jugador_rojo", "test_player"]
        mock_colores.get_color_name.side_effect = lambda x: (
            "rojo" if x == "jugador_rojo" else "azul"
        )
        mock_colores.get_color_name_by_client_id.return_value = "azul"

        # Jugador rojo eliminado (no tiene países)
        resultado = self.objetivos_secretos.verificar_condicion_victoria(
            jugador, mock_mapa, mock_colores
        )
        self.assertTrue(resultado)

    def test_verificar_condicion_victoria_conquistar_continentes(self) -> None:
        """Test de verificación de victoria por conquista de continentes."""
        jugador = "test_player"

        # Crear mock de jugador
        mock_jugador = Mock()
        mock_jugador.userid.return_value = jugador

        # Agregar objetivo de conquistar continentes a los datos
        objetivo_continentes: dict[str, object] = {
            "id": "obj_3",
            "tipo": "conquistar_continentes",
            "descripcion": "Conquistar America del Norte y Africa",
            "continentes": ["America del Norte", "Africa"],
        }
        self.objetivos_data["obj_3"] = objetivo_continentes
        self.objetivos_secretos.objetivos_asignados[jugador] = "obj_3"

        # Mock del mapa donde el jugador controla todos los países de ambos continentes
        mock_mapa: dict[str, list[object]] = {
            "usa": ["America del Norte", "coords", mock_jugador, 1],
            "canada": ["America del Norte", "coords", mock_jugador, 1],
            "mexico": ["America del Norte", "coords", mock_jugador, 1],
            "egipto": ["Africa", "coords", mock_jugador, 1],
            "sudafrica": ["Africa", "coords", mock_jugador, 2],
            "nigeria": ["Africa", "coords", mock_jugador, 1],
        }

        # Mock get_paises para cada continente
        def mock_get_paises(continente: str) -> list[str]:
            if continente == "America del Norte":
                return ["usa", "canada", "mexico"]
            if continente == "Africa":
                return ["egipto", "sudafrica", "nigeria"]
            return []

        self.mock_toml_reader.get_paises.side_effect = mock_get_paises

        resultado = self.objetivos_secretos.verificar_condicion_victoria(
            jugador, mock_mapa, Mock()
        )
        self.assertTrue(resultado)

    def test_contar_paises_jugador(self) -> None:
        """Test del conteo de países de un jugador."""
        jugador = "test_player"

        # Crear mocks de jugadores con método userid()
        mock_jugador = Mock()
        mock_jugador.userid.return_value = jugador

        mock_otro_jugador = Mock()
        mock_otro_jugador.userid.return_value = "otro_jugador"

        mock_mapa = {
            "pais1": ["continente1", "coords", mock_jugador, 1],
            "pais2": ["continente1", "coords", mock_jugador, 2],
            "pais3": ["continente2", "coords", mock_otro_jugador, 1],
        }

        count = self.objetivos_secretos._contar_paises_jugador(jugador, mock_mapa)  # noqa: SLF001
        self.assertEqual(count, 2)

    def test_sin_objetivo_asignado(self) -> None:
        """Test cuando un jugador no tiene objetivo asignado."""
        jugador = "test_player"

        resultado = self.objetivos_secretos.verificar_condicion_victoria(
            jugador, {}, Mock()
        )
        self.assertFalse(resultado)


if __name__ == "__main__":
    unittest.main()
