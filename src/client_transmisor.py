from abc import ABC, abstractmethod

from src.msg import MsgChat


class IClientTransmisor(ABC):

    @abstractmethod
    def __init__(self):
        pass

    @abstractmethod
    def enviar_chat(self, msg):
        pass


class ClientNullTransmisor(IClientTransmisor):

    def __init__(self):
        pass

    def enviar_chat(self, _):
        print("No estas conectado")


class ClientTransmisor(IClientTransmisor):

    def __init__(self, conn):
        self._conn = conn

    def enviar_chat(self, msg):
        msg_chat = MsgChat(msg)
        self._conn.send_data(msg_chat.to_json())
