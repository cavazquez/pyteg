"""Módulo para manejar la transmisión de mensajes del cliente al servidor."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from src.client_msg import (
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


class IClientTransmisor(ABC):
    """Interfaz abstracta para el transmisor de mensajes del cliente."""

    @abstractmethod
    def __init__(self) -> None:
        """Inicializa el transmisor."""

    @abstractmethod
    def enviar_chat(self, msg: str) -> None:
        """Envía un mensaje de chat al servidor.

        Args:
            msg: Mensaje de chat a enviar.

        """

    @abstractmethod
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

    @abstractmethod
    def seleccionar_color(self, color: Any) -> None:
        """Selecciona un color para el jugador.

        Args:
            color: Color a seleccionar.

        """

    @abstractmethod
    def empezar_partida(self) -> None:
        """Inicia la partida."""

    @abstractmethod
    def set_username(self, username: str) -> None:
        """Establece el nombre de usuario.

        Args:
            username: Nombre de usuario a establecer.

        """

    @abstractmethod
    def agregar_unidad(self, pais: str, tipo_unidad: str, cantidad: int = 1) -> None:
        """Envía un mensaje al servidor para agregar unidades en un país específico.

        Args:
            pais (str): Nombre del país donde se agregará la unidad
            tipo_unidad (str): Tipo de unidad a agregar (ej: 'infanteria', 'misil')
            cantidad (int, optional): Cantidad de unidades a agregar. Defaults to 1.

        """

    @abstractmethod
    def mover_unidad(self, origen: str, destino: str, cantidad: int = 1) -> None:
        """Envía un mensaje al servidor para mover unidades entre países.

        Args:
            origen (str): Nombre del país de origen
            destino (str): Nombre del país de destino
            cantidad (int, optional): Cantidad de unidades a mover. Defaults to 1.

        """

    @abstractmethod
    def atacar(
        self, origen: str, destino: str, cantidad_unidades: int | None = None
    ) -> None:
        """Envía un mensaje al servidor para atacar de un país a otro.

        Args:
            origen (str): Nombre del país atacante
            destino (str): Nombre del país defensor
            cantidad_unidades (int, optional): Cantidad de unidades con las que
                                              atacar (1-3). Si es None, se usa el
                                              máximo posible.

        """

    @abstractmethod
    def actualizar_lista_jugadores(self, jugadores: list[dict[str, Any]]) -> None:
        """Actualiza la lista de jugadores en la interfaz de usuario.

        Args:
            jugadores (list): Lista de diccionarios con la información de los jugadores
                Cada diccionario debe tener las claves 'userid' y 'color' (con
                'r', 'g', 'b')

        """

    @abstractmethod
    def finalizar_turno(self) -> None:
        """Envía un mensaje al servidor para finalizar el turno actual."""

    @abstractmethod
    def solicitar_tarjetas(self) -> None:
        """Solicita al servidor las tarjetas del jugador."""

    @abstractmethod
    def reclamar_tarjeta(self) -> None:
        """Reclama una tarjeta después de conquistar un país."""

    @abstractmethod
    def canje_especial(self, pais: str) -> None:
        """Realiza un canje especial de país + tarjeta por 2 unidades.

        Args:
            pais (str): Nombre del país donde se agregaran las unidades

        """

    @abstractmethod
    def canjear_misil(self, pais: str) -> None:
        """Canjea 6 unidades por 1 misil en un país.

        Args:
            pais (str): Nombre del país donde se canjeará el misil

        """

    @abstractmethod
    def lanzar_misil(self, pais_origen: str, pais_destino: str) -> None:
        """Lanza un misil desde un país hacia otro.

        Args:
            pais_origen (str): País desde donde se lanza el misil
            pais_destino (str): País objetivo del misil

        """


class ClientNullTransmisor(IClientTransmisor):
    """Transmisor nulo que no envía mensajes (para cuando no hay conexión)."""

    def __init__(self) -> None:
        """Inicializa el transmisor nulo."""

    def enviar_chat(self, _: str) -> None:
        """Envía un mensaje de chat (no-op cuando no hay conexión).

        Args:
            _: Mensaje de chat (ignorado).

        """
        print("No estas conectado")

    def empezar(
        self,
        segundos: int | None = None,
        paises_para_victoria: int | None = None,
        *,
        objetivos_secretos: bool = False,
        misiles_habilitados: bool = False,
    ) -> None:
        """No-op para el transmisor nulo."""

    def seleccionar_color(self, _color: Any) -> None:
        """Selecciona un color (no-op cuando no hay conexión).

        Args:
            _color: Color a seleccionar (ignorado).

        """
        print("No estas conectado")

    def empezar_partida(self) -> None:
        """Inicia la partida (no-op cuando no hay conexión)."""
        print("No estas conectado")

    def set_username(self, _: str) -> None:
        """Establece el nombre de usuario (no-op cuando no hay conexión).

        Args:
            _: Nombre de usuario (ignorado).

        """
        print("No estas conectado")

    def agregar_unidad(self, _pais: str, _tipo_unidad: str, _cantidad: int = 1) -> None:
        """Agrega una unidad (no-op cuando no hay conexión).

        Args:
            _pais: País donde agregar (ignorado).
            _tipo_unidad: Tipo de unidad (ignorado).
            _cantidad: Cantidad de unidades (ignorado).

        """
        print("No estas conectado")

    def mover_unidad(self, _origen: str, _destino: str, _cantidad: int = 1) -> None:
        """Mueve unidades (no-op cuando no hay conexión).

        Args:
            _origen: País de origen (ignorado).
            _destino: País de destino (ignorado).
            _cantidad: Cantidad de unidades (ignorado).

        """
        print("No puedes mover unidades. No estas conectado.")

    def atacar(self, _: str, __: str, cantidad_unidades: int | None = None) -> None:  # noqa: ARG002
        """Ataca (no-op cuando no hay conexión).

        Args:
            _: País de origen (ignorado).
            __: País de destino (ignorado).
            cantidad_unidades: Cantidad de unidades (ignorado).

        """
        print("No puedes atacar. No estas conectado.")

    def actualizar_lista_jugadores(self, _: list[dict[str, Any]]) -> None:
        """Actualiza la lista de jugadores (no-op cuando no hay conexión).

        Args:
            _: Lista de jugadores (ignorado).

        """

    def finalizar_turno(self) -> None:
        """Finaliza el turno (no-op cuando no hay conexión)."""
        print("No puedes finalizar el turno. No estás conectado.")

    def solicitar_tarjetas(self) -> None:
        """Solicita tarjetas (no-op cuando no hay conexión)."""
        print("No puedes ver tarjetas. No estás conectado.")

    def reclamar_tarjeta(self) -> None:
        """Reclama una tarjeta (no-op cuando no hay conexión)."""
        print("No puedes reclamar tarjetas. No estás conectado.")

    def canje_especial(self, pais: str) -> None:
        """Realiza un canje especial cuando no está conectado."""
        _ = pais  # Evitar warning de argumento no usado
        print("No puedes realizar canje especial. No estás conectado.")

    def canjear_misil(self, pais: str) -> None:
        """Canjea un misil cuando no está conectado."""
        _ = pais  # Evitar warning de argumento no usado
        print("No puedes canjear misiles. No estás conectado.")

    def lanzar_misil(self, pais_origen: str, pais_destino: str) -> None:
        """Lanza un misil cuando no está conectado."""
        _, _ = pais_origen, pais_destino  # Evitar warning de argumentos no usados
        print("No puedes lanzar misiles. No estás conectado.")


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
        print("Transmisor empezar()")
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
        print("Selecciono color")
        msg = MsgSeleccionarColor(color)
        self._conn.send_data(msg.to_json())

    def empezar_partida(self) -> None:
        """Inicia la partida."""
        print("empezar_partida")
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
        print(f"Agregando {cantidad} unidad(es) de tipo {tipo_unidad} en {pais}")
        msg = MsgAgregarUnidad(pais, tipo_unidad, cantidad)
        self._conn.send_data(msg.to_json())

    def mover_unidad(self, origen: str, destino: str, cantidad: int = 1) -> None:
        """Envía un mensaje al servidor para mover unidades entre países.

        Args:
            origen (str): Nombre del país de origen
            destino (str): Nombre del país de destino
            cantidad (int, optional): Cantidad de unidades a mover. Defaults to 1.

        """
        print(f"Moviendo {cantidad} unidad(es) de {origen} a {destino}")

        # Reproducir sonido de movimiento
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
        # Este método no necesita hacer nada aquí, ya que el cliente
        # procesará el mensaje a través de la cola de tareas

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
        """Canjea 6 unidades por 1 misil en un país.

        Args:
            pais (str): Nombre del país donde se canjeará el misil

        """
        print(f"Canjeando misil en {pais}")
        msg = MsgCanjearMisil(pais)
        self._conn.send_data(msg.to_json())

    def lanzar_misil(self, pais_origen: str, pais_destino: str) -> None:
        """Lanza un misil desde un país hacia otro.

        Args:
            pais_origen (str): País desde donde se lanza el misil
            pais_destino (str): País objetivo del misil

        """
        print(f"Lanzando misil desde {pais_origen} hacia {pais_destino}")
        msg = MsgLanzarMisil(pais_origen, pais_destino)
        self._conn.send_data(msg.to_json())
