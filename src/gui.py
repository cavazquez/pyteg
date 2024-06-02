from pathlib import Path

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QAction, QBrush, QColor, QFont, QPen, QPixmap
from PySide6.QtWidgets import (
    QGraphicsEllipseItem,
    QGraphicsPixmapItem,
    QGraphicsScene,
    QGraphicsTextItem,
    QGraphicsView,
    QMainWindow,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from src.gui_chat import Chat
from src.gui_conectar import VentanaConectar
from src.toml_reader import TomlReader


class Gui(QMainWindow):
    def __init__(self, client):
        super().__init__()
        self._vivo = True
        self.client = client
        self.w = None
        self.setWindowTitle("PyTeg")
        self.setFixedSize(QSize(1024, 768))
        self.setMouseTracking(True)

        self.setup_graphics_view()
        self.load_map_data()
        self.cor_mouse()

        self.show()  # IMPORTANT!!!!! Windows are hidden by default.

    def vivo(self):
        return self._vivo

    def cor_mouse(self):
        self.statusBar().showMessage("Coordenadas: (0, 0)")

    def mouse_move_event(self, event):
        x = event.x()
        y = event.y()
        self.statusBar().showMessage(f"Coordenadas: ({x}, {y})")

    def setup_graphics_view(self):
        input_layout = QVBoxLayout()

        self.chat = Chat(self.client)
        self.chat.show()
        input_layout.addWidget(self.chat)

        toolbar = QToolBar("My main toolbar")
        self.addToolBar(toolbar)
        button_conectar = QAction("Conectar", self)
        button_conectar.triggered.connect(self.ventana_conectar)
        toolbar.addAction(button_conectar)

        self.scene = QGraphicsScene()
        self.view = QGraphicsView(self.scene)

        # Create a widget to hold the QGraphicsView and input area
        self.main_widget = QWidget(self)
        main_layout = QVBoxLayout()
        main_layout.addWidget(self.view)
        main_layout.addLayout(input_layout)
        self.main_widget.setLayout(main_layout)
        self.setCentralWidget(self.main_widget)
        self.view.show()

    def ventana_conectar(self):
        self.w = None
        self.w = VentanaConectar(self.client)
        self.w.show()

    def load_map_data(self):
        folder = "themes/"

        reader = TomlReader(
            Path("themes/classic/paises.toml").read_text(encoding="locale"),
        )

        for continente in reader.get_continentes():
            cor_x, cor_y = reader.coordenadas_continente(continente)
            for pais in reader.get_paises(continente):
                # Paises
                # print(pais)
                pixmap = QPixmap(folder + reader.img_path(pais))
                graphics_pixmap_item = QGraphicsPixmapItem(pixmap)
                pos_x, pos_y, army_x, army_y = reader.coordenadas(pais)
                graphics_pixmap_item.setPos(cor_x + pos_x, cor_y + pos_y)
                # print(cor_x + pos_x, cor_y + pos_y)
                self.scene.addItem(graphics_pixmap_item)

                # Circulos en paises
                # Crear un objeto círculo
                pos_x_abs = cor_x + pos_x + army_x
                pos_y_abs = cor_y + pos_y + army_y

                circle = QGraphicsEllipseItem(pos_x_abs, pos_y_abs, 15, 15)
                # (x, y, width, height)

                # Establecer el color del borde y del relleno del círculo
                pen = QPen(Qt.blue)
                brush = QBrush(QColor(255, 0, 0))  # Color rojo
                circle.setPen(pen)
                circle.setBrush(brush)

                # Agregar el círculo a la escena
                self.scene.addItem(circle)

                # Calcular el centro del círculo
                center_x = circle.rect().center().x()
                center_y = circle.rect().center().y()
                # print(center_x, center_y)

                center_text = QGraphicsTextItem("1")
                center_text.setFont(QFont("Helvetica [Cronyx]", 14))
                center_text.setPos(center_x - 8, center_y - 12)
                self.scene.addItem(center_text)

    def send_message(self):
        text = self.input_field.text()
        if text:
            self.client.send_chat(text)
            self.input_field.clear()

    def msg_chat(self, text):
        self.text_field.append(text)

    def close_event(self, event):
        self._vivo = False
        print(event)
        self.client.cerrar()
        print("Aceptando Evento")
        event.accept()
