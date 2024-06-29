from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QBrush, QColor, QFont, QMouseEvent, QPen, QPixmap
from PySide6.QtWidgets import (
    QGraphicsEllipseItem,
    QGraphicsPixmapItem,
    QGraphicsScene,
    QGraphicsTextItem,
)

from src.toml_reader import TomlReader


class QCustomGraphicsScene(QGraphicsScene):
    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        self.load_map_data(main_window)

    def mouseMoveEvent(self, event: QMouseEvent):  # noqa: N802
        # Obtener las coordenadas del mouse en la escena
        scene_pos = event.scenePos()
        self.main_window.update_status_bar(
            f"Coordenadas: ({scene_pos.x()}, {scene_pos.y()})",
        )
        # Llamar al evento original
        super().mouseMoveEvent(event)

    def leaveEvent(self, event: QMouseEvent):  # noqa: N802
        self.main_window.clear_status_bar()
        super().leaveEvent(event)

    def load_map_data(self, main_window):
        folder = "themes/"

        reader = TomlReader(
            Path("themes/test/paises.toml").read_text(encoding="locale"),
        )

        for continente in reader.get_continentes():
            cor_x, cor_y = reader.coordenadas_continente(continente)
            for pais in reader.get_paises(continente):

                main_window.unidades.update({pais: 1})
                main_window.continente.update({pais: continente})
                # Paises
                pixmap = QPixmap(folder + reader.img_path(pais))
                graphics_pixmap_item = QGraphicsPixmapItem(pixmap)
                pos_x, pos_y, army_x, army_y = reader.coordenadas(pais)
                graphics_pixmap_item.setPos(cor_x + pos_x, cor_y + pos_y)
                # print(cor_x + pos_x, cor_y + pos_y)
                self.addItem(graphics_pixmap_item)

                # Circulos en paises
                # Crear un objeto círculo
                pos_x_abs = cor_x + pos_x + army_x
                pos_y_abs = cor_y + pos_y + army_y

                circle = QGraphicsEllipseItem(pos_x_abs, pos_y_abs, 30, 30)
                # (x, y, width, height)

                # Establecer el color del borde y del relleno del círculo
                pen = QPen(Qt.blue)
                brush = QBrush(QColor(0, 255, 0))  # Color verde
                circle.setPen(pen)
                circle.setBrush(brush)

                # Agregar el círculo a la escena
                self.addItem(circle)

                # Calcular el centro del círculo
                center_x = circle.rect().center().x()
                center_y = circle.rect().center().y()
                # print(center_x, center_y)

                center_text = QGraphicsTextItem("1")
                center_text.setFont(QFont("Helvetica [Cronyx]", 14))
                center_text.setPos(center_x - 8, center_y - 12)
                main_window.circulo.update({pais: center_text})
                self.addItem(center_text)
