"""Configuración de partida.

Este módulo define la estructura de configuración de una partida,
permitiendo validación y type safety.
"""

from dataclasses import dataclass

from src.config import (
    DEFAULT_TURN_SECONDS,
    DEFAULT_VICTORY_COUNTRIES,
    VICTORY_ALL_COUNTRIES,
)


@dataclass
class GameConfig:
    """Configuración de una partida del juego.

    Attributes:
        segundos_por_turno: Duración de cada turno en segundos.
        paises_para_victoria: Cantidad de países necesarios para ganar.
            Use 0 para indicar que se necesitan todos los países.
        objetivos_secretos: Si los objetivos secretos están activados.
        misiles_habilitados: Si los misiles están habilitados.

    """

    segundos_por_turno: int = DEFAULT_TURN_SECONDS
    paises_para_victoria: int = DEFAULT_VICTORY_COUNTRIES
    objetivos_secretos: bool = False
    misiles_habilitados: bool = False

    def __post_init__(self) -> None:
        """Valida los valores de configuración después de la inicialización.

        Raises:
            ValueError: Si los valores de configuración son inválidos.

        """
        if self.segundos_por_turno <= 0:
            msg = (
                f"segundos_por_turno debe ser > 0, recibido: {self.segundos_por_turno}"
            )
            raise ValueError(msg)

        if self.paises_para_victoria < 0:
            msg = (
                f"paises_para_victoria debe ser >= 0, "
                f"recibido: {self.paises_para_victoria}"
            )
            raise ValueError(msg)

    def requiere_todos_los_paises(self) -> bool:
        """Verifica si la configuración requiere controlar todos los países.

        Returns:
            True si paises_para_victoria es 0 (todos los países).

        """
        return self.paises_para_victoria == VICTORY_ALL_COUNTRIES

    @classmethod
    def default(cls) -> "GameConfig":
        """Crea una configuración con valores por defecto.

        Returns:
            Configuración con valores por defecto.

        """
        return cls()
