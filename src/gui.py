from PySide6.QtCore import QSize
from PySide6.QtGui import QAction, QPixmap
from PySide6.QtWidgets import (
    QGraphicsPixmapItem,
    QGraphicsScene,
    QGraphicsView,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QTextEdit,
    QToolBar,
    QVBoxLayout,
    QWidget,
)
from toml_reader import TomlReader


class Gui(QMainWindow):
    def __init__(self):
        # QMainWindow.__init__(self, parent=None)
        super().__init__()
        self.setWindowTitle("PyTeg")
        self.setFixedSize(QSize(1024, 768))

        self.setup_graphics_view()
        self.load_map_data()

        self.show()  # IMPORTANT!!!!! Windows are hidden by default.

    def setup_graphics_view(self):
        input_layout = QVBoxLayout()

        self.input_field = QLineEdit()
        self.text_field = QTextEdit()
        self.text_field.setReadOnly(True)
        self.text_field.setMaximumSize(1024, 100)
        self.text_field.setMinimumSize(1024, 20)
        self.send_button = QPushButton("Enviar")
        self.send_button.clicked.connect(self.send_message)

        input_layout.addWidget(self.text_field)
        input_layout.addWidget(self.input_field)
        input_layout.addWidget(self.send_button)

        toolbar = QToolBar("My main toolbar")
        self.addToolBar(toolbar)
        button_action = QAction("Your button", self)
        toolbar.addAction(button_action)

        self.scene = QGraphicsScene()
        self.view = QGraphicsView(self.scene)

        # Create a widget to hold the QGraphicsView and input area
        main_widget = QWidget(self)
        main_layout = QVBoxLayout()
        main_layout.addWidget(self.view)
        main_layout.addLayout(input_layout)
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)
        self.view.show()

    def load_map_data(self):
        folder = "themes/"

        with open("src/paises.toml") as fs:
            reader = TomlReader(fs.read())

        for continente in reader.get_continentes():
            cor = reader.coordenadas_continente(continente)
            for pais in reader.get_paises(continente):
                pixmap = QPixmap(folder + reader.img_path(pais))
                graphicsPixmapItem = QGraphicsPixmapItem(pixmap)
                pos_x, pos_y, _, _ = reader.coordenadas(pais)
                graphicsPixmapItem.setPos(cor[0] + pos_x, cor[1] + pos_y)
                self.scene.addItem(graphicsPixmapItem)

            for pais in reader.get_paises(continente):
                pass

    def send_message(self):
        self.text_field.append(self.input_field.text())
        self.input_field.clear()
