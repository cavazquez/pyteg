from src.msg import MsgChat


class ClientNullTransmisor:

    def __init__(self):
        pass


class ClientTransmisor:

    def __init__(self, conn):
        self._conn = conn

    def enviar_chat(self, msg):
        msg_chat = MsgChat(msg)
        self._conn.send_data(msg_chat.to_json())
