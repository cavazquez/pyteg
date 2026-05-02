"""Módulo para gestionar colores en el cliente."""

from __future__ import annotations

from PySide6.QtGui import QColor


class Colores:
    """Gestiona los colores disponibles y asignados a los clientes."""

    def __init__(self) -> None:
        """Inicializa el gestor de colores con la lista de colores disponibles."""
        self._colores: list[QColor] = [
            QColor(255, 0, 0),  # Rojo
            QColor(0, 255, 0),  # Verde
            QColor(0, 0, 255),  # Azul
            QColor(255, 255, 0),  # Amarillo
            QColor(0, 255, 255),  # Cian
            QColor(255, 0, 255),  # Magenta
            QColor(0, 0, 0),  # Negro
            QColor(255, 255, 255),  # Blanco
        ]
        self._asignacion: dict[int, QColor] = {}

    def agregar_color(self, color: QColor) -> None:
        """Agrega un color a la lista de colores disponibles.

        Args:
            color: Color a agregar.

        """
        self._colores.append(color)

    def asignar(self, cliente: int | str, color: QColor | dict[str, int]) -> None:
        """Asigna un color a un cliente.

        Args:
            cliente: userid (int) del cliente. Acepta strings y los convierte a int.
            color: Color a asignar (QColor o diccionario con r, g, b).

        """
        if isinstance(color, dict):
            r = color.get("r", 0)
            g = color.get("g", 0)
            b = color.get("b", 0)
            color_qcolor = QColor(r, g, b)
        else:
            color_qcolor = color

        self._asignacion[int(cliente)] = color_qcolor

    def colores(self) -> list[QColor]:
        """Obtiene la lista de colores disponibles.

        Returns:
            Lista de colores disponibles.

        """
        return self._colores

    def colores_asignados(self) -> dict[int, QColor]:
        """Obtiene el diccionario de colores asignados a clientes.

        Returns:
            Diccionario con userid (int) como clave y QColor como valor.

        """
        return self._asignacion

    def color_asignado(self, cliente: int | str | None) -> QColor:
        """Obtiene el color asignado al cliente.

        Args:
            cliente: userid (int) del cliente.

        Returns:
            QColor asignado al cliente, o QColor(128, 128, 128) si no se encuentra.

        """
        if cliente is None:
            return QColor(128, 128, 128)
        try:
            key = int(cliente)
        except (TypeError, ValueError):
            return QColor(128, 128, 128)
        return self._asignacion.get(key, QColor(128, 128, 128))

    def __str__(self) -> str:
        """Retorna representación en string de los colores y asignaciones.

        Returns:
            String con la información de colores y asignaciones.

        """
        colores = ", ".join(str(color.getRgb()) for color in self._colores)
        asignacion = "\n".join(
            f"{clave}: {valor.getRgb()}" for clave, valor in self._asignacion.items()
        )
        return f"""Colores:
        {colores}
        Asignacion:
        {asignacion}
        """
