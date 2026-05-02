"""Módulo para broadcast de mensajes a todos los clientes.

Este módulo encapsula la lógica de envío de mensajes a múltiples clientes,
separando esta responsabilidad del Server principal.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pyteg.event_types import (
    EVENT_BATALLA_RESULTADO,
    EVENT_CHAT,
    EVENT_CONFIGURACION_PARTIDA,
    EVENT_ESTADO_CAMBIADO,
    EVENT_MAPA_ACTUALIZADO,
    EVENT_MISIL_AGREGADO,
    EVENT_TARJETAS_ACTUALIZADAS,
    EVENT_VICTORIA,
)
from pyteg.message_bus import get_message_bus

if TYPE_CHECKING:
    from pyteg.server.conexion.cliente import Client


class ServerMessageBroadcaster:
    """Encapsula la lógica de envío de mensajes a todos los clientes.

    Esta clase se encarga de todos los métodos de broadcasting del servidor,
    separando esta responsabilidad del Server principal.
    """

    def __init__(self, get_clients: Any) -> None:
        """Inicializa el broadcaster.

        Args:
            get_clients: Función o método que retorna la lista de clientes.

        """
        self._get_clients = get_clients

    def _dame_clientes(self) -> list[Client]:
        """Obtiene la lista de clientes.

        Returns:
            Lista de clientes conectados.

        """
        clients = self._get_clients()
        if not isinstance(clients, list):
            return []
        return clients

    def enviar_estado(self, estado: str) -> None:
        """Envía el estado actual del juego a todos los clientes.

        Args:
            estado: Estado actual del juego.

        """
        for client in self._dame_clientes():
            client.transmisor.enviar_estado(estado)

        # Publicar evento en MessageBus
        get_message_bus().publish(EVENT_ESTADO_CAMBIADO, {"estado": estado})

    def enviar_chat(self, username: str, msg: str) -> None:
        """Envía un mensaje de chat a todos los clientes.

        Args:
            username: Nombre de usuario del remitente.
            msg: Mensaje de chat.

        """
        for client in self._dame_clientes():
            client.transmisor.enviar_chat(f"{username}: {msg}")

        # Publicar evento en MessageBus
        get_message_bus().publish(EVENT_CHAT, {"username": username, "message": msg})

    def enviar_userid(self) -> None:
        """Envía los IDs de usuario a todos los clientes."""
        for client in self._dame_clientes():
            # Primero enviar el ID del cliente actual (su propio ID)
            client.transmisor.enviar_userid(client.userid())

            # Luego enviar los IDs de los otros clientes
            for otro_client in self._dame_clientes():
                if otro_client.userid() != client.userid():
                    client.transmisor.enviar_userid(otro_client.userid())

    def enviar_username(self) -> None:
        """Envía los nombres de usuario a todos los clientes."""
        for client in self._dame_clientes():
            for otro_client in self._dame_clientes():
                client.transmisor.enviar_username(
                    otro_client.userid(), otro_client.username()
                )

    def enviar_mapa(self, mapa: Any, game: Any) -> None:
        """Envía el estado actual del mapa a todos los clientes.

        Args:
            mapa: Instancia del mapa del juego.
            game: Instancia del juego actual.

        """
        for client in self._dame_clientes():
            client.transmisor.enviar_mapa(mapa, game)

        # Publicar evento en MessageBus
        get_message_bus().publish(EVENT_MAPA_ACTUALIZADO, {})

    def enviar_victoria(self, ganador_id: str, ganador_nombre: str) -> None:
        """Envía el mensaje de victoria a todos los clientes.

        Args:
            ganador_id: ID del jugador ganador.
            ganador_nombre: Nombre del jugador ganador.

        """
        for client in self._dame_clientes():
            client.transmisor.enviar_victoria(ganador_id, ganador_nombre)

        # Publicar evento en MessageBus
        get_message_bus().publish(
            EVENT_VICTORIA,
            {"ganador_id": ganador_id, "ganador_nombre": ganador_nombre},
        )

    def enviar_configuracion_partida(
        self,
        segundos_por_turno: int,
        paises_para_victoria: int,
        *,
        objetivos_secretos: bool = False,
        misiles_habilitados: bool = False,
    ) -> None:
        """Envía la configuración de la partida a todos los clientes.

        Args:
            segundos_por_turno: Segundos por turno.
            paises_para_victoria: Países necesarios para ganar.
            objetivos_secretos: Si los objetivos secretos están activados.
            misiles_habilitados: Si los misiles están habilitados.

        """
        for client in self._dame_clientes():
            client.transmisor.enviar_configuracion_partida(
                segundos_por_turno,
                paises_para_victoria,
                objetivos_secretos=objetivos_secretos,
                misiles_habilitados=misiles_habilitados,
            )

        # Publicar evento en MessageBus
        get_message_bus().publish(
            EVENT_CONFIGURACION_PARTIDA,
            {
                "segundos_por_turno": segundos_por_turno,
                "paises_para_victoria": paises_para_victoria,
                "objetivos_secretos": objetivos_secretos,
                "misiles_habilitados": misiles_habilitados,
            },
        )

    def enviar_resultado_batalla(self, resultado_data: dict[str, Any]) -> None:
        """Envía el resultado de una batalla a todos los clientes.

        Args:
            resultado_data: Datos del resultado de la batalla.

        """
        for client in self._dame_clientes():
            client.transmisor.enviar_resultado_batalla(resultado_data)

        # Publicar evento en MessageBus
        get_message_bus().publish(EVENT_BATALLA_RESULTADO, resultado_data)

    def enviar_resultado_misil(self, resultado_data: dict[str, Any]) -> None:
        """Envía el resultado de un misil a todos los clientes.

        Args:
            resultado_data: Datos del resultado del misil.

        """
        for client in self._dame_clientes():
            client.transmisor.enviar_resultado_misil(resultado_data)

    def enviar_misil_agregado(self, pais: str, cantidad_misiles: int) -> None:
        """Envía notificación de misil agregado a todos los clientes.

        Args:
            pais: País donde se agregó el misil.
            cantidad_misiles: Cantidad total de misiles en el país.

        """
        for client in self._dame_clientes():
            client.transmisor.enviar_misil_agregado(pais, cantidad_misiles)

        # Publicar evento en MessageBus
        get_message_bus().publish(
            EVENT_MISIL_AGREGADO,
            {"pais": pais, "cantidad_misiles": cantidad_misiles},
        )

    def enviar_tarjetas_jugador(
        self, client: Client, tarjetas_data: list[dict[str, str]]
    ) -> None:
        """Envía las tarjetas del jugador específico al cliente.

        Args:
            client: Cliente al que enviar las tarjetas.
            tarjetas_data: Datos de las tarjetas a enviar.

        """
        client.transmisor.enviar_tarjetas_jugador(tarjetas_data)

        # Publicar evento en MessageBus
        get_message_bus().publish(
            EVENT_TARJETAS_ACTUALIZADAS,
            {
                "user_id": client.userid(),
                "username": client.username(),
                "tarjetas": tarjetas_data,
            },
        )

    def enviar_objetivos_secretos(self, get_objetivo_jugador: Any) -> None:
        """Envía el objetivo secreto asignado a cada jugador.

        Args:
            get_objetivo_jugador: Función para obtener objetivo de un jugador.

        """
        for client in self._dame_clientes():
            user_id = client.userid()
            objetivo = get_objetivo_jugador(str(user_id))
            if objetivo:
                client.transmisor.enviar_objetivo_secreto(
                    objetivo["id"], objetivo["descripcion"]
                )
