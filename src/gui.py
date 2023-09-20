from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QAction, QBrush, QColor, QFont, QIntValidator, QPen, QPixmap
from PySide6.QtWidgets import (
    QGraphicsEllipseItem,
    QGraphicsPixmapItem,
    QGraphicsScene,
    QGraphicsTextItem,
    QGraphicsView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
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

    def __init__(self, client):
        self.client = client
        super().__init__()
        layout = QVBoxLayout()
        self.setWindowTitle("Conectar")
        self.setFixedSize(QSize(300, 150))
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowMinimizeButtonHint)
        label_addr = QLabel("Direccion")
        addr = QLineEdit("localhost")
        label_port = QLabel("Puerto")
        port = QLineEdit("65432")
        port.setValidator(QIntValidator())
        button_conectar = QPushButton("Conectar")
        button_conectar.clicked.connect(self.connect)
        layout.addWidget(label_addr)
        layout.addWidget(addr)
        layout.addWidget(label_port)
        layout.addWidget(port)
        layout.addWidget(button_conectar)
        self.setLayout(layout)

    def connect(self):
        try:
            self.client.conectar()
            self.close()
        except ConnectionRefusedError:
            msgBox = QMessageBox()
            msgBox.setWindowTitle("Advertencia")
            msgBox.setIcon(QMessageBox.Warning)
            msgBox.setText("Conexión rehusada.")
            msgBox.setModal(True)
            msgBox.exec()


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

    def mouseMoveEvent(self, event):
        x = event.x()
        y = event.y()
        self.statusBar().showMessage(f"Coordenadas: ({x}, {y})")

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

        with open("src/paises.toml") as fs:
            reader = TomlReader(fs.read())

        for continente in reader.get_continentes():
            cor_x, cor_y = reader.coordenadas_continente(continente)
            for pais in reader.get_paises(continente):
                # Paises
                print(pais)
                pixmap = QPixmap(folder + reader.img_path(pais))
                graphicsPixmapItem = QGraphicsPixmapItem(pixmap)
                pos_x, pos_y, army_x, army_y = reader.coordenadas(pais)
                graphicsPixmapItem.setPos(cor_x + pos_x, cor_y + pos_y)
                print(cor_x + pos_x, cor_y + pos_y)
                self.scene.addItem(graphicsPixmapItem)

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
                print(center_x, center_y)

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

    def closeEvent(self, event):
        self._vivo = False
        print(event)
        self.client.cerrar()
        print("Aceptando Evento")
        event.accept()
