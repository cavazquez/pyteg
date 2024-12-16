from abc import ABC, abstractmethod

from src.client_msg import MsgChat, MsgEmpezar, MsgSeleccionarColor


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


class ClientNullTransmisor(IClientTransmisor):
    def __init__(self):
        pass

    def enviar_chat(self, _):
        print("No estas conectado")

    def empezar(self):
        print("No estas conectado")

    def seleccionar_color(self):
        print("No estas conectado")


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
