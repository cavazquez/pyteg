"""Protocolos (interfaces) para mejorar type safety.

Este módulo define protocolos que especifican las interfaces necesarias
para diferentes componentes del sistema, permitiendo reemplazar `Any`
con tipos específicos y mejorar la seguridad de tipos.

Organización por dominio
------------------------
- **Cliente / servidor**: `IClientProtocol`, `ServerLikeProtocol` — borde entre el
  cliente conectado y el objeto servidor en tareas del servidor.
- **Reglas de juego**: `IGameProtocol` — turnos, batalla, tarjetas, mazo.
- **Mapa**: `IMapProtocol` — unidades, ocupación, misiles, distancias.

Estabilidad
-----------
Los protocolos son contratos de tipado para el código del monorepo; no constituyen
una API pública versionada como librería externa. Los cambios deben ir acompañados
de actualizaciones en las implementaciones concretas bajo `pyteg`.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol

from pyteg.server.juego.state_validator import HasEstado

if TYPE_CHECKING:
    from pyteg.colores import IColor
    from pyteg.core.turnos.protocol import ITurno
    from pyteg.server.conexion.transmisor import ServerTransmisor


class IClientProtocol(Protocol):
    """Protocolo para objetos cliente del servidor.

    Define la interfaz mínima que debe implementar un cliente
    para ser usado en las tareas del servidor.
    """

    @property
    def transmisor(self) -> ServerTransmisor:
        """Transmisor de mensajes del cliente."""
        ...

    @property
    def server(self) -> ServerLikeProtocol:
        """Referencia al servidor."""
        ...


class ServerLikeProtocol(HasEstado, Protocol):
    """Protocolo para objetos que actúan como servidor.

    Define la interfaz mínima que debe implementar un objeto servidor
    para ser usado en las tareas del servidor.
    Extiende HasEstado para compatibilidad con validadores.
    """

    @property
    def mapa(self) -> IMapProtocol:
        """Mapa del juego."""
        ...

    @property
    def game(self) -> IGameProtocol | None:
        """Juego actual (puede ser None si no ha comenzado)."""
        ...

    def enviar_mapa(self) -> None:
        """Envía el mapa actualizado a todos los clientes."""
        ...

    def enviar_unidades_disponibles(self) -> None:
        """Envía las unidades disponibles al jugador actual."""
        ...

    def enviar_resultado_batalla(self, resultado: dict[str, Any]) -> None:
        """Envía el resultado de una batalla a todos los clientes."""
        ...

    def enviar_misil_agregado(self, pais: str, cantidad_misiles: int) -> None:
        """Envía notificación de misil agregado."""
        ...

    def enviar_tarjetas_jugador(self, client: IClientProtocol) -> None:
        """Envía las tarjetas del jugador."""
        ...

    def enviar_turno_actual(self) -> None:
        """Envía el turno actual a todos los clientes."""
        ...

    def misiles_habilitados(self) -> bool:
        """Retorna si los misiles están habilitados."""
        ...

    def dame_clientes(self) -> list[IClientProtocol]:
        """Obtiene la lista de clientes."""
        ...

    def userid(self) -> int:
        """Obtiene el ID de usuario del cliente.

        Returns:
            ID de usuario del cliente.

        """
        ...

    def username(self) -> str:
        """Obtiene el nombre de usuario del cliente.

        Returns:
            Nombre de usuario del cliente.

        """
        ...

    def es_admin(self) -> bool:
        """Verifica si el cliente es administrador.

        Returns:
            True si es administrador, False en caso contrario.

        """
        ...

    def color_actual(self) -> IColor | None:
        """Obtiene el color actual del cliente.

        Returns:
            Color actual del cliente o None.

        """
        ...


class IGameProtocol(Protocol):
    """Protocolo para objetos de juego.

    Define la interfaz mínima que debe implementar un objeto de juego
    para ser usado en las tareas del servidor.
    """

    def empezo(self) -> bool:
        """Verifica si el juego ha comenzado.

        Returns:
            True si el juego ha comenzado, False en caso contrario.

        """
        ...

    def turno_actual(self) -> ITurno:
        """Obtiene el turno actual.

        Returns:
            El turno actual.

        """
        ...

    def turnos(self) -> list[ITurno]:
        """Obtiene la lista de turnos.

        Returns:
            Lista de turnos.

        """
        ...

    def id_turno_actual(self) -> int:
        """Obtiene el índice del turno actual.

        Returns:
            Índice del turno actual.

        """
        ...

    def num_ronda(self) -> int:
        """Obtiene el número de ronda actual.

        Returns:
            Número de ronda.

        """
        ...

    def mazo(self) -> object:  # Mazo, pero evitamos import circular
        """Obtiene el mazo de tarjetas.

        Returns:
            El mazo de tarjetas.

        """
        ...

    def atacar(
        self,
        pais_atacante: str,
        pais_defensor: str,
        unidades_atacantes: int,
    ) -> dict[str, Any]:
        """Realiza un ataque entre dos países.

        Args:
            pais_atacante: País que ataca.
            pais_defensor: País que defiende.
            unidades_atacantes: Cantidad de unidades que atacan.

        Returns:
            Diccionario con el resultado del ataque.

        """
        ...

    def marcar_jugador_puede_reclamar(self, jugador: IClientProtocol) -> None:
        """Marca que un jugador puede reclamar una tarjeta.

        Args:
            jugador: Jugador que puede reclamar.

        """
        ...

    def puede_reclamar_tarjeta(self, jugador: IClientProtocol) -> bool:
        """Verifica si un jugador puede reclamar una tarjeta.

        Args:
            jugador: Jugador a verificar.

        Returns:
            True si puede reclamar, False en caso contrario.

        """
        ...

    def dame_una_tarjeta(self, jugador: IClientProtocol) -> None:
        """Asigna una tarjeta a un jugador.

        Args:
            jugador: Jugador al que asignar la tarjeta.

        """
        ...

    def reclamar_tarjeta_jugador(self, jugador: IClientProtocol) -> None:
        """Reclama una tarjeta para un jugador.

        Args:
            jugador: Jugador que reclama la tarjeta.

        """
        ...

    def limpiar_elegibilidad_reclamar(self) -> None:
        """Limpia la elegibilidad de reclamar tarjetas."""
        ...

    def finalizar_turno(self) -> None:
        """Finaliza el turno actual."""
        ...

    def mapa(self) -> IMapProtocol:
        """Obtiene el mapa del juego.

        Returns:
            El mapa del juego.

        """
        ...


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

    def ocupado_por(self, pais: str) -> str:
        """Obtiene el jugador que ocupa un país.

        Args:
            pais: Nombre del país.

        Returns:
            ID del jugador que ocupa el país.

        """
        ...

    def paises(self) -> list[str]:
        """Obtiene la lista de todos los países del mapa.

        Returns:
            Lista de nombres de países.

        """
        ...

    def asignar_pais(self, jugador: str, pais: str) -> None:
        """Asigna un país a un jugador.

        Args:
            jugador: ID del jugador.
            pais: Nombre del país.

        """
        ...

    def jugador_posee_pais(self, jugador: str, pais: str) -> bool:
        """Verifica si un jugador específico posee un país determinado.

        Args:
            jugador: ID del jugador.
            pais: Nombre del país.

        Returns:
            True si el jugador posee el país, False en caso contrario.

        """
        ...

    def jugador_controla_continente(self, jugador: str, continente: str) -> bool:
        """Verifica si un jugador controla completamente un continente.

        Args:
            jugador: ID del jugador.
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
