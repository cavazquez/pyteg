import random
from typing import Any

from src.logger import get_logger

LOGGER = get_logger("server.objetivos_secretos")


class ObjetivosSecretos:
    """Maneja la asignación y verificación de objetivos secretos para los jugadores."""

    def __init__(self, toml_reader: Any) -> None:
        """
        Inicializa el sistema de objetivos secretos.

        Args:
            toml_reader: Instancia de TomlReader con objetivos secretos cargados
        """
        self.toml_reader = toml_reader
        self.objetivos_disponibles = toml_reader.get_objetivos_secretos()
        self.objetivos_asignados: dict[str, str] = {}  # client_id -> objetivo_id

    def asignar_objetivos_aleatorios(self, clientes: list[Any]) -> None:
        """
        Asigna objetivos secretos aleatorios a una lista de clientes.

        Args:
            clientes: Lista de objetos cliente con atributo user_id
        """
        if not clientes:
            return

        # Limpiar asignaciones previas
        self.objetivos_asignados.clear()

        # Obtener lista de objetivos disponibles
        objetivos_ids = list(self.objetivos_disponibles.keys())

        # Mezclar objetivos para asignación aleatoria
        random.shuffle(objetivos_ids)

        LOGGER.info("=== ASIGNANDO OBJETIVOS SECRETOS ===")
        LOGGER.info("Objetivos disponibles: %s", objetivos_ids)
        LOGGER.info("Clientes a asignar: %s", len(clientes))

        # Asignar un objetivo a cada cliente
        for i, client in enumerate(clientes):
            # Si hay más jugadores que objetivos, reutilizar objetivos
            objetivo_id = objetivos_ids[i % len(objetivos_ids)]
            user_id = client.userid()
            self.objetivos_asignados[user_id] = objetivo_id
            LOGGER.info(
                "Asignado objetivo '%s' a cliente %s (ID: %s)",
                objetivo_id,
                client.username(),
                user_id,
            )

        LOGGER.info("Objetivos asignados: %s", self.objetivos_asignados)
        LOGGER.info("=== FIN ASIGNACIÓN OBJETIVOS ===")

    def get_objetivo_jugador(self, client_id: str) -> dict[str, Any] | None:
        """
        Obtiene el objetivo secreto asignado a un jugador.

        Args:
            client_id: ID del cliente

        Returns:
            Diccionario con datos del objetivo o None si no tiene asignado
        """
        objetivo_id = self.objetivos_asignados.get(client_id)
        if objetivo_id:
            return self.toml_reader.get_objetivo_secreto(objetivo_id)
        return None

    def verificar_condicion_victoria(
        self, client_id: str, mapa: Any, colores: Any
    ) -> bool:
        """
        Verifica si un jugador ha cumplido su objetivo secreto.

        Args:
            client_id: ID del cliente
            mapa: Estado actual del mapa
            colores: Sistema de colores para identificar jugadores

        Returns:
            True si el jugador ha cumplido su objetivo secreto
        """
        objetivo = self.get_objetivo_jugador(client_id)
        if not objetivo:
            return False

        tipo = objetivo.get("tipo")

        if tipo == "destruir_jugador":
            return self._verificar_destruir_jugador(client_id, objetivo, mapa, colores)
        if tipo == "conquistar_continentes":
            return self._verificar_conquistar_continentes(client_id, objetivo, mapa)
        if tipo == "conquistar_paises":
            return self._verificar_conquistar_paises(client_id, objetivo, mapa)
        if tipo == "conquistar_paises_con_tropas":
            return self._verificar_conquistar_paises_con_tropas(
                client_id, objetivo, mapa
            )

        return False

    def _verificar_destruir_jugador(
        self, client_id: str, objetivo: dict[str, Any], mapa: Any, colores: Any
    ) -> bool:
        """Verifica si se ha destruido completamente al jugador objetivo."""
        color_objetivo = objetivo.get("color_objetivo")
        paises_alternativos = objetivo.get("paises_alternativos", 24)

        # Buscar si existe un jugador con el color objetivo
        jugador_objetivo_existe = False
        jugador_objetivo_eliminado = True

        # Obtener todos los clientes del servidor
        try:
            all_clients = (
                colores.dame_clientes() if hasattr(colores, "dame_clientes") else []
            )
        except (AttributeError, RuntimeError):
            all_clients = []

        for client in all_clients:
            try:
                client_color = (
                    colores.get_color_name(client)
                    if hasattr(colores, "get_color_name")
                    else None
                )
                if client_color == color_objetivo:
                    jugador_objetivo_existe = True
                    # Verificar si tiene países
                    if any(pais_data[2] == client for pais_data in mapa.values()):
                        jugador_objetivo_eliminado = False
                    break
            except (AttributeError, RuntimeError):
                continue

        # Si no existe el jugador objetivo o soy yo mismo, usar objetivo alternativo
        try:
            mi_color = (
                colores.get_color_name_by_client_id(client_id)
                if hasattr(colores, "get_color_name_by_client_id")
                else None
            )
        except (AttributeError, RuntimeError):
            mi_color = None

        if not jugador_objetivo_existe or mi_color == color_objetivo:
            return self._contar_paises_jugador(client_id, mapa) >= paises_alternativos

        # Si existe y fue eliminado, objetivo cumplido
        return jugador_objetivo_eliminado

    def _verificar_conquistar_continentes(
        self, client_id: str, objetivo: dict[str, Any], mapa: Any
    ) -> bool:
        """Verifica si se han conquistado los continentes requeridos."""
        continentes_objetivo = objetivo.get("continentes", [])

        for continente in continentes_objetivo:
            if not self._controla_continente_completo(client_id, continente, mapa):
                return False

        return True

    def _verificar_conquistar_paises(
        self, client_id: str, objetivo: dict[str, Any], mapa: Any
    ) -> bool:
        """Verifica si se ha conquistado la cantidad de países requerida."""
        cantidad_objetivo = objetivo.get("cantidad_paises", 24)
        return self._contar_paises_jugador(client_id, mapa) >= cantidad_objetivo

    def _verificar_conquistar_paises_con_tropas(
        self, client_id: str, objetivo: dict[str, Any], mapa: Any
    ) -> bool:
        """Verifica si se han conquistado países con tropas mínimas."""
        cantidad_paises = objetivo.get("cantidad_paises", 18)
        tropas_minimas = objetivo.get("tropas_minimas", 2)

        paises_con_tropas_suficientes = 0

        for pais_data in mapa.values():
            # Estructura: [unidades, continente, jugador, adyacentes, misiles]
            unidades, _, dueno, *_ = pais_data
            if dueno and dueno.userid() == client_id and unidades >= tropas_minimas:
                paises_con_tropas_suficientes += 1

        return paises_con_tropas_suficientes >= cantidad_paises

    def _contar_paises_jugador(self, client_id: str, mapa: Any) -> int:
        """Cuenta la cantidad de países que controla un jugador."""
        contador = 0
        for pais_data in mapa.values():
            # Estructura: [unidades, continente, jugador, adyacentes, misiles]
            _, _, dueno, *_ = pais_data
            if dueno and dueno.userid() == client_id:
                contador += 1
        return contador

    def _controla_continente_completo(
        self, client_id: str, continente: str, mapa: Any
    ) -> bool:
        """Verifica si un jugador controla completamente un continente."""
        paises_continente = self.toml_reader.get_paises(continente)

        for pais in paises_continente:
            pais_data = mapa.get(pais)
            if not pais_data:
                return False

            # Estructura: [unidades, continente, jugador, adyacentes, misiles]
            _, _, dueno, *_ = pais_data  # *_ captura adyacentes y misiles
            if not dueno or dueno.userid() != client_id:
                return False

        return True
