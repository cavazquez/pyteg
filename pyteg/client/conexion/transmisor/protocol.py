"""Interfaz abstracta del transmisor cliente -> servidor."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


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
        """Canjea unidades por 1 misil en un país.

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
