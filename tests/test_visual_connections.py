"""Regresiones para conexiones visuales opcionales de los temas."""

# ruff: noqa: D102

from __future__ import annotations

import unittest
from types import SimpleNamespace
from typing import cast

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from pyteg.gui.mapa.scene import QCustomGraphicsScene
from pyteg.toml_reader import TomlReader, TomlReaderError

EXPECTED_CLASSIC_VISUAL_CONNECTIONS = {
    ("Alaska", "Kamchatka"),
    ("Australia", "Borneo"),
    ("Australia", "Java"),
    ("Australia", "Sumatra"),
    ("Brasil", "Sahara"),
    ("Chile", "Australia"),
    ("Colombia", "Mexico"),
    ("Egipto", "Israel"),
    ("Egipto", "Polonia"),
    ("Egipto", "Turquia"),
    ("Espana", "Sahara"),
    ("GranBretana", "Espana"),
    ("GranBretana", "Islandia"),
    ("Groenlandia", "Islandia"),
    ("India", "Sumatra"),
    ("Japon", "Kamchatka"),
    ("Labrador", "Groenlandia"),
    ("Malasia", "Borneo"),
    ("NuevaYork", "Groenlandia"),
    ("Polonia", "Turquia"),
    ("Rusia", "Aral"),
    ("Rusia", "Iran"),
    ("Rusia", "Turquia"),
}


class VisualConnectionReaderTests(unittest.TestCase):
    """Valida el esquema TOML de conexiones visuales."""

    def _paises(self) -> str:
        return """
        [Cartas]
        Galeon = "test/galeon.svg"

        [Mapa]
        pos_x = 0
        pos_y = 0

        [Mapa.A]
        continente = "Mapa"

        [Mapa.B]
        continente = "Mapa"

        [Mapa.C]
        continente = "Mapa"
        """

    def _adyacencias(self, visual: str = "") -> str:
        return f"""
        [Adyacencias]
        A = ["B"]
        B = ["A"]
        C = []

        {visual}
        """

    def test_carga_conexion_visual_y_conserva_grafo_de_reglas(self) -> None:
        reader = TomlReader(
            self._paises(),
            adyacencias_toml_string=self._adyacencias(
                """
                [[ConexionesVisuales]]
                origen = "A"
                destino = "B"
                puntos = [[12, -4.5]]
                """
            ),
        )

        connections = reader.get_conexiones_visuales()
        self.assertEqual(len(connections), 1)
        self.assertEqual(connections[0].origen, "A")
        self.assertEqual(connections[0].destino, "B")
        self.assertEqual(connections[0].puntos, ((12.0, -4.5),))
        self.assertEqual(reader.obtener_paises_adyacentes("A"), ["B"])

    def test_tema_clasico_declara_conexiones_maritimas(self) -> None:
        reader = TomlReader.from_theme("classic", strict=True)

        connections = reader.get_conexiones_visuales()
        self.assertEqual(
            {(connection.origen, connection.destino) for connection in connections},
            EXPECTED_CLASSIC_VISUAL_CONNECTIONS,
        )

    def test_rechaza_pais_visual_inexistente(self) -> None:
        with self.assertRaisesRegex(TomlReaderError, "países inexistentes"):
            TomlReader(
                self._paises(),
                adyacencias_toml_string=self._adyacencias(
                    """
                    [[ConexionesVisuales]]
                    origen = "A"
                    destino = "Z"
                    """
                ),
            )

    def test_rechaza_conexion_visual_que_no_es_adyacencia(self) -> None:
        with self.assertRaisesRegex(TomlReaderError, "no corresponde a una adyacencia"):
            TomlReader(
                self._paises(),
                adyacencias_toml_string=self._adyacencias(
                    """
                    [[ConexionesVisuales]]
                    origen = "A"
                    destino = "C"
                    """
                ),
            )

    def test_rechaza_puntos_no_numericos(self) -> None:
        with self.assertRaisesRegex(TomlReaderError, r"debe ser \[x, y\] numérico"):
            TomlReader(
                self._paises(),
                adyacencias_toml_string=self._adyacencias(
                    """
                    [[ConexionesVisuales]]
                    origen = "A"
                    destino = "B"
                    puntos = [["12", 4]]
                    """
                ),
            )


class VisualConnectionSceneTests(unittest.TestCase):
    """Verifica que las conexiones se dibujen detrás de los países."""

    _app: QApplication

    @classmethod
    def setUpClass(cls) -> None:
        existing_app = QApplication.instance()
        cls._app = (
            cast("QApplication", existing_app)
            if existing_app is not None
            else QApplication([])
        )

    def test_escena_dibuja_linea_detras_de_los_paises(self) -> None:
        scene = QCustomGraphicsScene(SimpleNamespace(), theme="test")

        self.assertEqual(len(scene.visual_connections), 1)
        connection = scene.visual_connections[0]
        self.assertEqual(connection.zValue(), -1000.0)
        self.assertEqual(connection.acceptedMouseButtons(), Qt.MouseButton.NoButton)
        self.assertFalse(
            bool(connection.flags() & connection.GraphicsItemFlag.ItemIsSelectable)
        )
        self.assertEqual(connection.path().elementCount(), 3)


if __name__ == "__main__":
    unittest.main()
