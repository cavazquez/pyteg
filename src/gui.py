from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QAction, QIntValidator, QPixmap
from PySide6.QtWidgets import (
    QGraphicsPixmapItem,
    QGraphicsScene,
    QGraphicsView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QTextEdit,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from src.toml_reader import TomlReader


class VentanaConectar(QWidget):
    """
    This "window" is a QWidget. If it has no parent, it
    will appear as a free-floating window as we want.
    """

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        self.setWindowTitle("Conectar")
        self.setFixedSize(QSize(300, 150))
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowMinimizeButtonHint)
        label_addr = QLabel("Direccion")
        addr = QLineEdit()
        label_port = QLabel("Puerto")
        port = QLineEdit()
        port.setValidator(QIntValidator())
        buton_conectar = QPushButton("Conectar")
        layout.addWidget(label_addr)
        layout.addWidget(addr)
        layout.addWidget(label_port)
        layout.addWidget(port)
        layout.addWidget(buton_conectar)
        self.setLayout(layout)


class Gui(QMainWindow):
    def __init__(self):
        super().__init__()
        self.w = None
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
        button_conectar = QAction("Conectar", self)
        button_conectar.triggered.connect(self.ventana_conectar)
        toolbar.addAction(button_conectar)

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

    def ventana_conectar(self):
        self.w = None
        self.w = VentanaConectar()
        self.w.show()

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
