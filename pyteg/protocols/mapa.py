"""Protocolo del mapa del juego (`IMapProtocol`)."""

from __future__ import annotations

from typing import Protocol


class IMapProtocol(Protocol):
    """Protocolo para objetos de mapa.

    Define la interfaz mínima que debe implementar un objeto de mapa
    para ser usado en las tareas del servidor.
    """

    def agregar_una_unidad(self, pais: str) -> None:
        """Agrega una unidad al país especificado.

        Args:
            pais: Nombre del país.

        """
        ...

    def restar_una_unidad(self, pais: str) -> None:
        """Resta una unidad del país especificado.

        Args:
            pais: Nombre del país.

        """
        ...

    def cantidad_unidades(self, pais: str) -> int:
        """Obtiene la cantidad de unidades en un país.

        Args:
            pais: Nombre del país.

        Returns:
            Cantidad de unidades en el país.

        """
        ...

    def set_unidades(self, pais: str, cant: int) -> None:
        """Establece la cantidad de unidades en un país.

        Args:
            pais: Nombre del país.
            cant: Cantidad de unidades a establecer.

        """
        ...

    def mover(self, desde: str, hacia: str, cantidad: int) -> None:
        """Mueve unidades entre dos países.

        Args:
            desde: País de origen.
            hacia: País de destino.
            cantidad: Cantidad de unidades a mover.

        """
        ...

    def continente(self, pais: str) -> str:
        """Obtiene el continente al que pertenece un país.

        Args:
            pais: Nombre del país.

        Returns:
            Nombre del continente.

        """
        ...

    def ocupado_por(self, pais: str) -> int | None:
        """Obtiene el userid del jugador que ocupa un país.

        Args:
            pais: Nombre del país.

        Returns:
            userid (int) del jugador que ocupa el país, o None si no tiene dueño.

        """
        ...

    def paises(self) -> list[str]:
        """Obtiene la lista de todos los países del mapa.

        Returns:
            Lista de nombres de países.

        """
        ...

    def asignar_pais(self, jugador: int, pais: str) -> None:
        """Asigna un país a un jugador.

        Args:
            jugador: userid (int) del jugador.
            pais: Nombre del país.

        """
        ...

    def jugador_posee_pais(self, jugador: int, pais: str) -> bool:
        """Verifica si un jugador específico posee un país determinado.

        Args:
            jugador: userid (int) del jugador.
            pais: Nombre del país.

        Returns:
            True si el jugador posee el país, False en caso contrario.

        """
        ...

    def jugador_controla_continente(self, jugador: int, continente: str) -> bool:
        """Verifica si un jugador controla completamente un continente.

        Args:
            jugador: userid (int) del jugador.
            continente: Nombre del continente.

        Returns:
            True si el jugador controla todo el continente.

        """
        ...

    def obtener_paises_adyacentes(self, pais: str) -> list[str]:
        """Devuelve la lista de países adyacentes al país especificado.

        Args:
            pais: Nombre del país.

        Returns:
            Lista de nombres de países adyacentes.

        """
        ...

    def cantidad_misiles(self, pais: str) -> int:
        """Retorna la cantidad de misiles en el país especificado.

        Args:
            pais: Nombre del país.

        Returns:
            Cantidad de misiles en el país.

        """
        ...

    def agregar_misil(self, pais: str) -> None:
        """Agrega un misil al país especificado.

        Args:
            pais: Nombre del país donde se agregará el misil.

        """
        ...

    def usar_misil(self, pais: str) -> None:
        """Usa un misil del país especificado.

        Args:
            pais: Nombre del país desde donde se lanzará el misil.

        """
        ...

    def calcular_distancia(self, pais_origen: str, pais_destino: str) -> int:
        """Calcula la distancia mínima entre dos países.

        Args:
            pais_origen: País de origen.
            pais_destino: País de destino.

        Returns:
            Distancia mínima en saltos entre países, o -1 si no hay camino.

        """
        ...

    def calcular_dano_misil(self, distancia: int) -> int:
        """Calcula el daño que causa un misil según la distancia.

        Args:
            distancia: Distancia en saltos entre países.

        Returns:
            Cantidad de unidades de daño (3, 2, 1, o 0 si fuera de rango).

        """
        ...
