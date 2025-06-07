from PySide6.QtGui import QColor


class Colores:
    def __init__(self):
        self._colores = [
            QColor(255, 0, 0),    # Rojo
            QColor(0, 255, 0),    # Verde
            QColor(0, 0, 255),    # Azul
            QColor(255, 255, 0),  # Amarillo
            QColor(0, 255, 255),  # Cian
            QColor(255, 0, 255),  # Magenta
            QColor(0, 0, 0),      # Negro
            QColor(255, 255, 255),  # Blanco
        ]
        self._asignacion = {}

    def agregar_color(self, color):
        self._colores.append(color)

    def asignar(self, cliente, color):
        if isinstance(color, dict):
            # Si el color es un diccionario, extraer los valores r, g, b
            r = color.get("r", 0)
            g = color.get("g", 0)
            b = color.get("b", 0)
            color_qcolor = QColor(r, g, b)
        else:
            # Si ya es un QColor, usarlo directamente
            color_qcolor = color

        self._asignacion[cliente] = color_qcolor

    def colores(self):
        return self._colores

    def colores_asignados(self):
        return self._asignacion

    def color_asignado(self, cliente):
        """
        Obtiene el color asignado al cliente.

        :param cliente: ID del cliente
        :return: QColor asignado al cliente, o QColor(128, 128, 128) si no se encuentra
        """
        return self._asignacion.get(cliente, QColor(128, 128, 128))

    def __str__(self):
        colores = ", ".join(str(color.getRgb()) for color in self._colores)
        asignacion = "\n".join(
            f"{clave}: {valor.getRgb()}" for clave, valor in self._asignacion.items()
        )
        return f"""Colores:
        {colores}
        Asignacion:
        {asignacion}
        """
