"""Transmisor real: serializa Msg* y los envía por la conexión."""

from __future__ import annotations

from typing import Any

from pyteg.client.conexion.transmisor.protocol import IClientTransmisor
from pyteg.client_msg import (
    MsgAgregarUnidad,
    MsgAtacar,
    MsgCanjearMisil,
    MsgCanjeEspecial,
    MsgChat,
    MsgEmpezar,
    MsgEmpezarPartida,
    MsgFinalizarTurno,
    MsgLanzarMisil,
    MsgMoverUnidad,
    MsgReclamarTarjeta,
    MsgSeleccionarColor,
    MsgSetUsername,
    MsgSolicitarTarjetas,
)
from pyteg.logger import get_logger

_LOG = get_logger("client.transmisor")


class ClientTransmisor(IClientTransmisor):
    """Transmisor de mensajes del cliente al servidor."""

    def __init__(self, conn: Any) -> None:
        """Inicializa el transmisor con una conexión.

        Args:
            conn: Conexión al servidor.

        """
        self._conn = conn

    def enviar_chat(self, msg: str) -> None:
        """Envía un mensaje de chat al servidor.

        Args:
            msg: Mensaje de chat a enviar.

        """
        msg_obj = MsgChat(msg)
        self._conn.send_data(msg_obj.to_json())

    def empezar(
        self,
        segundos: int | None = None,
        paises_para_victoria: int | None = None,
        *,
        objetivos_secretos: bool = False,
        misiles_habilitados: bool = False,
    ) -> None:
        """Inicia la configuración de la partida.

        Args:
            segundos: Tiempo límite por turno en segundos.
            paises_para_victoria: Cantidad de países necesarios para ganar.
            objetivos_secretos: Si los objetivos secretos están habilitados.
            misiles_habilitados: Si los misiles están habilitados.

        """
        _LOG.debug("Transmisor empezar()")
        msg = MsgEmpezar(
            segundos,
            paises_para_victoria,
            objetivos_secretos=objetivos_secretos,
            misiles_habilitados=misiles_habilitados,
        )
        self._conn.send_data(msg.to_json())

    def seleccionar_color(self, color: Any) -> None:
        """Selecciona un color para el jugador.

        Args:
            color: Color a seleccionar.

        """
        _LOG.debug("Selecciono color")
        msg = MsgSeleccionarColor(color)
        self._conn.send_data(msg.to_json())

    def empezar_partida(self) -> None:
        """Inicia la partida."""
        _LOG.debug("empezar_partida")
        msg = MsgEmpezarPartida()
        self._conn.send_data(msg.to_json())

    def set_username(self, username: str) -> None:
        """Establece el nombre de usuario.

        Args:
            username: Nombre de usuario a establecer.

        """
        msg = MsgSetUsername(username)
        self._conn.send_data(msg.to_json())

    def agregar_unidad(self, pais: str, tipo_unidad: str, cantidad: int = 1) -> None:
        """Envía un mensaje al servidor para agregar unidades en un país específico.

        Args:
            pais (str): Nombre del país donde se agregará la unidad
            tipo_unidad (str): Tipo de unidad a agregar (ej: 'infanteria', 'misil')
            cantidad (int, optional): Cantidad de unidades a agregar. Defaults to 1.

        """
        _LOG.debug(
            "Agregando %s unidad(es) de tipo %s en %s", cantidad, tipo_unidad, pais
        )
        msg = MsgAgregarUnidad(pais, tipo_unidad, cantidad)
        self._conn.send_data(msg.to_json())

    def mover_unidad(self, origen: str, destino: str, cantidad: int = 1) -> None:
        """Envía un mensaje al servidor para mover unidades entre países.

        Args:
            origen (str): Nombre del país de origen
            destino (str): Nombre del país de destino
            cantidad (int, optional): Cantidad de unidades a mover. Defaults to 1.

        """
        _LOG.debug("Moviendo %s unidad(es) de %s a %s", cantidad, origen, destino)

        main_window = self._conn.get_main_window()
        if main_window and hasattr(main_window, "sound_manager"):
            main_window.sound_manager.play_move()

        msg = MsgMoverUnidad(origen, destino, cantidad)
        self._conn.send_data(msg.to_json())

    def atacar(
        self, origen: str, destino: str, cantidad_unidades: int | None = None
    ) -> None:
        """Envía un mensaje de ataque al servidor.

        Args:
            origen (str): País de origen del ataque
            destino (str): País de destino del ataque
            cantidad_unidades (int, optional): Cantidad de unidades con las que
                                              atacar (1-3). Si es None, se usa el
                                              máximo posible.

        """
        msg = MsgAtacar(origen, destino, cantidad_unidades)
        self._conn.send_data(msg.to_json())

    def actualizar_lista_jugadores(self, jugadores: list[dict[str, Any]]) -> None:
        """Actualiza la lista de jugadores en la interfaz de usuario.

        Args:
            jugadores (list): Lista de diccionarios con la información de los jugadores
                Cada diccionario debe tener las claves 'userid' y 'color' (con
                'r', 'g', 'b')

        """

    def finalizar_turno(self) -> None:
        """Envía un mensaje al servidor para finalizar el turno actual."""
        msg = MsgFinalizarTurno()
        self._conn.send_data(msg.to_json())

    def solicitar_tarjetas(self) -> None:
        """Solicita al servidor las tarjetas del jugador."""
        msg = MsgSolicitarTarjetas()
        self._conn.send_data(msg.to_json())

    def reclamar_tarjeta(self) -> None:
        """Reclama una tarjeta después de conquistar un país."""
        msg = MsgReclamarTarjeta()
        self._conn.send_data(msg.to_json())

    def canje_especial(self, pais: str) -> None:
        """Realiza un canje especial de país + tarjeta por 2 unidades.

        Args:
            pais (str): Nombre del país donde se agregaran las unidades

        """
        msg = MsgCanjeEspecial(pais)
        self._conn.send_data(msg.to_json())

    def canjear_misil(self, pais: str) -> None:
        """Canjea unidades por 1 misil en un país.

        Args:
            pais (str): Nombre del país donde se canjeará el misil

        """
        _LOG.debug("Canjeando misil en %s", pais)
        msg = MsgCanjearMisil(pais)
        self._conn.send_data(msg.to_json())

    def lanzar_misil(self, pais_origen: str, pais_destino: str) -> None:
        """Lanza un misil desde un país hacia otro.

        Args:
            pais_origen (str): País desde donde se lanza el misil
            pais_destino (str): País objetivo del misil

        """
        _LOG.debug("Lanzando misil desde %s hacia %s", pais_origen, pais_destino)
        msg = MsgLanzarMisil(pais_origen, pais_destino)
        self._conn.send_data(msg.to_json())
