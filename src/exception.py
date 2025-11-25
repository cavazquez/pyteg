"""Excepciones personalizadas del proyecto."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence


class PyTegError(Exception):
    """Excepción base para todos los errores de PyTeg."""

    def __init__(self, msg: str) -> None:
        """Inicializa la excepción con un mensaje.

        Args:
            msg: Mensaje de error.

        """
        super().__init__(msg)
        self.mensaje = msg


class MensajeNoValidoError(PyTegError):
    """Excepción cuando se recibe un mensaje no válido."""

    def __init__(self, msg: str) -> None:
        """Inicializa la excepción con un mensaje.

        Args:
            msg: Mensaje de error.

        """
        self._msg = f"MensajeNoValidoError: {msg}"
        super().__init__(self._msg)


class EstadoInvalidoError(PyTegError):
    """Excepción cuando se ejecuta una acción en un estado inválido."""

    def __init__(
        self, accion: str, estado_actual: str, estados_validos: Sequence[str]
    ) -> None:
        """Inicializa la excepción con información del estado inválido.

        Args:
            accion: Acción que se intentó ejecutar.
            estado_actual: Estado actual del sistema.
            estados_validos: Secuencia de estados válidos para la acción.

        """
        self.accion = accion
        self.estado_actual = estado_actual
        self.estados_validos = list(estados_validos)
        estados = ", ".join(self.estados_validos)
        msg = (
            f"No se puede ejecutar la acción '{accion}' en el estado "
            f"'{estado_actual}'. Estados válidos: {estados}"
        )
        super().__init__(msg)


class ImagenNoEncontradaError(PyTegError):
    """Excepción cuando no se puede cargar una imagen requerida."""

    def __init__(self, ruta_imagen: str, contexto: str = "") -> None:
        """Inicializa la excepción con la ruta de la imagen.

        Args:
            ruta_imagen: Ruta de la imagen que no se pudo cargar.
            contexto: Contexto adicional sobre dónde se intentó cargar la imagen.

        """
        self.ruta_imagen = ruta_imagen
        self.contexto = contexto
        msg = f"No se pudo cargar la imagen: '{ruta_imagen}'"
        if contexto:
            msg += f" ({contexto})"
        msg += ". Verifique que el archivo existe y es accesible."
        super().__init__(msg)


class GameRuleViolationError(PyTegError):
    """Excepción base para violaciones de reglas del juego."""


class NotPlayerTurnError(GameRuleViolationError):
    """Excepción lanzada cuando un jugador intenta actuar fuera de su turno."""

    def __init__(self, mensaje: str = "No es tu turno") -> None:
        """Inicializa la excepción.

        Args:
            mensaje: Mensaje descriptivo del error.

        """
        super().__init__(mensaje)


class CountryNotOwnedError(GameRuleViolationError):
    """Excepción lanzada cuando un jugador intenta actuar sobre un país que no posee."""

    def __init__(self, pais: str, mensaje: str | None = None) -> None:
        """Inicializa la excepción.

        Args:
            pais: Nombre del país involucrado.
            mensaje: Mensaje descriptivo del error. Si es None,
                se genera uno automático.

        """
        if mensaje is None:
            mensaje = f"No eres dueño de {pais}"
        super().__init__(mensaje)
        self.pais = pais


class InvalidActionError(GameRuleViolationError):
    """Excepción lanzada cuando se intenta realizar una acción inválida."""


class GameNotStartedError(GameRuleViolationError):
    """Excepción cuando se intenta realizar una acción antes de que el juego comience."""  # noqa: E501

    def __init__(self, mensaje: str = "El juego no ha comenzado") -> None:
        """Inicializa la excepción.

        Args:
            mensaje: Mensaje descriptivo del error.

        """
        super().__init__(mensaje)
