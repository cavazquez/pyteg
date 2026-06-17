"""Excepciones de violaciones de reglas del juego."""

from __future__ import annotations

from pyteg.exceptions.base import PyTegError


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


class CountryNotFoundError(GameRuleViolationError):
    """Excepción cuando se referencia un país inexistente en el mapa."""

    def __init__(self, pais: str, mensaje: str | None = None) -> None:
        """Inicializa la excepción.

        Args:
            pais: Nombre del país no encontrado.
            mensaje: Mensaje descriptivo del error.

        """
        if mensaje is None:
            mensaje = f"El país '{pais}' no existe en el mapa"
        super().__init__(mensaje)
        self.pais = pais


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


class MissingFieldError(GameRuleViolationError):
    """Excepción cuando falta un campo requerido en una acción."""

    def __init__(self, campo: str, mensaje: str | None = None) -> None:
        """Inicializa la excepción.

        Args:
            campo: Nombre del campo faltante.
            mensaje: Mensaje descriptivo del error. Si es None,
                se genera uno automático.

        """
        if mensaje is None:
            mensaje = f"{campo} no especificado"
        super().__init__(mensaje)
        self.campo = campo


class MissilesNotEnabledError(GameRuleViolationError):
    """Excepción cuando se intenta usar misiles pero no están habilitados."""

    def __init__(
        self, mensaje: str = "Los misiles no están habilitados en esta partida"
    ) -> None:
        """Inicializa la excepción.

        Args:
            mensaje: Mensaje descriptivo del error.

        """
        super().__init__(mensaje)


class InsufficientUnitsError(GameRuleViolationError):
    """Excepción cuando no hay suficientes unidades para una acción."""

    def __init__(self, pais: str, requeridas: int, disponibles: int) -> None:
        """Inicializa la excepción.

        Args:
            pais: Nombre del país.
            requeridas: Cantidad de unidades requeridas.
            disponibles: Cantidad de unidades disponibles.

        """
        mensaje = (
            f"Necesitas al menos {requeridas} unidades en {pais}. "
            f"Tienes {disponibles} unidades."
        )
        super().__init__(mensaje)
        self.pais = pais
        self.requeridas = requeridas
        self.disponibles = disponibles


class NoMissilesAvailableError(GameRuleViolationError):
    """Excepción cuando se intenta usar un misil pero no hay disponibles."""

    def __init__(self, pais: str) -> None:
        """Inicializa la excepción.

        Args:
            pais: Nombre del país sin misiles.

        """
        mensaje = f"No tienes misiles disponibles en {pais}"
        super().__init__(mensaje)
        self.pais = pais


class MissileOutOfRangeError(GameRuleViolationError):
    """Excepción cuando un misil está fuera de rango."""

    def __init__(self, distancia: int, max_distancia: int) -> None:
        """Inicializa la excepción.

        Args:
            distancia: Distancia calculada.
            max_distancia: Distancia máxima permitida.

        """
        mensaje = (
            f"El misil está fuera de rango. Distancia: {distancia}, "
            f"Máximo permitido: {max_distancia}"
        )
        super().__init__(mensaje)
        self.distancia = distancia
        self.max_distancia = max_distancia
