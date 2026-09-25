"""Regresiones para conexiones visuales opcionales de los temas."""

# ruff: noqa: D102

from __future__ import annotations

import unittest
from types import SimpleNamespace
from typing import cast

from PySide6.QtCore import QPointF, Qt
from PySide6.QtWidgets import QApplication, QGraphicsPathItem

from pyteg.gui.mapa.overlap_check import load_pais_bounds, paises_en_punto
from pyteg.gui.mapa.scene import QCustomGraphicsScene
from pyteg.toml_reader import TomlReader, TomlReaderError

EXPECTED_CLASSIC_VISUAL_CONNECTIONS = {
    ("Alaska", "Kamchatka"),
    ("Australia", "Borneo"),
    ("Australia", "Java"),
    ("Australia", "Sumatra"),
    ("Brasil", "Sahara"),
    ("Chile", "Australia"),
    ("China", "Japon"),
    ("Colombia", "Mexico"),
    ("Egipto", "Israel"),
    ("Egipto", "Polonia"),
    ("Egipto", "Turquia"),
    ("Espana", "Sahara"),
    ("GranBretana", "Espana"),
    ("GranBretana", "Alemania"),
    ("GranBretana", "Islandia"),
    ("Groenlandia", "Islandia"),
    ("Islandia", "Suecia"),
    ("India", "Sumatra"),
    ("Japon", "Kamchatka"),
    ("Labrador", "Groenlandia"),
    ("Malasia", "Borneo"),
    ("Madagascar", "Egipto"),
    ("Madagascar", "Zaire"),
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

    def test_carga_conexion_que_envuelve_el_mapa(self) -> None:
        reader = TomlReader(
            self._paises(),
            adyacencias_toml_string=self._adyacencias(
                """
                [[ConexionesVisuales]]
                origen = "A"
                destino = "B"
                envolver = "horizontal"
                puntos = [[0, 20], [640, 30]]
                """
            ),
        )

        connection = reader.get_conexiones_visuales()[0]
        self.assertEqual(connection.envolver, "horizontal")
        self.assertEqual(connection.puntos, ((0.0, 20.0), (640.0, 30.0)))

    def test_rechaza_envolver_horizontal_sin_dos_puntos(self) -> None:
        with self.assertRaisesRegex(TomlReaderError, "dos puntos"):
            TomlReader(
                self._paises(),
                adyacencias_toml_string=self._adyacencias(
                    """
                    [[ConexionesVisuales]]
                    origen = "A"
                    destino = "B"
                    envolver = "horizontal"
                    puntos = [[0, 20]]
                    """
                ),
            )

    def test_rechaza_bordes_de_wrap_fuera_de_orden(self) -> None:
        with self.assertRaisesRegex(TomlReaderError, "borde izquierdo"):
            TomlReader(
                self._paises(),
                adyacencias_toml_string=self._adyacencias(
                    """
                    [[ConexionesVisuales]]
                    origen = "A"
                    destino = "B"
                    envolver = "horizontal"
                    puntos = [[640, 20], [0, 30]]
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

    def test_conexiones_que_envuelven_no_cruzan_el_mapa(self) -> None:
        reader = TomlReader.from_theme("classic", strict=True)
        scene = QCustomGraphicsScene(SimpleNamespace(), theme="classic")
        routes = dict(
            zip(reader.get_conexiones_visuales(), scene.visual_connections, strict=True)
        )
        wrapped = {
            (connection.origen, connection.destino): item.path()
            for connection, item in routes.items()
            if connection.envolver == "horizontal"
        }

        self.assertEqual(
            set(wrapped),
            {("Alaska", "Kamchatka"), ("Chile", "Australia")},
        )
        for connection, item in routes.items():
            if connection.envolver != "horizontal":
                continue
            path = item.path()
            self.assertEqual(path.elementCount(), 4)
            self.assertEqual(
                path.elementAt(2).type,
                path.ElementType.MoveToElement,
            )
            self.assertEqual(path.elementAt(1).x, 0.0)
            self.assertEqual(path.elementAt(2).x, 640.0)
            arrows = [
                child.path()
                for child in item.childItems()
                if isinstance(child, QGraphicsPathItem)
            ]
            self.assertEqual(
                {(arrow.elementAt(0).x, arrow.elementAt(1).x) for arrow in arrows},
                {(0.0, 6.0), (634.0, 640.0)},
            )

    def test_rutas_empiezan_y_terminan_en_el_contorno_del_pais(self) -> None:
        reader = TomlReader.from_theme("classic", strict=True)
        scene = QCustomGraphicsScene(SimpleNamespace(), theme="classic")

        for config, route in zip(
            reader.get_conexiones_visuales(), scene.visual_connections, strict=True
        ):
            with self.subTest(origen=config.origen, destino=config.destino):
                path = route.path()
                start = path.elementAt(0)
                end = path.elementAt(path.elementCount() - 1)
                for country_name, point in (
                    (config.origen, (start.x, start.y)),
                    (config.destino, (end.x, end.y)),
                ):
                    country = scene.paises[country_name]
                    anchor = country.mapFromScene(QPointF(*point))
                    self.assertFalse(country.shape().contains(anchor))
                    self.assertGreater(
                        (
                            country.mapToScene(country.boundingRect().center()) - anchor
                        ).manhattanLength(),
                        1,
                    )

    def test_descarta_waypoints_ocultos_dentro_del_pais_de_origen(self) -> None:
        reader = TomlReader.from_theme("classic", strict=True)
        scene = QCustomGraphicsScene(SimpleNamespace(), theme="classic")
        route_configs = reader.get_conexiones_visuales()
        index = next(
            i
            for i, connection in enumerate(route_configs)
            if (connection.origen, connection.destino) == ("NuevaYork", "Groenlandia")
        )
        config = route_configs[index]
        path = scene.visual_connections[index].path()
        origin = scene.paises[config.origen]
        hidden_waypoint = QPointF(*config.puntos[0])

        self.assertTrue(origin.shape().contains(origin.mapFromScene(hidden_waypoint)))
        self.assertEqual(path.elementCount(), 3)
        self.assertNotIn(
            (hidden_waypoint.x(), hidden_waypoint.y()),
            [
                (path.elementAt(i).x, path.elementAt(i).y)
                for i in range(path.elementCount())
            ],
        )

    def test_seleccion_cerca_de_las_costas_sigue_eligiendo_el_pais(self) -> None:
        host = SimpleNamespace(
            scene=None,
            update_status_bar=lambda *_args: None,
            clear_status_bar=lambda: None,
        )
        scene = QCustomGraphicsScene(host, theme="classic")
        host.scene = scene
        reader = TomlReader.from_theme("classic", strict=True)
        bounds = load_pais_bounds("classic")

        for config, route in zip(
            reader.get_conexiones_visuales(), scene.visual_connections, strict=True
        ):
            path = route.path()
            first = path.elementAt(0)
            last = path.elementAt(path.elementCount() - 1)
            for country_name, point in (
                (config.origen, QPointF(first.x, first.y)),
                (config.destino, QPointF(last.x, last.y)),
            ):
                with self.subTest(origen=config.origen, pais=country_name):
                    country = scene.paises[country_name]
                    center = country.mapToScene(country.boundingRect().center())
                    dx, dy = center.x() - point.x(), center.y() - point.y()
                    distance = (dx**2 + dy**2) ** 0.5
                    candidate = None
                    for step in range(1, 13):
                        offset = step * 0.5 / distance
                        probe = QPointF(
                            point.x() + dx * offset, point.y() + dy * offset
                        )
                        if paises_en_punto(bounds, probe.x(), probe.y()) == [
                            country_name
                        ]:
                            candidate = probe
                            break
                    if candidate is None:
                        self.fail(
                            "No se encontró un punto seleccionable junto al ancla"
                        )
                    scene.selection_manager.cancelar_seleccion()
                    self.assertTrue(scene.handle_country_click(candidate))
                    self.assertEqual(
                        scene.selection_manager.get_pais_origen(), country_name
                    )


if __name__ == "__main__":
    unittest.main()
