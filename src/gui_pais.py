from PySide6.QtGui import (
    QPixmap,
)


class Pais(QPixmap):

    def __init__(self, path, nombre):
        super().__init__(path)
        self._nombre = nombre
