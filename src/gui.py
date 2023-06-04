from PySide6.QtWidgets import QWidget, QPushButton, QMainWindow, QRadioButton, QVBoxLayout, QLineEdit, QGridLayout, QLabel, QGraphicsView
from PySide6.QtGui import QPixmap, QPainter
from PySide6.QtCore import QSize, QRect

from xyz import XYZ

# Only needed for access to command line arguments
#import sys

# You need one (and only one) QApplication instance per application.
# Pass in sys.argv to allow command line arguments for your app.
# If you know you won't use command line arguments QApplication([]) works too.

class Gui(QMainWindow):

    def __init__(self):
        QMainWindow.__init__(self, parent=None)
        #window = QMainWindow()
        self.setWindowTitle("PyTeg")

        #print(XYZ().paises())
        VMap = QVBoxLayout()

        pixmap = QPixmap('themes/classic/argentina.png')
        #label = QLabel(self)
        #label.setPixmap(pixmap)
        #label.move(2000,2000)
        #VMap.addWidget(label)
        #self.resize(pixmap.width(), pixmap.height())

        graphics = QGraphicsView()
        graphics.addPixmap(pixmap)


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

        self.setFixedSize(QSize(1024, 768))

        self.show()  # IMPORTANT!!!!! Windows are hidden by default.

    def update(self, lista_jugadores):
        print("lista_jugadores:",  lista_jugadores)
        for i in range(len(lista_jugadores)):
            self._jugadores[i].insert(f"{lista_jugadores[i]}")



