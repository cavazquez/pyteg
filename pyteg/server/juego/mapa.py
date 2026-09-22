# ruff: noqa: DOC201, DOC501, D417, TRY003, EM101, EM102, PLR2004

"""Módulo para manejar el mapa del juego en el servidor."""

from __future__ import annotations

import json
from random import shuffle
from typing import TYPE_CHECKING, Any

from pyteg.core.combate.missile_system import MissileSystem
from pyteg.core.mapa.country_data import CountryData
from pyteg.exceptions import CountryNotFoundError

if TYPE_CHECKING:
    from collections.abc import Callable

    from pyteg.core.partida.reglas import ThemeRules


class Mapa:
    """Representa el mapa del juego con países, continentes y jugadores."""

    def __init__(
        self,
        build_mapa: Callable[[], dict[str, list[Any]]],
        rules: ThemeRules | None = None,
    ) -> None:
        """Inicializa el mapa del juego.

        Args:
            build_mapa: Función que construye y retorna el diccionario del mapa.
            rules: Perfil de reglas opcional del tema.

        """
        mapa_raw = build_mapa()
        self._build_mapa = build_mapa
        self._rules = rules
        # Convertir listas a CountryData para mejor type safety
        self._mapa: dict[str, CountryData] = {}
        for pais, data in mapa_raw.items():
            self._mapa[pais] = CountryData.from_list(data)
        # Un condominio conserva una única cantidad total de unidades en
        # ``CountryData`` y distribuye esas unidades por jugador aquí.  Así se
        # mantiene compatible el formato histórico del mapa y el snapshot
        # puede publicar ambos colores sin perder información.
        self._condominios: dict[str, dict[int, int]] = {}
        # Inicializar sistema de misiles
        self._missile_system = MissileSystem(self, rules)

    def reiniciar(self) -> None:
        """Restaura países, unidades y misiles al mapa original del tema."""
        mapa_raw = self._build_mapa()
        self._mapa = {
            pais: CountryData.from_list(data) for pais, data in mapa_raw.items()
        }
        self._condominios = {}
        self._missile_system = MissileSystem(self, self._rules)

    def configurar_reglas(self, rules: ThemeRules) -> None:
        """Asocia el perfil público a los cálculos dependientes del tema."""
        self._rules = rules
        self._missile_system = MissileSystem(self, rules)

    def pais_existe(self, pais: str) -> bool:
        """Indica si un país está definido en el mapa.

        Returns:
            True si el país existe.

        """
        return pais in self._mapa

    def _require_pais(self, pais: str) -> CountryData:
        """Obtiene los datos de un país o lanza si no existe.

        Returns:
            Datos del país solicitado.

        Raises:
            CountryNotFoundError: Si el país no está en el mapa.

        """
        if pais not in self._mapa:
            raise CountryNotFoundError(pais)
        return self._mapa[pais]

    def agregar_una_unidad(self, pais: str) -> None:
        """Agrega una unidad al país especificado.

        Args:
            pais: Nombre del país.

        """
        self._require_pais(pais).unidades += 1

    def agregar_unidad_jugador(self, pais: str, jugador: int) -> None:
        """Agrega una unidad al aporte de un jugador en un condominio."""
        data = self._require_pais(pais)
        jugador = int(jugador)
        if pais not in self._condominios:
            if data.jugador != jugador:
                raise ValueError(f"El jugador {jugador} no ocupa {pais}")
            data.unidades += 1
            return
        if jugador not in self._condominios[pais]:
            raise ValueError(f"El jugador {jugador} no ocupa {pais}")
        self._condominios[pais][jugador] += 1
        data.unidades += 1

    def restar_una_unidad(self, pais: str) -> None:
        """Resta una unidad del país especificado.

        Args:
            pais: Nombre del país.

        """
        self._require_pais(pais).unidades -= 1

    def restar_unidad_jugador(
        self, pais: str, jugador: int, *, normalizar: bool = True
    ) -> None:
        """Resta una unidad del aporte de un jugador."""
        data = self._require_pais(pais)
        jugador = int(jugador)
        if pais not in self._condominios:
            if data.jugador != jugador:
                raise ValueError(f"El jugador {jugador} no ocupa {pais}")
            data.unidades -= 1
            return
        cantidad = self._condominios[pais].get(jugador, 0)
        if cantidad <= 0:
            raise ValueError(f"El jugador {jugador} no tiene unidades en {pais}")
        self._condominios[pais][jugador] = cantidad - 1
        data.unidades -= 1
        if normalizar:
            self._normalizar_condominio(pais)

    def cantidad_unidades(self, pais: str) -> int:
        """Obtiene la cantidad de unidades en un país.

        Args:
            pais: Nombre del país.

        Returns:
            Cantidad de unidades en el país.

        """
        return self._require_pais(pais).unidades

    def set_unidades(self, pais: str, cant: int) -> None:
        """Establece la cantidad de unidades en un país.

        Args:
            pais: Nombre del país.
            cant: Cantidad de unidades a establecer.

        """
        self._require_pais(pais).unidades = cant

    def mover(self, desde: str, hacia: str, cantidad: int) -> None:
        """Mueve unidades entre dos países.

        Args:
            desde: País de origen.
            hacia: País de destino.
            cantidad: Cantidad de unidades a mover.

        """
        origen_data = self._require_pais(desde)
        destino_data = self._require_pais(hacia)
        origen_data.unidades -= cantidad
        destino_data.unidades += cantidad

    def mover_jugador(
        self, desde: str, hacia: str, jugador: int, cantidad: int
    ) -> None:
        """Mueve unidades de un jugador entre países que ocupa."""
        jugador = int(jugador)
        if not self.jugador_posee_pais(jugador, desde):
            raise ValueError(f"El jugador {jugador} no ocupa {desde}")
        if not self.jugador_posee_pais(jugador, hacia):
            raise ValueError(f"El jugador {jugador} no ocupa {hacia}")
        disponibles = self.cantidad_unidades_jugador(desde, jugador)
        if cantidad <= 0 or disponibles <= cantidad:
            raise ValueError("El movimiento debe dejar una unidad en el origen")
        self.restar_unidad_jugador_n(pais=desde, jugador=jugador, cantidad=cantidad)
        self.agregar_unidad_jugador_n(pais=hacia, jugador=jugador, cantidad=cantidad)

    def restar_unidad_jugador_n(self, pais: str, jugador: int, cantidad: int) -> None:
        """Resta varias unidades conservando la validación por jugador."""
        for _ in range(int(cantidad)):
            self.restar_unidad_jugador(pais, jugador)

    def agregar_unidad_jugador_n(self, pais: str, jugador: int, cantidad: int) -> None:
        """Agrega varias unidades conservando la validación por jugador."""
        for _ in range(int(cantidad)):
            self.agregar_unidad_jugador(pais, jugador)

    def continente(self, pais: str) -> str:
        """Obtiene el continente al que pertenece un país.

        Args:
            pais: Nombre del país.

        Returns:
            Nombre del continente.

        """
        return self._require_pais(pais).continente

    def ocupado_por(self, pais: str) -> int | None:
        """Obtiene el userid del jugador que ocupa un país.

        Args:
            pais: Nombre del país.

        Returns:
            userid (int) del jugador que ocupa el país, o None si no tiene dueño.

        """
        return self._require_pais(pais).jugador

    def es_condominio(self, pais: str) -> bool:
        """Indica si el país tiene dos o más ocupantes."""
        return pais in self._condominios

    def ocupantes(self, pais: str) -> dict[int, int]:
        """Devuelve las unidades de cada ocupante, sin exponer referencias."""
        data = self._require_pais(pais)
        if pais in self._condominios:
            return dict(self._condominios[pais])
        return {data.jugador: data.unidades} if data.jugador is not None else {}

    def unidades_jugador(self, pais: str, jugador: int) -> int:
        """Obtiene sólo las unidades del jugador en un país."""
        jugador = int(jugador)
        if pais in self._condominios:
            return self._condominios[pais].get(jugador, 0)
        data = self._require_pais(pais)
        return data.unidades if data.jugador == jugador else 0

    def cantidad_unidades_jugador(self, pais: str, jugador: int) -> int:
        """Alias explícito usado por validadores y tareas."""
        return self.unidades_jugador(pais, jugador)

    def crear_condominio(self, pais: str, unidades_por_jugador: dict[int, int]) -> None:
        """Convierte un país en condominio con aportes positivos."""
        data = self._require_pais(pais)
        holdings = {
            int(jugador): int(unidades)
            for jugador, unidades in unidades_por_jugador.items()
            if int(unidades) > 0
        }
        if len(holdings) < 2:
            raise ValueError("Un condominio necesita al menos dos ocupantes")
        if sum(holdings.values()) != data.unidades:
            raise ValueError("Los aportes del condominio no coinciden con sus unidades")
        self._condominios[pais] = holdings
        data.jugador = None

    def conquistar_condominio(
        self, pais: str, atacante: int, defensor: int | None, unidades: int = 1
    ) -> None:
        """Expulsa a un defensor y agrega al atacante al país conquistado."""
        atacante = int(atacante)
        if pais not in self._condominios:
            self.asignar_pais(atacante, pais)
            return
        holdings = self._condominios[pais]
        if defensor is not None:
            holdings.pop(int(defensor), None)
        holdings[atacante] = holdings.get(atacante, 0) + int(unidades)
        data = self._require_pais(pais)
        data.unidades = sum(holdings.values())
        self._normalizar_condominio(pais)

    def expulsar_ocupante(self, pais: str, jugador: int) -> None:
        """Elimina a un ocupante derrotado y normaliza el país."""
        if pais not in self._condominios:
            return
        self._condominios[pais].pop(int(jugador), None)
        self._normalizar_condominio(pais)

    def _normalizar_condominio(self, pais: str) -> None:
        holdings = self._condominios.get(pais)
        if holdings is None:
            return
        holdings = {
            jugador: unidades for jugador, unidades in holdings.items() if unidades > 0
        }
        data = self._require_pais(pais)
        if not holdings:
            data.jugador = None
            data.unidades = 0
            self._condominios.pop(pais, None)
        elif len(holdings) == 1:
            data.jugador, data.unidades = next(iter(holdings.items()))
            self._condominios.pop(pais, None)
        else:
            data.jugador = None
            data.unidades = sum(holdings.values())
            self._condominios[pais] = holdings

    def paises(self) -> list[str]:
        """Obtiene la lista de todos los países del mapa.

        Returns:
            Lista de nombres de países.

        """
        if self._mapa:
            return list(self._mapa.keys())
        return []

    def asignar_paises(self, jugadores: list[int]) -> None:
        """Asigna países aleatoriamente a los jugadores.

        Args:
            jugadores: Lista de userids (int) de jugadores.

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
        if self.cantidad_unidades(pais_defensor) == 0 and atacante is not None:
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

    def asignar_pais(self, jugador: int, pais: str) -> None:
        """Asigna un país a un jugador.

        Args:
            jugador: userid (int) del jugador.
            pais: Nombre del país.

        """
        data = self._require_pais(pais)
        self._condominios.pop(pais, None)
        data.jugador = jugador

    def cantidad_de_paises_del_jugador(
        self, jugador: int, *, incluir_condominios: bool = False
    ) -> int:
        """Obtiene la cantidad de países que posee un jugador.

        Args:
            jugador: userid (int) del jugador.

        Returns:
            Cantidad de países del jugador.

        """
        exclusivos = len(
            [pais for pais in self.paises() if self.ocupado_por(pais) == jugador],
        )
        if not incluir_condominios:
            return exclusivos
        compartidos = sum(
            1 for pais in self._condominios if int(jugador) in self._condominios[pais]
        )
        return exclusivos + compartidos

    def tiene_paises(self, jugador: int) -> bool:
        """Indica si el jugador conserva al menos un país, incluso compartido."""
        return (
            self.cantidad_de_paises_del_jugador(jugador, incluir_condominios=True) > 0
        )

    def jugador_posee_pais(self, jugador: int, pais: str) -> bool:
        """Verifica si un jugador específico posee un país determinado.

        Args:
            jugador: userid (int) del jugador.
            pais: Nombre del país.

        Returns:
            True si el jugador posee el país, False en caso contrario.

        """
        jugador = int(jugador)
        if pais in self._condominios:
            return jugador in self._condominios[pais]
        return self.ocupado_por(pais) == jugador

    def cantidad_de_paises_del_jugador_por_continente(
        self, jugador: int, continente: str
    ) -> int:
        """Obtiene la cantidad de países de un jugador en un continente.

        Args:
            jugador: userid (int) del jugador.
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

    def jugador_controla_continente(self, jugador: int, continente: str) -> bool:
        """Verifica si un jugador controla completamente un continente.

        Args:
            jugador: userid (int) del jugador.
            continente: Nombre del continente.

        Returns:
            True si el jugador controla todo el continente.

        """
        cantidad_total = self.cantidad_de_paises_por_continente(continente)
        if cantidad_total == 0:
            return False
        return (
            self.cantidad_de_paises_del_jugador_por_continente(jugador, continente)
            == cantidad_total
        )

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
            pais: Nombre del país del que se quieren obtener los adyacentes.

        Returns:
            Lista de nombres de países adyacentes, o lista vacía si no hay
            adyacentes definidos.

        """
        if not self.pais_existe(pais):
            return []
        adyacentes = self._mapa[pais].adyacentes
        return [str(p) for p in adyacentes]

    def _tiene_pais(self, pais: str) -> bool:
        """Verifica si un país existe en el mapa.

        Args:
            pais: Nombre del país.

        Returns:
            True si el país existe, False en caso contrario.

        """
        return self.pais_existe(pais)

    def _obtener_misiles(self, pais: str) -> int:
        """Obtiene la cantidad de misiles de un país (método interno).

        Args:
            pais: Nombre del país.

        Returns:
            Cantidad de misiles.

        """
        return self._mapa[pais].misiles if pais in self._mapa else 0

    def _incrementar_misiles(self, pais: str) -> None:
        """Incrementa los misiles de un país (método interno).

        Args:
            pais: Nombre del país.

        """
        if pais in self._mapa:
            self._mapa[pais].misiles += 1

    def _decrementar_misiles(self, pais: str) -> None:
        """Decrementa los misiles de un país (método interno).

        Args:
            pais: Nombre del país.

        """
        if pais in self._mapa and self._mapa[pais].misiles > 0:
            self._mapa[pais].misiles -= 1

    # ========== Métodos para el sistema de misiles ==========
    # Estos métodos delegan al MissileSystem para mantener la API pública
    # y separar la lógica de misiles del mapa.

    def agregar_misil(self, pais: str) -> None:
        """Agrega un misil al país especificado.

        Args:
            pais: Nombre del país donde se agregará el misil.

        """
        self._missile_system.agregar_misil(pais)

    def cantidad_misiles(self, pais: str) -> int:
        """Retorna la cantidad de misiles en el país especificado.

        Args:
            pais: Nombre del país.

        Returns:
            Cantidad de misiles en el país.

        """
        return self._missile_system.cantidad_misiles(pais)

    def usar_misil(self, pais: str) -> None:
        """Usa un misil del país especificado (lo decrementa en 1).

        Args:
            pais: Nombre del país desde donde se lanzará el misil.

        """
        self._missile_system.usar_misil(pais)

    def calcular_distancia(self, pais_origen: str, pais_destino: str) -> int:
        """Calcula la distancia mínima entre dos países usando BFS.

        Args:
            pais_origen: País de origen.
            pais_destino: País de destino.

        Returns:
            Distancia mínima en saltos entre países, o -1 si no hay camino.

        """
        return self._missile_system.calcular_distancia(pais_origen, pais_destino)

    def calcular_dano_misil(self, distancia: int) -> int:
        """Calcula el daño que causa un misil según la distancia.

        Args:
            distancia: Distancia en saltos entre países.

        Returns:
            Cantidad de unidades de daño (3, 2, 1, o 0 si fuera de rango).

        """
        return self._missile_system.calcular_dano_misil(distancia)
