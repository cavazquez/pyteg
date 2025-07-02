from abc import ABC, abstractmethod

from src.client_msg import (
    MsgAgregarUnidad,
    MsgChat,
    MsgEmpezar,
    MsgEmpezarPartida,
    MsgMoverUnidad,
    MsgSeleccionarColor,
    MsgSetUsername,
)


class IClientTransmisor(ABC):
    @abstractmethod
    def __init__(self):
        pass

    @abstractmethod
    def enviar_chat(self, msg):
        pass

    @abstractmethod
    def empezar(self):
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
    def actualizar_lista_jugadores(self, jugadores):
        """
        Actualiza la lista de jugadores en la interfaz de usuario.

        Args:
            jugadores (list): Lista de diccionarios con la información de los jugadores
                Cada diccionario debe tener las claves 'userid' y 'color' (con
                'r', 'g', 'b')
        """


class ClientNullTransmisor(IClientTransmisor):
    def __init__(self):
        pass

    def enviar_chat(self, _):
        print("No estas conectado")

    def empezar(self):
        print("No estas conectado")

    def seleccionar_color(self):
        print("No estas conectado")

    def empezar_partida(self):
        print("No estas conectado")

    def set_username(self, _):
        print("No estas conectado")

    def agregar_unidad(self, _):
        print("No estas conectado")

    def mover_unidad(self, _):
        print("No puedes mover unidades. No estas conectado.")

    def actualizar_lista_jugadores(self, _):
        pass


class ClientTransmisor(IClientTransmisor):
    def __init__(self, conn):
        self._conn = conn

    def enviar_chat(self, msg):
        msg = MsgChat(msg)
        self._conn.send_data(msg.to_json())

    def empezar(self):
        print("Transmisor empezar()")
        msg = MsgEmpezar()
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
