from abc import ABC, abstractmethod

from src.client_msg import (
    MsgAgregarUnidad,
    MsgAtacar,
    MsgChat,
    MsgEmpezar,
    MsgEmpezarPartida,
    MsgFinalizarTurno,
    MsgMoverUnidad,
    MsgReclamarTarjeta,
    MsgSeleccionarColor,
    MsgSetUsername,
    MsgSolicitarTarjetas,
)


class IClientTransmisor(ABC):
    @abstractmethod
    def __init__(self):
        pass

    @abstractmethod
    def enviar_chat(self, msg):
        pass

    @abstractmethod
    def empezar(self, segundos: int | None = None):
        pass

    @abstractmethod
    def seleccionar_color(self):
        pass

    @abstractmethod
    def empezar_partida(self):
        pass

    @abstractmethod
    def set_username(self, username):
        pass

    @abstractmethod
    def agregar_unidad(self, pais, tipo_unidad, cantidad=1):
        """
        Envía un mensaje al servidor para agregar unidades en un país específico.

        Args:
            pais (str): Nombre del país donde se agregará la unidad
            tipo_unidad (str): Tipo de unidad a agregar (ej: 'infanteria', 'misil')
            cantidad (int, optional): Cantidad de unidades a agregar. Defaults to 1.
        """

    @abstractmethod
    def mover_unidad(self, origen, destino, cantidad=1):
        """
        Envía un mensaje al servidor para mover unidades entre países.

        Args:
            origen (str): Nombre del país de origen
            destino (str): Nombre del país de destino
            cantidad (int, optional): Cantidad de unidades a mover. Defaults to 1.
        """

    @abstractmethod
    def atacar(self, origen, destino, cantidad_unidades=None):
        """
        Envía un mensaje al servidor para atacar de un país a otro.

        Args:
            origen (str): Nombre del país atacante
            destino (str): Nombre del país defensor
            cantidad_unidades (int, optional): Cantidad de unidades con las que
                                              atacar (1-3). Si es None, se usa el
                                              máximo posible.
        """

    @abstractmethod
    def actualizar_lista_jugadores(self, jugadores):
        """
        Actualiza la lista de jugadores en la interfaz de usuario.

        Args:
            jugadores (list): Lista de diccionarios con la información de los jugadores
                Cada diccionario debe tener las claves 'userid' y 'color' (con
                'r', 'g', 'b')
        """

    @abstractmethod
    def finalizar_turno(self):
        """
        Envía un mensaje al servidor para finalizar el turno actual.
        """

    @abstractmethod
    def solicitar_tarjetas(self):
        """
        Solicita al servidor las tarjetas del jugador.
        """

    @abstractmethod
    def reclamar_tarjeta(self):
        """
        Reclama una tarjeta después de conquistar un país.
        """


class ClientNullTransmisor(IClientTransmisor):
    def __init__(self):
        pass

    def enviar_chat(self, _):
        print("No estas conectado")

    def empezar(
        self, segundos: int | None = None, paises_para_victoria: int | None = None
    ):
        """No-op para el transmisor nulo."""

    def seleccionar_color(self):
        print("No estas conectado")

    def empezar_partida(self):
        print("No estas conectado")

    def set_username(self, _):
        print("No estas conectado")

    def agregar_unidad(self, **_kwargs):
        print("No estas conectado")

    def mover_unidad(self, **_kwargs):
        print("No puedes mover unidades. No estas conectado.")

    def atacar(self, _, __, cantidad_unidades=None):  # noqa: ARG002
        print("No puedes atacar. No estas conectado.")

    def actualizar_lista_jugadores(self, _):
        pass

    def finalizar_turno(self):
        print("No puedes finalizar el turno. No estás conectado.")

    def solicitar_tarjetas(self):
        print("No puedes ver tarjetas. No estás conectado.")

    def reclamar_tarjeta(self):
        print("No puedes reclamar tarjetas. No estás conectado.")


class ClientTransmisor(IClientTransmisor):
    def __init__(self, conn):
        self._conn = conn

    def enviar_chat(self, msg):
        msg = MsgChat(msg)
        self._conn.send_data(msg.to_json())

    def empezar(
        self, segundos: int | None = None, paises_para_victoria: int | None = None
    ):
        print("Transmisor empezar()")
        msg = MsgEmpezar(segundos, paises_para_victoria)
        self._conn.send_data(msg.to_json())

    def seleccionar_color(self, color):
        print("Selecciono color")
        msg = MsgSeleccionarColor(color)
        self._conn.send_data(msg.to_json())

    def empezar_partida(self):
        print("empezar_partida")
        msg = MsgEmpezarPartida()
        self._conn.send_data(msg.to_json())

    def set_username(self, username):
        msg = MsgSetUsername(username)
        self._conn.send_data(msg.to_json())

    def agregar_unidad(self, pais, tipo_unidad, cantidad=1):
        """
        Envía un mensaje al servidor para agregar unidades en un país específico.

        Args:
            pais (str): Nombre del país donde se agregará la unidad
            tipo_unidad (str): Tipo de unidad a agregar (ej: 'infanteria', 'misil')
            cantidad (int, optional): Cantidad de unidades a agregar. Defaults to 1.
        """
        print(f"Agregando {cantidad} unidad(es) de tipo {tipo_unidad} en {pais}")
        msg = MsgAgregarUnidad(pais, tipo_unidad, cantidad)
        self._conn.send_data(msg.to_json())

    def mover_unidad(self, origen, destino, cantidad=1):
        """
        Envía un mensaje al servidor para mover unidades entre países.

        Args:
            origen (str): Nombre del país de origen
            destino (str): Nombre del país de destino
            cantidad (int, optional): Cantidad de unidades a mover. Defaults to 1.
        """
        print(f"Moviendo {cantidad} unidad(es) de {origen} a {destino}")

        msg = MsgMoverUnidad(origen, destino, cantidad)
        self._conn.send_data(msg.to_json())

    def atacar(self, origen, destino, cantidad_unidades=None):
        """
        Envía un mensaje de ataque al servidor.

        Args:
            origen (str): País de origen del ataque
            destino (str): País de destino del ataque
            cantidad_unidades (int, optional): Cantidad de unidades con las que
                                              atacar (1-3). Si es None, se usa el
                                              máximo posible.
        """
        msg = MsgAtacar(origen, destino, cantidad_unidades)
        self._conn.send_data(msg.to_json())

    def actualizar_lista_jugadores(self, jugadores):
        """
        Actualiza la lista de jugadores en la interfaz de usuario.

        Args:
            jugadores (list): Lista de diccionarios con la información de los jugadores
                Cada diccionario debe tener las claves 'userid' y 'color' (con
                'r', 'g', 'b')
        """
        # Este método no necesita hacer nada aquí, ya que el cliente
        # procesará el mensaje a través de la cola de tareas

    def finalizar_turno(self):
        """
        Envía un mensaje al servidor para finalizar el turno actual.
        """
        msg = MsgFinalizarTurno()
        self._conn.send_data(msg.to_json())

    def solicitar_tarjetas(self):
        """
        Solicita al servidor las tarjetas del jugador.
        """
        msg = MsgSolicitarTarjetas()
        self._conn.send_data(msg.to_json())

    def reclamar_tarjeta(self):
        """
        Reclama una tarjeta después de conquistar un país.
        """
        msg = MsgReclamarTarjeta()
        self._conn.send_data(msg.to_json())
