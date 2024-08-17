class Colores:

    def __init__(self):
        self.colores = []
        self.asignacion = {}

    def agregar_color(self, color):
        self.colores.append(color)

    def asignar(self, cliente, color):
        self.asignacion[cliente] = color

    def __str__(self):
        colores = ", ".join(str(color) for color in self.colores)
        asignacion = "\n".join(
            f"{clave}: {valor}" for clave, valor in self.asignacion.items()
        )
        return f"""Colores:
        {colores}
        Asignacion:
        {asignacion}
        """
