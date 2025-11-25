"""Excepciones personalizadas del proyecto."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence


class MensajeNoValidoError(Exception):
    def __init__(self, msg: str) -> None:
        self._msg = f"MensajeNoValidoError: {msg}"
        super().__init__(self._msg)


class EstadoInvalidoError(Exception):
    """Excepción cuando se ejecuta una acción en un estado inválido."""

    def __init__(
        self, accion: str, estado_actual: str, estados_validos: Sequence[str]
    ) -> None:
        self.accion = accion
        self.estado_actual = estado_actual
        self.estados_validos = list(estados_validos)
        estados = ", ".join(self.estados_validos)
        msg = (
            f"No se puede ejecutar la acción '{accion}' en el estado "
            f"'{estado_actual}'. Estados válidos: {estados}"
        )
        super().__init__(msg)


class ImagenNoEncontradaError(Exception):
    """Excepción cuando no se puede cargar una imagen requerida."""

    def __init__(self, ruta_imagen: str, contexto: str = "") -> None:
        self.ruta_imagen = ruta_imagen
        self.contexto = contexto
        msg = f"No se pudo cargar la imagen: '{ruta_imagen}'"
        if contexto:
            msg += f" ({contexto})"
        msg += ". Verifique que el archivo existe y es accesible."
        super().__init__(msg)
