import json
from random import shuffle


class Mapa:
    # Constantes para índices de la estructura de datos del mapa
    _UNIDADES = 0
    _CONTINENTE = 1
    _JUGADOR = 2
    _ADYACENTES = 3

    def __init__(self, build_mapa):
        self._mapa = (
            build_mapa()
        )  # Ahora build_mapa ya devuelve el diccionario completo

    def agregar_una_unidad(self, pais):
        self._mapa[pais][self._UNIDADES] += 1

    def restar_una_unidad(self, pais):
        self._mapa[pais][self._UNIDADES] -= 1

    def cantidad_unidades(self, pais):
        return self._mapa[pais][self._UNIDADES]

    def set_unidades(self, pais, cant):
        self._mapa[pais][self._UNIDADES] = cant

    def mover(self, desde, hacia, cantidad):
        self._mapa[desde][self._UNIDADES] -= cantidad
        self._mapa[hacia][self._UNIDADES] += cantidad

    def continente(self, pais):
        return self._mapa[pais][self._CONTINENTE]

    def ocupado_por(self, pais):
        return self._mapa[pais][self._JUGADOR]

    def paises(self):
        if self._mapa:
            return list(self._mapa.keys())
        return []

    def asignar_paises(self, jugadores):
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

    def aplicar_resultado_batalla(self, resultado):
        for res in resultado["restar"]:
            self.restar_una_unidad(res)

        pais_defensor = resultado["defensor"]
        pais_atacante = resultado["atacante"]
        atacante = self.ocupado_por(pais_atacante)
        if self.cantidad_unidades(pais_defensor) == 0:
            self.agregar_una_unidad(pais_defensor)
            self.asignar_pais(atacante, pais_defensor)

    def cantidad_de_paises_por_continente(self, continente):
        return len(
            [pais for pais in self.paises() if self.continente(pais) == continente],
        )

    def asignar_pais(self, jugador, pais):
        self._mapa[pais][self._JUGADOR] = jugador

    def cantidad_de_paises_del_jugador(self, jugador):
        return len(
            [pais for pais in self.paises() if self.ocupado_por(pais) == jugador],
        )

    def jugador_posee_pais(self, jugador, pais):
        """Verifica si un jugador específico posee un país determinado."""
        return self.ocupado_por(pais) == jugador

    def cantidad_de_paises_del_jugador_por_continente(self, jugador, continente):
        return len(
            [
                pais
                for pais in self.paises()
                if self.ocupado_por(pais) == jugador
                and self.continente(pais) == continente
            ],
        )

    def jugador_controla_continente(self, jugador, continente):
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

    def tiene_toda_europa(self, jugador):
        return self.jugador_controla_continente(jugador, "Europa")

    def tiene_toda_asia(self, jugador):
        return self.jugador_controla_continente(jugador, "Asia")

    def tiene_toda_oceania(self, jugador):
        return self.jugador_controla_continente(jugador, "Oceania")

    def tiene_toda_africa(self, jugador):
        return self.jugador_controla_continente(jugador, "Africa")

    def tiene_toda_america_del_sur(self, jugador):
        return self.jugador_controla_continente(jugador, "Sudamerica")

    def tiene_toda_america_del_norte(self, jugador):
        return self.jugador_controla_continente(jugador, "Norteamerica")

    def __str__(self):
        return json.dumps(self._mapa)

    def obtener_paises_adyacentes(self, pais):
        """
        Devuelve la lista de países adyacentes al país especificado.

        Args:
            pais (str): Nombre del país del que se quieren obtener los adyacentes

        Returns:
            list: Lista de nombres de países adyacentes,
            o lista vacía si no hay adyacentes definidos
        """
        if pais in self._mapa:
            return self._mapa[pais][self._ADYACENTES]
        return []
