class Colores:

    def __init__(self):
        self._colores = []
        self._asignacion = {}

    def agregar_color(self, color):
        self._colores.append(color)

    def asignar(self, cliente, color):
        self._asignacion[cliente] = color

    def colores(self):
        return self._colores

    def colores_asignados(self):
        return self._asignacion

    def __str__(self):
        colores = ", ".join(str(color) for color in self._colores)
        asignacion = "\n".join(
            f"{clave}: {valor}" for clave, valor in self._asignacion.items()
        )
        return f"""Colores:
        {colores}
        Asignacion:
        {asignacion}
        """
