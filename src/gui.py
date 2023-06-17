from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (QGraphicsPixmapItem, QGraphicsScene,
                               QGraphicsView, QMainWindow)

from xyz import XYZ


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

        XYZ()

        pixmap = QPixmap("themes/classic/argentina.png")
        pixmap_br = QPixmap("themes/classic/brasil.png")
        pixmap_uy = QPixmap("themes/classic/uruguay.png")

        # Create QGraphicsPixmapItem
        graphicsPixmapItem = QGraphicsPixmapItem(pixmap)
        graphicsPixmapItem.setPos(31,68)
        graphicsPixmapItem_br = QGraphicsPixmapItem(pixmap_br)
        graphicsPixmapItem_br.setPos(30,8)
        graphicsPixmapItem_uy = QGraphicsPixmapItem(pixmap_uy)
        graphicsPixmapItem_uy.setPos(51,54)

        # Create QGraphicsScene
        self.scene = QGraphicsScene()
        self.scene.addItem(graphicsPixmapItem)
        self.scene.addItem(graphicsPixmapItem_br)
        self.scene.addItem(graphicsPixmapItem_uy)

        # Create QGraphicsView
        self.view = QGraphicsView(self.scene)

        # Create QVBoxLayout
        #VMap = QVBoxLayout()
        #VMap.addWidget(view)

        self.view.setWindowTitle("Line Drawing Example")
        self.view.resize(800, 800)

        self.view.show()
        
        self.setCentralWidget(self.view)

        #self.setFixedSize(QSize(1024, 768))

        #self.show()  # IMPORTANT!!!!! Windows are hidden by default.

    def update(self, lista_jugadores):
        print("lista_jugadores:", lista_jugadores)
        for i in range(len(lista_jugadores)):
            self._jugadores[i].insert(f"{lista_jugadores[i]}")
