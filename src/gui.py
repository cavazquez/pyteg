from PySide6.QtWidgets import QApplication, QWidget, QPushButton, QMainWindow, QRadioButton, QVBoxLayout, QLineEdit, QGridLayout
from PySide6.QtCore import QSize

# Only needed for access to command line arguments
import sys

# You need one (and only one) QApplication instance per application.
# Pass in sys.argv to allow command line arguments for your app.
# If you know you won't use command line arguments QApplication([]) works too.

class Gui(QMainWindow):

    def __init__(self):
        QMainWindow.__init__(self, parent=None)
        #window = QMainWindow()
        self.setWindowTitle("PyTeg")


        VMap = QVBoxLayout()
        test_jugador = QLineEdit()
        VMap.addWidget(test_jugador)

        Vlayout = QVBoxLayout()
        self._jugadores = []
        for i in range(0,6):
            jugador = QLineEdit()
            jugador.setReadOnly(True)
            self._jugadores.append(jugador)
            Vlayout.addWidget(jugador)

        grid_layout = QGridLayout()
        grid_layout.addLayout(VMap, 0 , 0)
        grid_layout.addLayout(Vlayout, 0 , 1)
        grid_layout.setColumnStretch(0, 4)
        grid_layout.setColumnStretch(1, 1)

        container = QWidget()
        container.setLayout(grid_layout)

        self.setCentralWidget(container)

        #window.setFixedSize(QSize(800, 600))
        self.setFixedSize(QSize(1024, 768))

        self.show()  # IMPORTANT!!!!! Windows are hidden by default.

    def update(self, text):
        self._jugadores[0].insert(text)


app = QApplication()
gui = Gui()
gui.update("Hola")

app.exec()

