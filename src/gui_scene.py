from PySide6.QtCore import Qt
from PySide6.QtGui import (
    QBrush,
    QColor,
    QMouseEvent,
)
from PySide6.QtWidgets import (
    QGraphicsPixmapItem,
    QGraphicsScene,
)

from src.gui_menu import Menu
from src.gui_pais import Pais
from src.gui_toolbar import ToolBar
from src.toml_reader import TomlReader
from src.utils import get_resource_path


class CountrySelectionManager:
    """Maneja la selección de países origen y destino"""

    def __init__(self, main_window, scene):
        self.main_window = main_window
        self.scene = scene
        self._pais_origen = None
        self._pais_destino = None
        self._pais_origen_widget = None
        self._pais_destino_widget = None

    def seleccionar_pais(self, nombre_pais):
        """Selecciona un país como origen o destino"""
        if self._pais_origen is None:
            # Primer clic: seleccionar como origen
            self._pais_origen = nombre_pais
            self._pais_origen_widget = self.scene.paises.get(nombre_pais)
            if self._pais_origen_widget:
                self._pais_origen_widget.set_seleccion_visual("origen")
            self._actualizar_seleccion_label()
        elif self._pais_origen == nombre_pais:
            # Clic en el mismo país origen: cancelar selección
            self.cancelar_seleccion()
        elif self._pais_destino is None:
            # Segundo clic: seleccionar como destino
            self._pais_destino = nombre_pais
            self._pais_destino_widget = self.scene.paises.get(nombre_pais)
            if self._pais_destino_widget:
                self._pais_destino_widget.set_seleccion_visual("destino")
            self._actualizar_seleccion_label()
        else:
            # Ya hay origen y destino: reiniciar selección con nuevo origen
            self.cancelar_seleccion()
            self.seleccionar_pais(nombre_pais)

    def cancelar_seleccion(self):
        """Cancela la selección actual de países"""
        if self._pais_origen_widget:
            self._pais_origen_widget.limpiar_seleccion_visual()
        if self._pais_destino_widget:
            self._pais_destino_widget.limpiar_seleccion_visual()

        self._pais_origen = None
        self._pais_destino = None
        self._pais_origen_widget = None
        self._pais_destino_widget = None
        self._actualizar_seleccion_label()

    def confirmar_seleccion(self):
        """Confirma la selección y ejecuta movimiento (acción por defecto)"""
        if (
            self._pais_origen
            and self._pais_destino
            and hasattr(self.main_window, "transmisor")
            and self.main_window.transmisor
        ):
            # Ejecutar movimiento de unidades como acción por defecto
            self.main_window.transmisor.mover_unidad(
                origen=self._pais_origen, destino=self._pais_destino, cantidad=1
            )
            # Mostrar mensaje en la barra de estado
            self.main_window.status_bar.showMessage(
                f"Moviendo 1 unidad de {self._pais_origen} a {self._pais_destino}",
                3000,  # 3 segundos
            )
            # Cancelar selección después de la acción
            self.cancelar_seleccion()

    def _actualizar_seleccion_label(self):
        """Actualiza el label de selección en la barra de estado"""
        if hasattr(self.main_window, "seleccion_label"):
            if self._pais_origen is None:
                self.main_window.seleccion_label.setText(
                    "Selección: Haz clic en un país para seleccionar origen"
                )
            elif self._pais_destino is None:
                self.main_window.seleccion_label.setText(
                    f"Origen: {self._pais_origen} | Haz clic en otro país para destino"
                )
            else:
                self.main_window.seleccion_label.setText(
                    f"Origen: {self._pais_origen} | Destino: {self._pais_destino} | "
                    f"Clic derecho: Atacar/Mover"
                )

        # Notificar a la toolbar sobre el cambio de selección
        self._actualizar_botones_toolbar()

    def get_pais_origen(self):
        """Retorna el país origen seleccionado"""
        return self._pais_origen

    def get_pais_destino(self):
        """Retorna el país destino seleccionado"""
        return self._pais_destino

    def _actualizar_botones_toolbar(self):
        """Actualiza el estado de los botones de atacar y mover en la toolbar"""
        hay_dos_paises = (
            self._pais_origen is not None and self._pais_destino is not None
        )

        # Buscar la toolbar en la ventana principal
        if hasattr(self.main_window, "findChildren"):
            toolbars = self.main_window.findChildren(ToolBar)
            for toolbar in toolbars:
                if hasattr(toolbar, "actualizar_botones_seleccion"):
                    toolbar.actualizar_botones_seleccion(hay_dos_paises)


class QCustomGraphicsScene(QGraphicsScene):
    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        self.paises = {}
        # Configurar fondo celeste que representa el agua/océano
        self.setBackgroundBrush(QBrush(QColor("#87CEEB")))  # Sky Blue / Celeste suave
        # Crear el manejador de selección de países
        self.selection_manager = CountrySelectionManager(main_window, self)
        self.load_map_data()

    def mouseMoveEvent(self, event: QMouseEvent):  # noqa: N802
        # Obtener las coordenadas del mouse en la escena
        # Mostrar las coordenadas en el Status Bar
        scene_pos = event.scenePos()
        self.main_window.update_status_bar(
            f"Coordenadas: ({scene_pos.x()}, {scene_pos.y()})",
        )
        # Llamar al evento original
        super().mouseMoveEvent(event)

    def leaveEvent(self, event: QMouseEvent):  # noqa: N802
        self.main_window.clear_status_bar()
        super().leaveEvent(event)

    def mousePressEvent(self, event):  # noqa: N802
        """Maneja los clics del mouse en la escena"""
        if event.button() == Qt.LeftButton:
            # Verificar si se hizo clic en un área vacía (sin países)
            items = self.items(event.scenePos())
            pais_clicked = False

            for item in items:
                if isinstance(item, QGraphicsPixmapItem) and hasattr(item, "nombre"):
                    pais_clicked = True
                    break

            # Si no se hizo clic en un país, cancelar todas las selecciones
            if not pais_clicked:
                self.selection_manager.cancelar_seleccion()

        # Llamar al evento original para mantener funcionalidad existente
        super().mousePressEvent(event)

    def contextMenuEvent(self, event):  # noqa: N802
        # Verificar si se hizo clic derecho sobre el QGraphicsPixmapItem
        items = self.items(event.scenePos())
        for item in items:
            if isinstance(item, QGraphicsPixmapItem):
                pais = item.nombre()
                # Pasar explícitamente la ventana principal como padre para Wayland
                menu = Menu(pais, self.main_window, parent=self.main_window)
                menu.exec_(event.screenPos())

    def load_map_data(self):
        folder = "themes/"

        paises_content = get_resource_path("themes/classic/paises.toml").read_text(
            encoding="utf-8"
        )
        cartas_content = get_resource_path("themes/classic/cartas.toml").read_text(
            encoding="utf-8"
        )
        adyacencias_content = get_resource_path(
            "themes/classic/adyacencias.toml"
        ).read_text(encoding="utf-8")
        reader = TomlReader(paises_content, cartas_content, adyacencias_content)

        for continente in reader.get_continentes():
            cor_x, cor_y = reader.coordenadas_continente(continente)
            for pais in reader.get_paises(continente):
                # Paises
                pos_x, pos_y, army_x, army_y = reader.coordenadas(pais)
                x = cor_x + pos_x
                y = cor_y + pos_y
                abs_img_path = str(get_resource_path(folder + reader.img_path(pais)))
                pixmap_item = Pais(
                    abs_img_path,
                    (pais, continente),
                    (x, y, army_x, army_y),
                )
                # Establecer la referencia a la ventana principal
                pixmap_item.set_main_window(self.main_window)
                self.paises[pais] = pixmap_item
                self.addItem(pixmap_item)

    def obtener_pais(self, nombre_pais):
        """Retorna el widget del país especificado.

        Args:
            nombre_pais (str): Nombre del país a buscar

        Returns:
            Pais | None: Widget del país o None si no existe
        """
        return self.paises.get(nombre_pais)
