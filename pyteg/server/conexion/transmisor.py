"""Módulo para manejar la transmisión de mensajes del servidor al cliente."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pyteg.logger import get_logger
from pyteg.server.msg import (
    IMsg,
    MsgActualizarListaJugadores,
    MsgCanjeEspecial,
    MsgChat,
    MsgColor,
    MsgColorAsignado,
    MsgConfiguracionPartida,
    MsgError,
    MsgEstado,
    MsgMisilAgregado,
    MsgObjetivoSecreto,
    MsgPais,
    MsgResultadoBatalla,
    MsgResultadoMisil,
    MsgSosAdmin,
    MsgTarjetasJugador,
    MsgTiempo,
    MsgTurno,
    MsgUnidadesDisponibles,
    MsgUserId,
    MsgUsername,
    MsgVictoria,
)

if TYPE_CHECKING:
    from pyteg.colores import IColor
    from pyteg.server.msg.types import BattleResultPayload, MissileResultPayload


LOGGER = get_logger(__name__)


class ServerTransmisor:
    """Transmisor de mensajes del servidor al cliente."""

    def __init__(self, conn: Any) -> None:
        """Inicializa el transmisor con una conexión.

        Args:
            conn: Conexión al cliente.

        """
        self._conn = conn

    def _send_message(self, msg: IMsg) -> None:
        """Envía un mensaje al cliente.

        Args:
            msg: Mensaje a enviar.

        """
        try:
            json_str = msg.to_json()
            # ConnectionServer.send() espera str y agrega \0 internamente.
            # También funciona con conexiones raw de bytes.
            if isinstance(json_str, str):
                self._conn.send(json_str)
            else:
                self._conn.send(json_str)
        except (ConnectionError, OSError, BrokenPipeError) as e:
            LOGGER.warning("Error al enviar mensaje: %s", e)

    def enviar_chat(self, msg: str) -> None:
        """Envía un mensaje de chat al cliente.

        Args:
            msg: Mensaje de chat a enviar.

        """
        msg_obj = MsgChat(msg)
        self._send_message(msg_obj)

    def enviar_error_chat(self, msg: str) -> None:
        """Envía un mensaje de error al chat del cliente."""
        msg_obj = MsgChat(msg, msg_type="error")
        self._send_message(msg_obj)

    def enviar_sistema(self, msg: str) -> None:
        """Envía un mensaje del sistema al chat del cliente."""
        msg_obj = MsgChat(msg, msg_type="system")
        self._send_message(msg_obj)

    def sos_admin(self) -> None:
        """Notifica al cliente que es administrador."""
        msg = MsgSosAdmin()
        self._send_message(msg)

    def color_asignado(self, id_user: int, color: IColor) -> None:
        """Envía notificación de color asignado a un usuario.

        Args:
            id_user: ID del usuario.
            color: Color asignado.

        """
        msg = MsgColorAsignado(id_user, color.to_json())
        self._send_message(msg)

    def enviar_userid(self, user_id: int) -> None:
        """Envía el ID de usuario al cliente.

        Args:
            user_id: ID de usuario a enviar.

        """
        msg = MsgUserId(user_id)
        self._send_message(msg)

    def enviar_username(self, userid: int, username: str) -> None:
        """Envía el nombre de usuario al cliente.

        Args:
            userid: ID del usuario.
            username: Nombre de usuario.

        """
        LOGGER.debug("enviar_username, userid=%s, username=%s", userid, username)
        msg = MsgUsername(userid, username)
        self._send_message(msg)

    def enviar_colores(self, colores: list[IColor]) -> None:
        """Envía la lista de colores disponibles al cliente.

        Args:
            colores: Lista de colores disponibles.

        """
        for color in colores:
            msg = MsgColor(color)
            self._send_message(msg)

    def enviar_estado(self, estado: str) -> None:
        """Envía el estado actual del juego al cliente.

        Args:
            estado: Estado actual del juego.

        """
        msg = MsgEstado(estado)
        self._send_message(msg)

    def enviar_tiempo(self, userid_turno: int, tiempo_restante: int) -> None:
        """Envía el tiempo restante del turno al cliente.

        Args:
            userid_turno: ID del usuario en turno.
            tiempo_restante: Tiempo restante en segundos.

        """
        msg = MsgTiempo(userid_turno, tiempo_restante)
        self._send_message(msg)

    def enviar_unidades_disponibles(self, unidades: dict[str, int]) -> None:
        """Envía la cantidad de unidades disponibles para colocar al jugador.

        Args:
            unidades (dict): Diccionario con el tipo de unidad y la cantidad disponible.
                Ejemplo: {"infanteria": 5, "artilleria": 2, "caballeria": 1}

        """
        msg = MsgUnidadesDisponibles(unidades)
        self._send_message(msg)

    def enviar_pais(self, pais: str, userid: int | None, unidades: int) -> None:
        """Envía información de un país al cliente.

        Args:
            pais: Nombre del país.
            userid: userid (int) del jugador que ocupa el país, o None si no tiene
                dueño.
            unidades: Cantidad de unidades en el país.

        """
        msg = MsgPais(pais, userid, unidades)
        self._send_message(msg)

    def enviar_turno(
        self,
        num_turno: int,
        num_ronda: int,
        jugador_actual_id: int | None = None,
        jugador_actual_nombre: str | None = None,
        jugador_actual_color: str | None = None,
    ) -> None:
        """Envía el número de turno y ronda actuales a los clientes.

        Args:
            num_turno (int): El número de turno actual
            num_ronda (int): El número de ronda actual
            jugador_actual_id (int, optional): ID del jugador actual
            jugador_actual_nombre (str, optional): Nombre del jugador actual
            jugador_actual_color (str, optional): Color del jugador actual

        """
        msg = MsgTurno(
            num_turno,
            num_ronda,
            jugador_actual_id,
            jugador_actual_nombre,
            jugador_actual_color,
        )
        self._send_message(msg)

    def actualizar_lista_jugadores(
        self, jugadores: list[tuple[int, dict[str, int]]]
    ) -> None:
        """Envía la lista actualizada de jugadores al cliente.

        Args:
            jugadores (list): Lista de tuplas (userid, color) donde color es un
                diccionario con las claves 'r', 'g', 'b'

        """
        msg = MsgActualizarListaJugadores(jugadores)
        self._send_message(msg)

    def enviar_mapa(self, mapa: Any, game: Any) -> None:  # noqa: ARG002
        """Envía el estado actual del mapa al cliente.

        Args:
            mapa: Instancia del mapa del juego.
            game: Instancia del juego actual (sin uso aquí, las unidades
                disponibles se envían vía `enviar_unidades_disponibles`).

        """
        for pais in mapa.paises():
            unidades = mapa.cantidad_unidades(pais)
            userid = mapa.ocupado_por(pais)
            LOGGER.debug("%s userid=%s unidades=%s", pais, userid, unidades)
            self.enviar_pais(pais, userid, unidades)

    def enviar_resultado_batalla(self, batalla_data: BattleResultPayload) -> None:
        """Envía el resultado de una batalla al cliente.

        Args:
            batalla_data: Payload tipado con los datos de la batalla.
                Ver `pyteg.server.msg.types.BattleResultPayload`.

        """
        msg = MsgResultadoBatalla(batalla_data)
        self._send_message(msg)

    def enviar_error(self, error_type: str, message: str) -> None:
        """Envía un mensaje de error al cliente.

        Args:
            error_type (str): Tipo de error (ej: "duplicate_username")
            message (str): Mensaje descriptivo del error

        """
        msg = MsgError(error_type, message)
        self._send_message(msg)

    def enviar_victoria(self, ganador_id: int, ganador_nombre: str) -> None:
        """Envía un mensaje de victoria al cliente.

        Args:
            ganador_id: userid (int) del jugador ganador.
            ganador_nombre: Nombre del jugador ganador (UI/chat).

        """
        msg = MsgVictoria(ganador_id, ganador_nombre)
        self._send_message(msg)

    def enviar_configuracion_partida(
        self,
        segundos_por_turno: int,
        paises_para_victoria: int,
        *,
        objetivos_secretos: bool = False,
        misiles_habilitados: bool = False,
    ) -> None:
        """Envía la configuración de la partida al cliente.

        Args:
            segundos_por_turno (int): Duración de cada turno en segundos
            paises_para_victoria (int): Número de países necesarios para ganar
            objetivos_secretos (bool): Si los objetivos secretos están activados
            misiles_habilitados (bool): Si el sistema de misiles está habilitado

        """
        msg = MsgConfiguracionPartida(
            segundos_por_turno,
            paises_para_victoria,
            objetivos_secretos=objetivos_secretos,
            misiles_habilitados=misiles_habilitados,
        )
        self._send_message(msg)

    def enviar_tarjetas_jugador(self, tarjetas: list[dict[str, str]]) -> None:
        """Envía las tarjetas del jugador al cliente.

        Args:
            tarjetas (list): Lista de tarjetas con formato
                [{"pais": str, "simbolo": str}, ...]

        """
        msg = MsgTarjetasJugador(tarjetas)
        self._send_message(msg)

    def enviar_objetivo_secreto(self, objetivo_id: str, descripcion: str) -> None:
        """Envía el objetivo secreto asignado al jugador.

        Args:
            objetivo_id (str): ID del objetivo secreto
            descripcion (str): Descripción del objetivo secreto

        """
        LOGGER.debug(
            "Enviando objetivo secreto - ID: %s, Desc: %s",
            objetivo_id,
            descripcion,
        )
        msg = MsgObjetivoSecreto(objetivo_id, descripcion)
        self._send_message(msg)

    def enviar_canje_especial(self, pais: str, unidades_agregadas: int) -> None:
        """Envía notificación de canje especial al cliente.

        Args:
            pais (str): Nombre del país donde se agregaron las unidades
            unidades_agregadas (int): Cantidad de unidades agregadas

        """
        msg = MsgCanjeEspecial(pais, unidades_agregadas)
        self._send_message(msg)

    def enviar_resultado_misil(self, resultado_data: MissileResultPayload) -> None:
        """Envía el resultado del lanzamiento de un misil al cliente.

        Args:
            resultado_data: Payload tipado con los datos del misil. Ver
                `pyteg.server.msg.types.MissileResultPayload`.

        """
        msg = MsgResultadoMisil(resultado_data)
        self._send_message(msg)

    def enviar_misil_agregado(self, pais: str, cantidad_misiles: int) -> None:
        """Envía notificación de que se agregó un misil a un país.

        Args:
            pais (str): Nombre del país donde se agregó el misil
            cantidad_misiles (int): Cantidad total de misiles en el país

        """
        msg = MsgMisilAgregado(pais, cantidad_misiles)
        self._send_message(msg)
