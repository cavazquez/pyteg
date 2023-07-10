from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (QGraphicsPixmapItem, QGraphicsScene,
                               QGraphicsView, QMainWindow)

from read_toml import ReadToml


# Only needed for access to command line arguments
# import sys

# You need one (and only one) QApplication instance per application.
# Pass in sys.argv to allow command line arguments for your app.
# If you know you won't use command line arguments QApplication([]) works too.

class Gui(QMainWindow):
    def __init__(self):
        QMainWindow.__init__(self, parent=None)
        # window = QMainWindow()
        self.setWindowTitle("PyTeg")
        self.scene = QGraphicsScene()
        folder = "themes/"

        reader = ReadToml()
        for continente in reader.get_continentes():
            cor = reader.coordenadas_continente(continente)
            print(cor)
            for pais in reader.get_paises(continente):
                print(pais)
                pixmap = QPixmap(folder + reader.img_path(pais, continente))
                graphicsPixmapItem = QGraphicsPixmapItem(pixmap)
                pos_x, pos_y, _, _ = reader.coordenadas(pais, continente)
                print(pos_x, pos_y)
                graphicsPixmapItem.setPos(cor[0] + pos_x, cor[1] + pos_y)
                self.scene.addItem(graphicsPixmapItem)

        # Create QGraphicsView
        self.view = QGraphicsView(self.scene)
        self.view.show()
        
        self.setCentralWidget(self.view)

        #self.setFixedSize(QSize(1024, 768))

        #self.show()  # IMPORTANT!!!!! Windows are hidden by default.

    def update(self, lista_jugadores):
        print("lista_jugadores:", lista_jugadores)
        for i in range(len(lista_jugadores)):
            self._jugadores[i].insert(f"{lista_jugadores[i]}")
