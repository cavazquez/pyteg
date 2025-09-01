import json
from random import shuffle


class Mapa:
    def __init__(self, build_mapa):
        self._mapa = (
            build_mapa()
        )  # Ahora build_mapa ya devuelve el diccionario completo

    def agregar_una_unidad(self, pais):
        self._mapa[pais][0] += 1

    def restar_una_unidad(self, pais):
        self._mapa[pais][0] -= 1

    def cantidad_unidades(self, pais):
        return self._mapa[pais][0]

    def set_unidades(self, pais, cant):
        self._mapa[pais][0] = cant

    def mover(self, desde, hacia, cantidad):
        self._mapa[desde][0] -= cantidad
        self._mapa[hacia][0] += cantidad

    def continente(self, pais):
        return self._mapa[pais][1]

    def ocupado_por(self, pais):
        return self._mapa[pais][2]

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
        self._mapa[pais][2] = jugador

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

    def tiene_toda_europa(self, jugador):
        continente = "Europa"
        return self.cantidad_de_paises_del_jugador_por_continente(
            jugador,
            continente,
        ) == self.cantidad_de_paises_por_continente(continente)

    def tiene_toda_asia(self, jugador):
        continente = "Asia"
        return self.cantidad_de_paises_del_jugador_por_continente(
            jugador,
            continente,
        ) == self.cantidad_de_paises_por_continente(continente)

    def tiene_toda_oceania(self, jugador):
        continente = "Oceania"
        return self.cantidad_de_paises_del_jugador_por_continente(
            jugador,
            continente,
        ) == self.cantidad_de_paises_por_continente(continente)

    def tiene_toda_africa(self, jugador):
        continente = "Africa"
        return self.cantidad_de_paises_del_jugador_por_continente(
            jugador,
            continente,
        ) == self.cantidad_de_paises_por_continente(continente)

    def tiene_toda_america_del_sur(self, jugador):
        continente = "Sudamerica"
        return self.cantidad_de_paises_del_jugador_por_continente(
            jugador,
            continente,
        ) == self.cantidad_de_paises_por_continente(continente)

    def tiene_toda_america_del_norte(self, jugador):
        continente = "Norteamerica"
        return self.cantidad_de_paises_del_jugador_por_continente(
            jugador,
            continente,
        ) == self.cantidad_de_paises_por_continente(continente)

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
            return self._mapa[pais][3]
        return []
