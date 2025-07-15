class MensajeNoValidoError(Exception):
    def __init__(self, msg):
        self._msg = f"MensajeNoValidoError: {msg}"
        super().__init__(self._msg)


class EstadoInvalidoError(Exception):
    """Excepción lanzada cuando se intenta ejecutar una acción en un estado inválido."""

    def __init__(self, accion, estado_actual, estados_validos):
        self.accion = accion
        self.estado_actual = estado_actual
        self.estados_validos = estados_validos
        msg = (
            f"No se puede ejecutar la acción '{accion}' en el estado "
            f"'{estado_actual}'. Estados válidos: {', '.join(estados_validos)}"
        )
        super().__init__(msg)


class ImagenNoEncontradaError(Exception):
    """Excepción lanzada cuando no se puede cargar una imagen requerida."""

    def __init__(self, ruta_imagen, contexto=""):
        self.ruta_imagen = ruta_imagen
        self.contexto = contexto
        msg = f"No se pudo cargar la imagen: '{ruta_imagen}'"
        if contexto:
            msg += f" ({contexto})"
        msg += ". Verifique que el archivo existe y es accesible."
        super().__init__(msg)
