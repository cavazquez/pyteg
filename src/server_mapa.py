"""Módulo para manejar el mapa del juego en el servidor."""

import json
from collections import deque
from collections.abc import Callable
from random import shuffle
from typing import Any

from src.config import (
    MISSILE_DAMAGE_DISTANCE_1,
    MISSILE_DAMAGE_DISTANCE_2,
    MISSILE_DAMAGE_DISTANCE_3,
)
from src.country_data import CountryData


class Mapa:
    """Representa el mapa del juego con países, continentes y jugadores."""

    def __init__(self, build_mapa: Callable[[], dict[str, list[Any]]]) -> None:
        """Inicializa el mapa del juego.

        Args:
            build_mapa: Función que construye y retorna el diccionario del mapa.

        """
        mapa_raw = build_mapa()
        # Convertir listas a CountryData para mejor type safety
        self._mapa: dict[str, CountryData] = {}
        for pais, data in mapa_raw.items():
            self._mapa[pais] = CountryData.from_list(data)

    def agregar_una_unidad(self, pais: str) -> None:
        """Agrega una unidad al país especificado.

        Args:
            pais: Nombre del país.

        """
        self._mapa[pais].unidades += 1

    def restar_una_unidad(self, pais: str) -> None:
        """Resta una unidad del país especificado.

        Args:
            pais: Nombre del país.

        """
        self._mapa[pais].unidades -= 1

    def cantidad_unidades(self, pais: str) -> int:
        """Obtiene la cantidad de unidades en un país.

        Args:
            pais: Nombre del país.

        Returns:
            Cantidad de unidades en el país.

        """
        return self._mapa[pais].unidades

    def set_unidades(self, pais: str, cant: int) -> None:
        """Establece la cantidad de unidades en un país.

        Args:
            pais: Nombre del país.
            cant: Cantidad de unidades a establecer.

        """
        self._mapa[pais].unidades = cant

    def mover(self, desde: str, hacia: str, cantidad: int) -> None:
        """Mueve unidades entre dos países.

        Args:
            desde: País de origen.
            hacia: País de destino.
            cantidad: Cantidad de unidades a mover.

        """
        self._mapa[desde].unidades -= cantidad
        self._mapa[hacia].unidades += cantidad

    def continente(self, pais: str) -> str:
        """Obtiene el continente al que pertenece un país.

        Args:
            pais: Nombre del país.

        Returns:
            Nombre del continente.

        """
        return self._mapa[pais].continente

    def ocupado_por(self, pais: str) -> str:
        """Obtiene el jugador que ocupa un país.

        Args:
            pais: Nombre del país.

        Returns:
            ID del jugador que ocupa el país.

        """
        jugador = self._mapa[pais].jugador
        return str(jugador) if jugador is not None else ""

    def paises(self) -> list[str]:
        """Obtiene la lista de todos los países del mapa.

        Returns:
            Lista de nombres de países.

        """
        if self._mapa:
            return list(self._mapa.keys())
        return []

    def asignar_paises(self, jugadores: list[str]) -> None:
        """Asigna países aleatoriamente a los jugadores.

        Args:
            jugadores: Lista de IDs de jugadores.

        """
        paises = self.paises()
        num_jugadores = len(jugadores)
        num_paises = len(paises)
        paises_por_jugador = num_paises // num_jugadores
        paises_restantes = num_paises % num_jugadores

        # Mezclar los jugadores para una asignación aleatoria
        jugadores_mezclados = jugadores.copy()
        shuffle(jugadores_mezclados)

        # Mezclar la lista de países
        shuffle(paises)

        # Asignar la cantidad base de países a cada jugador
        indice = 0
        for jugador in jugadores_mezclados:
            # Asignar países base
            paises_a_asignar = paises_por_jugador
            if paises_restantes > 0:
                paises_a_asignar += 1
                paises_restantes -= 1

            for _ in range(paises_a_asignar):
                if indice < len(paises):
                    pais = paises[indice]
                    self.asignar_pais(jugador, pais)
                    # Asignar 1 unidad por defecto a cada país
                    self.set_unidades(pais, 1)
                    indice += 1

    def aplicar_resultado_batalla(self, resultado: dict[str, Any]) -> None:
        """Aplica el resultado de una batalla al mapa.

        Args:
            resultado: Diccionario con información del resultado de la batalla.

        """
        for res in resultado["restar"]:
            self.restar_una_unidad(res)

        pais_defensor = resultado["defensor"]
        pais_atacante = resultado["atacante"]
        atacante = self.ocupado_por(pais_atacante)
        if self.cantidad_unidades(pais_defensor) == 0:
            self.agregar_una_unidad(pais_defensor)
            self.asignar_pais(atacante, pais_defensor)

    def cantidad_de_paises_por_continente(self, continente: str) -> int:
        """Obtiene la cantidad de países en un continente.

        Args:
            continente: Nombre del continente.

        Returns:
            Cantidad de países en el continente.

        """
        return len(
            [pais for pais in self.paises() if self.continente(pais) == continente],
        )

    def asignar_pais(self, jugador: str, pais: str) -> None:
        """Asigna un país a un jugador.

        Args:
            jugador: ID del jugador.
            pais: Nombre del país.

        """
        self._mapa[pais].jugador = jugador

    def cantidad_de_paises_del_jugador(self, jugador: str) -> int:
        """Obtiene la cantidad de países que posee un jugador.

        Args:
            jugador: ID del jugador.

        Returns:
            Cantidad de países del jugador.

        """
        return len(
            [pais for pais in self.paises() if self.ocupado_por(pais) == jugador],
        )

    def jugador_posee_pais(self, jugador: str, pais: str) -> bool:
        """Verifica si un jugador específico posee un país determinado.

        Returns:
            True si el jugador posee el país, False en caso contrario.

        """
        return self.ocupado_por(pais) == jugador

    def cantidad_de_paises_del_jugador_por_continente(
        self, jugador: str, continente: str
    ) -> int:
        """Obtiene la cantidad de países de un jugador en un continente.

        Args:
            jugador: ID del jugador.
            continente: Nombre del continente.

        Returns:
            Cantidad de países del jugador en el continente.

        """
        return len(
            [
                pais
                for pais in self.paises()
                if self.ocupado_por(pais) == jugador
                and self.continente(pais) == continente
            ],
        )

    def jugador_controla_continente(self, jugador: str, continente: str) -> bool:
        """Verifica si un jugador controla completamente un continente.

        Args:
            jugador (str): ID del jugador
            continente (str): Nombre del continente

        Returns:
            bool: True si el jugador controla todo el continente

        """
        return self.cantidad_de_paises_del_jugador_por_continente(
            jugador, continente
        ) == self.cantidad_de_paises_por_continente(continente)

    def __str__(self) -> str:
        """Retorna representación en JSON del mapa.

        Returns:
            String JSON del mapa en formato de lista (compatible con versión anterior).

        """
        # Convertir CountryData a formato de lista para compatibilidad
        mapa_lista: dict[str, list[Any]] = {}
        for pais, data in self._mapa.items():
            mapa_lista[pais] = data.to_list()
        return json.dumps(mapa_lista)

    def obtener_paises_adyacentes(self, pais: str) -> list[str]:
        """Devuelve la lista de países adyacentes al país especificado.

        Args:
            pais (str): Nombre del país del que se quieren obtener los adyacentes

        Returns:
            list: Lista de nombres de países adyacentes,
            o lista vacía si no hay adyacentes definidos

        """
        if pais in self._mapa:
            adyacentes = self._mapa[pais].adyacentes
            return [str(p) for p in adyacentes]
        return []

    # ========== Métodos para el sistema de misiles ==========

    def agregar_misil(self, pais: str) -> None:
        """Agrega un misil al país especificado.

        Args:
            pais (str): Nombre del país donde se agregará el misil

        """
        if pais in self._mapa:
            self._mapa[pais].misiles += 1

    def cantidad_misiles(self, pais: str) -> int:
        """Retorna la cantidad de misiles en el país especificado.

        Args:
            pais (str): Nombre del país

        Returns:
            int: Cantidad de misiles en el país

        """
        if pais in self._mapa:
            return self._mapa[pais].misiles
        return 0

    def usar_misil(self, pais: str) -> None:
        """Usa un misil del país especificado (lo decrementa en 1).

        Args:
            pais (str): Nombre del país desde donde se lanzará el misil

        """
        if pais in self._mapa and self._mapa[pais].misiles > 0:
            self._mapa[pais].misiles -= 1

    def calcular_distancia(self, pais_origen: str, pais_destino: str) -> int:
        """Calcula la distancia mínima entre dos países usando BFS.

        Args:
            pais_origen (str): País de origen
            pais_destino (str): País de destino

        Returns:
            int: Distancia mínima en saltos entre países,
            o -1 si no hay camino

        """
        if pais_origen not in self._mapa or pais_destino not in self._mapa:
            return -1

        if pais_origen == pais_destino:
            return 0

        # BFS para encontrar la distancia mínima
        visitados = {pais_origen}
        cola: deque[tuple[str, int]] = deque([(pais_origen, 0)])

        while cola:
            pais_actual, distancia = cola.popleft()

            for pais_adyacente in self.obtener_paises_adyacentes(pais_actual):
                if pais_adyacente == pais_destino:
                    return distancia + 1

                if pais_adyacente not in visitados:
                    visitados.add(pais_adyacente)
                    cola.append((pais_adyacente, distancia + 1))

        return -1  # No hay camino

    def calcular_dano_misil(self, distancia: int) -> int:
        """Calcula el daño que causa un misil según la distancia.

        Args:
            distancia (int): Distancia en saltos entre países

        Returns:
            int: Cantidad de unidades de daño (3, 2, 1, o 0 si fuera de rango)

        """
        damage_map = {
            1: MISSILE_DAMAGE_DISTANCE_1,
            2: MISSILE_DAMAGE_DISTANCE_2,
            3: MISSILE_DAMAGE_DISTANCE_3,
        }
        return damage_map.get(distancia, 0)  # 0 si está fuera de rango
