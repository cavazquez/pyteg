"""Módulo para gestionar objetivos secretos del juego."""

from __future__ import annotations

import random
from typing import TYPE_CHECKING, Any, Protocol, cast

from pyteg.logger import get_logger

if TYPE_CHECKING:
    from collections.abc import Callable

    from pyteg.server.juego.mapa import Mapa

LOGGER = get_logger("server.objetivos_secretos")
_MIN_RELATIVE_PLAYERS = 2
_REVANCHA_TWO_PLAYERS = 2
_REVANCHA_THREE_PLAYERS = 3
_REVANCHA_EXTRA_COUNTRIES = 10
_REVANCHA_EXCLUDED_COUNTRY_OBJECTIVE = 35


class SecretObjectiveEvaluator(Protocol):
    """Contrato para asignar y evaluar objetivos secretos."""

    def reiniciar(self) -> None:
        """Descarta el estado de objetivos de la partida."""

    def asignar_objetivos_aleatorios(self, clientes: list[Any]) -> None:
        """Asigna objetivos a los clientes que participan de una partida."""

    def get_objetivo_jugador(self, client_id: int) -> dict[str, Any] | None:
        """Obtiene el objetivo privado de un jugador, si existe."""

    def verificar_condicion_victoria(
        self, client_id: int, mapa: Mapa, colores: Any
    ) -> bool:
        """Indica si el jugador cumplió su objetivo secreto."""

    def set_player_order(self, provider: Callable[[], list[int]]) -> None:
        """Configura el orden de turnos usado por objetivos relativos."""


class NoSecretObjectives:
    """Implementación nula cuando la partida no usa objetivos secretos."""

    def reiniciar(self) -> None:
        """No conserva estado entre partidas."""

    def asignar_objetivos_aleatorios(self, _clientes: list[Any]) -> None:
        """No asigna objetivos a los clientes."""

    def get_objetivo_jugador(self, _client_id: int) -> dict[str, Any] | None:
        """Devuelve que el jugador no tiene objetivo secreto.

        Returns:
            Siempre ``None``.

        """
        objetivo: dict[str, Any] | None = None
        return objetivo

    def verificar_condicion_victoria(
        self, _client_id: int, _mapa: Mapa, _colores: Any
    ) -> bool:
        """Indica que ningún objetivo secreto puede producir una victoria.

        Returns:
            Siempre ``False``.

        """
        return False

    def set_player_order(self, _provider: Callable[[], list[int]]) -> None:
        """Acepta la configuración para mantener el contrato del evaluador nulo."""


NO_SECRET_OBJECTIVES = NoSecretObjectives()


class ObjetivosSecretos:
    """Maneja la asignación y verificación de objetivos secretos para los jugadores."""

    def __init__(self, toml_reader: Any, *, rng: random.Random | None = None) -> None:
        """Inicializa el sistema de objetivos secretos.

        Args:
            toml_reader: Instancia de TomlReader con objetivos secretos cargados
            rng: Fuente aleatoria para barajar objetivos. Si no se proporciona,
                se usa ``SystemRandom`` para conservar entropía del sistema.

        """
        self.toml_reader = toml_reader
        self.objetivos_disponibles = dict(toml_reader.get_objetivos_secretos())
        self.objetivos_comunes = {
            objetivo_id: objetivo
            for objetivo_id, objetivo in self.objetivos_disponibles.items()
            if bool(objetivo.get("objetivo_comun", False))
        }
        self.objetivos_asignables = {
            objetivo_id: objetivo
            for objetivo_id, objetivo in self.objetivos_disponibles.items()
            if not bool(objetivo.get("objetivo_comun", False))
        }
        self._rng = rng if rng is not None else random.SystemRandom()
        # client_userid (int) -> objetivo_id (str)
        self.objetivos_asignados: dict[int, str] = {}
        self.objetivos_adicionales: dict[int, str] = {}
        self._revancha_players: int | None = None
        self._player_order: Callable[[], list[int]] | None = None

    def reiniciar(self) -> None:
        """Descarta objetivos de la partida anterior."""
        self.objetivos_asignados.clear()
        self.objetivos_adicionales.clear()
        self._revancha_players = None

    def asignar_objetivos_aleatorios(
        self, clientes: list[Any], *, revancha_players: int | None = None
    ) -> None:
        """Asigna objetivos secretos aleatorios a una lista de clientes.

        Args:
            clientes: Lista de objetos cliente con atributo user_id
            revancha_players: Cantidad inicial de jugadores de Revancha.

        Raises:
            ValueError: Si faltan objetivos válidos para repartir sin repetir.

        """
        self.objetivos_asignados.clear()
        self.objetivos_adicionales.clear()
        self._revancha_players = (
            revancha_players
            if revancha_players in {_REVANCHA_TWO_PLAYERS, _REVANCHA_THREE_PLAYERS}
            else None
        )
        if not clientes:
            return

        # Los objetivos comunes se publican en las reglas y nunca se entregan
        # como objetivo privado a un jugador.
        objetivos_ids = list(self.objetivos_asignables.keys())
        if self._revancha_players is not None:
            objetivos_ids = [
                objetivo_id
                for objetivo_id in objetivos_ids
                if self.objetivos_asignables[objetivo_id].get("tipo")
                != "destruir_jugador"
                and self.objetivos_asignables[objetivo_id].get("cantidad_paises")
                != _REVANCHA_EXCLUDED_COUNTRY_OBJECTIVE
            ]
        if not objetivos_ids:
            LOGGER.warning(
                "No hay objetivos secretos definidos en el tema; omitiendo asignación"
            )
            return

        self._rng.shuffle(objetivos_ids)
        required_cards = len(clientes) * (
            _REVANCHA_TWO_PLAYERS
            if self._revancha_players == _REVANCHA_TWO_PLAYERS
            else 1
        )
        if self._revancha_players is not None and len(objetivos_ids) < required_cards:
            msg = "No hay suficientes objetivos válidos para esta partida de Revancha"
            raise ValueError(msg)

        LOGGER.info("=== ASIGNANDO OBJETIVOS SECRETOS ===")
        LOGGER.info("Objetivos disponibles: %s", objetivos_ids)
        LOGGER.info("Clientes a asignar: %s", len(clientes))

        for i, client in enumerate(clientes):
            card_index = i * 2 if self._revancha_players == _REVANCHA_TWO_PLAYERS else i
            objetivo_id = objetivos_ids[card_index % len(objetivos_ids)]
            user_id = int(client.userid())
            self.objetivos_asignados[user_id] = objetivo_id
            if self._revancha_players == _REVANCHA_TWO_PLAYERS:
                self.objetivos_adicionales[user_id] = objetivos_ids[card_index + 1]
            LOGGER.info(
                "Asignado objetivo '%s' a cliente %s (ID: %s)",
                objetivo_id,
                client.username(),
                user_id,
            )

        LOGGER.info("Objetivos asignados: %s", self.objetivos_asignados)
        LOGGER.info("=== FIN ASIGNACIÓN OBJETIVOS ===")

    def set_player_order(self, provider: Callable[[], list[int]]) -> None:
        """Usa el orden vivo de turnos para resolver izquierda/derecha.

        El callback se evalúa al comprobar la victoria, por lo que refleja
        rotaciones y jugadores eliminados sin copiar estado de la partida.
        """
        self._player_order = provider

    def get_objetivos_comunes(self) -> list[dict[str, Any]]:
        """Devuelve una copia de los objetivos públicos del tema.

        Returns:
            Objetivos comunes que pueden mostrar todos los clientes.

        """
        return [dict(objetivo) for objetivo in self.objetivos_comunes.values()]

    def get_objetivo_jugador(self, client_id: int) -> dict[str, Any] | None:
        """Obtiene el objetivo secreto asignado a un jugador.

        Args:
            client_id: userid (int) del cliente

        Returns:
            Diccionario con datos del objetivo o None si no tiene asignado

        """
        objetivo_id = self.objetivos_asignados.get(int(client_id))
        if objetivo_id:
            if objetivo_id in self.objetivos_comunes:
                return None
            objetivo = self.toml_reader.get_objetivo_secreto(objetivo_id)
            if objetivo is not None:
                adicional_id = self.objetivos_adicionales.get(int(client_id))
                if adicional_id is not None:
                    adicional = self.toml_reader.get_objetivo_secreto(adicional_id)
                    if adicional is None:
                        return None
                    return {
                        "id": f"{objetivo_id}+{adicional_id}",
                        "descripcion": (
                            "Cumplir ambos objetivos:\n"
                            f"1. {objetivo['descripcion']}\n"
                            f"2. {adicional['descripcion']}"
                        ),
                    }
                if self._revancha_players == _REVANCHA_THREE_PLAYERS:
                    return {
                        **objetivo,
                        "descripcion": (
                            f"{objetivo['descripcion']}\n"
                            "Además, ocupar 10 países adicionales a los "
                            "necesarios para el objetivo."
                        ),
                    }
                return cast("dict[str, Any]", objetivo)
        return None

    def verificar_condicion_victoria(
        self, client_id: int, mapa: Mapa, colores: Any
    ) -> bool:
        """Verifica si un jugador ha cumplido su objetivo secreto.

        Args:
            client_id: userid (int) del cliente
            mapa: Instancia del mapa del juego
            colores: Sistema de colores para identificar jugadores

        Returns:
            True si el jugador ha cumplido su objetivo secreto

        """
        objetivo_id = self.objetivos_asignados.get(int(client_id))
        if objetivo_id is None or objetivo_id in self.objetivos_comunes:
            return False
        objetivo = self.toml_reader.get_objetivo_secreto(objetivo_id)
        if objetivo is None or not self._cumple_objetivo(
            client_id, objetivo, mapa, colores
        ):
            return False
        adicional_id = self.objetivos_adicionales.get(int(client_id))
        if adicional_id is not None:
            adicional = self.toml_reader.get_objetivo_secreto(adicional_id)
            if adicional is None or not self._cumple_objetivo(
                client_id, adicional, mapa, colores
            ):
                return False
        if self._revancha_players == _REVANCHA_THREE_PLAYERS:
            base = self._paises_minimos_objetivo(objetivo, mapa)
            return (
                self._cantidad_paises_exclusivos(client_id, mapa)
                >= base + _REVANCHA_EXTRA_COUNTRIES
            )
        return True

    def _cumple_objetivo(
        self, client_id: int, objetivo: dict[str, Any], mapa: Mapa, colores: Any
    ) -> bool:
        """Evalúa una tarjeta individual, también dentro de un objetivo doble.

        Returns:
            ``True`` si se cumplió la tarjeta.

        """
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

    def _paises_minimos_objetivo(self, objetivo: dict[str, Any], mapa: Mapa) -> int:
        """Cuenta los países mínimos exigidos antes de los diez extras.

        Returns:
            Mínimo de países para cumplir la tarjeta sin el requisito adicional.

        """
        paises = self._paises(mapa)
        requeridos: dict[str, int] = {}
        for continente in objetivo.get("continentes", []):
            requeridos[str(continente)] = sum(
                self._continente(mapa, pais) == continente for pais in paises
            )
        for continente, cantidad in objetivo.get("cuotas_continentes", {}).items():
            nombre = str(continente)
            requeridos[nombre] = max(requeridos.get(nombre, 0), int(cantidad))

        base = sum(requeridos.values())
        islas_requeridas = int(objetivo.get("islas", 0))
        continentes_islas = int(objetivo.get("continentes_minimos_islas", 0))
        if islas_requeridas:
            islas_disponibles = {
                continente: sum(
                    self._continente(mapa, pais) == continente
                    and self._es_isla(mapa, pais)
                    for pais in paises
                )
                for continente in requeridos
            }
            islas_incluidas = sum(
                min(cantidad, islas_disponibles[continente])
                for continente, cantidad in requeridos.items()
            )
            continentes_incluidos = sum(
                cantidad > 0 and islas_disponibles[continente] > 0
                for continente, cantidad in requeridos.items()
            )
            base += max(
                0,
                islas_requeridas - islas_incluidas,
                continentes_islas - continentes_incluidos,
            )
        return max(base, int(objetivo.get("cantidad_paises", 0)))

    def _verificar_destruir_jugador(
        self, client_id: int, objetivo: dict[str, Any], mapa: Mapa, colores: Any
    ) -> bool:
        """Verifica si se ha destruido completamente al jugador objetivo.

        Returns:
            True si el jugador objetivo ha sido destruido, False en caso contrario.

        """
        all_clients = self._all_clients(colores)
        color_objetivo = self._normalizar_color(objetivo.get("color_objetivo"))
        objetivo_id: int | None = None

        for client in all_clients:
            cid = self._client_id(client)
            if cid is None or self._client_color(client, colores) != color_objetivo:
                continue
            if cid != int(client_id):
                objetivo_id = cid
                break

        # La carta sólo puede apuntar al color elegido si ese color está
        # ocupado por otro jugador. Si no, el reglamento manda usar el vecino
        # de la derecha/izquierda o la alternativa de países.
        if objetivo_id is not None:
            return not self._jugador_tiene_paises(objetivo_id, mapa)

        relativo = objetivo.get("objetivo_relativo") or objetivo.get(
            "jugador_alternativo"
        )
        if objetivo_id is None and relativo in {"derecha", "izquierda"}:
            relativo_id = self._jugador_relativo(int(client_id), str(relativo), colores)
            if relativo_id is not None and relativo_id != int(client_id):
                return not self._jugador_tiene_paises(relativo_id, mapa)

        paises_alternativos = int(objetivo.get("paises_alternativos", 24))
        return (
            self._cantidad_paises_exclusivos(int(client_id), mapa)
            >= paises_alternativos
        )

    def _jugador_tiene_paises(self, jugador_id: int, mapa: Mapa) -> bool:
        tiene_paises = getattr(mapa, "tiene_paises", None)
        if callable(tiene_paises):
            try:
                resultado = tiene_paises(jugador_id)
                if isinstance(resultado, bool):
                    return resultado
            except AttributeError, TypeError, ValueError:
                pass
        cantidad = getattr(mapa, "cantidad_de_paises_del_jugador", None)
        if not callable(cantidad):
            return False
        try:
            return int(cantidad(jugador_id, incluir_condominios=True)) > 0
        except TypeError, ValueError:
            return int(cantidad(jugador_id)) > 0

    def _all_clients(self, colores: Any) -> list[Any]:
        """Obtiene clientes desde el servidor o desde un doble de pruebas.

        Returns:
            Clientes disponibles para resolver colores y orden relativo.

        """
        dame_clientes = getattr(colores, "dame_clientes", None)
        if callable(dame_clientes):
            try:
                return list(dame_clientes())
            except AttributeError, RuntimeError, TypeError:
                return []
        return []

    @staticmethod
    def _client_id(client: Any) -> int | None:
        userid = getattr(client, "userid", None)
        if not callable(userid):
            return None
        try:
            return int(userid())
        except TypeError, ValueError:
            return None

    def _client_color(self, client: Any, colores: Any) -> str | None:
        get_color = getattr(colores, "get_color_name", None)
        if callable(get_color):
            try:
                value = get_color(client)
                if value is not None:
                    return self._normalizar_color(value)
            except AttributeError, RuntimeError, TypeError:
                pass
        color_actual = getattr(client, "color_actual", None)
        if not callable(color_actual):
            return None
        try:
            color = color_actual()
        except AttributeError, RuntimeError, TypeError:
            return None
        if color is None:
            return None
        nombre = getattr(color, "nombre", None) or type(color).__name__
        return self._normalizar_color(nombre)

    @staticmethod
    def _normalizar_color(color: Any) -> str | None:
        if color is None:
            return None
        texto = str(color).strip().lower()
        return {
            "rojo": "rojo",
            "red": "rojo",
            "azul": "azul",
            "blue": "azul",
            "verde": "verde",
            "green": "verde",
            "amarillo": "amarillo",
            "yellow": "amarillo",
            "negro": "negro",
            "black": "negro",
            "blanco": "blanco",
            "white": "blanco",
            "violeta": "violeta",
            "morado": "violeta",
            "purple": "violeta",
        }.get(texto, texto)

    def _jugador_relativo(
        self, client_id: int, direccion: str, colores: Any
    ) -> int | None:
        orden: list[int] = []
        if self._player_order is not None:
            try:
                orden = [int(player_id) for player_id in self._player_order()]
            except AttributeError, RuntimeError, TypeError, ValueError:
                orden = []
        if not orden:
            orden = [
                client_id_value
                for client in self._all_clients(colores)
                if (client_id_value := self._client_id(client)) is not None
            ]
        if client_id not in orden or len(orden) < _MIN_RELATIVE_PLAYERS:
            return None
        desplazamiento = 1 if direccion.lower() == "derecha" else -1
        return orden[(orden.index(client_id) + desplazamiento) % len(orden)]

    def _paises(self, mapa: Mapa) -> list[str]:
        paises = getattr(mapa, "paises", None)
        if not callable(paises):
            return []
        try:
            return [str(pais) for pais in paises()]
        except AttributeError, TypeError, ValueError:
            return []

    def _posee_exclusivamente(self, client_id: int, pais: str, mapa: Mapa) -> bool:
        ocupado_por = getattr(mapa, "ocupado_por", None)
        if callable(ocupado_por):
            try:
                propietario = ocupado_por(pais)
                if isinstance(propietario, int):
                    return propietario == int(client_id)
            except AttributeError, RuntimeError, TypeError, ValueError:
                pass
        es_condominio = getattr(mapa, "es_condominio", None)
        if callable(es_condominio):
            try:
                if es_condominio(pais) is True:
                    return False
            except AttributeError, RuntimeError, TypeError, ValueError:
                pass
        posee = getattr(mapa, "jugador_posee_pais", None)
        if callable(posee):
            try:
                resultado = posee(client_id, pais)
                return resultado if isinstance(resultado, bool) else False
            except AttributeError, RuntimeError, TypeError, ValueError:
                pass
        return False

    def _paises_exclusivos(self, client_id: int, mapa: Mapa) -> list[str]:
        paises = self._paises(mapa)
        if paises:
            return [
                pais
                for pais in paises
                if self._posee_exclusivamente(client_id, pais, mapa)
            ]
        return []

    def _cantidad_paises_exclusivos(self, client_id: int, mapa: Mapa) -> int:
        propios = self._paises_exclusivos(client_id, mapa)
        if propios:
            return len(propios)
        cantidad = getattr(mapa, "cantidad_de_paises_del_jugador", None)
        if callable(cantidad):
            try:
                valor = cantidad(client_id)
                if isinstance(valor, int):
                    return valor
            except AttributeError, RuntimeError, TypeError, ValueError:
                pass
        return 0

    def _continente(self, mapa: Mapa, pais: str) -> str | None:
        continente = getattr(mapa, "continente", None)
        if not callable(continente):
            return None
        try:
            return str(continente(pais))
        except AttributeError, RuntimeError, TypeError, ValueError:
            return None

    def _cumple_cuotas(
        self,
        objetivo: dict[str, Any],
        mapa: Mapa,
        propios: list[str],
    ) -> bool:
        cuotas = objetivo.get("cuotas_continentes", {})
        if not isinstance(cuotas, dict):
            return False
        for continente, cuota in cuotas.items():
            try:
                requerida = int(cuota)
            except TypeError, ValueError:
                return False
            cantidad = sum(
                1 for pais in propios if self._continente(mapa, pais) == str(continente)
            )
            if cantidad < requerida:
                return False
        return True

    def _es_isla(self, mapa: Mapa, pais: str) -> bool:
        es_isla = getattr(mapa, "es_isla", None)
        if callable(es_isla):
            try:
                return bool(es_isla(pais))
            except AttributeError, RuntimeError, TypeError, ValueError:
                pass
        adyacentes = getattr(mapa, "obtener_paises_adyacentes", None)
        if callable(adyacentes):
            try:
                return len(adyacentes(pais)) == 0
            except AttributeError, RuntimeError, TypeError, ValueError:
                pass
        return False

    def _cumple_islas(
        self, objetivo: dict[str, Any], mapa: Mapa, propios: list[str]
    ) -> bool:
        requeridas = objetivo.get("islas")
        if requeridas is None:
            return True
        try:
            requeridas_int = int(requeridas)
            minimo_continentes = int(objetivo.get("continentes_minimos_islas", 1))
        except TypeError, ValueError:
            return False
        islas = [pais for pais in propios if self._es_isla(mapa, pais)]
        continentes = {
            continente
            for pais in islas
            if (continente := self._continente(mapa, pais)) is not None
        }
        return len(islas) >= requeridas_int and len(continentes) >= minimo_continentes

    def _verificar_conquistar_continentes(
        self, client_id: int, objetivo: dict[str, Any], mapa: Mapa
    ) -> bool:
        """Verifica si se han conquistado los continentes requeridos.

        Returns:
            True si se han conquistado los continentes requeridos,
            False en caso contrario.

        """
        propios = self._paises_exclusivos(client_id, mapa)
        continentes_objetivo = objetivo.get("continentes", [])

        for continente in continentes_objetivo:
            if not mapa.jugador_controla_continente(client_id, continente):
                return False

        return self._cumple_cuotas(objetivo, mapa, propios) and self._cumple_islas(
            objetivo, mapa, propios
        )

    def _verificar_conquistar_paises(
        self, client_id: int, objetivo: dict[str, Any], mapa: Mapa
    ) -> bool:
        """Verifica si se ha conquistado la cantidad de países requerida.

        Returns:
            True si se ha conquistado la cantidad requerida, False en caso contrario.

        """
        cantidad_objetivo = int(objetivo.get("cantidad_paises", 24))
        propios = self._paises_exclusivos(client_id, mapa)
        paises_count = (
            len(propios)
            if propios
            else self._cantidad_paises_exclusivos(client_id, mapa)
        )
        return bool(
            paises_count >= cantidad_objetivo
            and self._cumple_cuotas(objetivo, mapa, propios)
            and self._cumple_islas(objetivo, mapa, propios)
        )

    def _verificar_conquistar_paises_con_tropas(
        self, client_id: int, objetivo: dict[str, Any], mapa: Mapa
    ) -> bool:
        """Verifica si se han conquistado países con tropas mínimas.

        Returns:
            True si se han conquistado los países requeridos, False en caso contrario.

        """
        cantidad_paises = objetivo.get("cantidad_paises", 18)
        tropas_minimas = objetivo.get("tropas_minimas", 2)

        paises_con_tropas_suficientes = 0

        for pais in self._paises_exclusivos(client_id, mapa):
            cantidad_unidades = getattr(mapa, "cantidad_unidades", None)
            if callable(cantidad_unidades):
                try:
                    unidades = cantidad_unidades(pais)
                except AttributeError, RuntimeError, TypeError, ValueError:
                    continue
                if isinstance(unidades, int) and unidades >= tropas_minimas:
                    paises_con_tropas_suficientes += 1

        return bool(paises_con_tropas_suficientes >= cantidad_paises)
