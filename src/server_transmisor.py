from src.msg import MsgChat


class ServerTransmisor:

    def __init__(self, conn):
        self._conn = conn

    def enviar_chat(self, msg):
        msg_chat = MsgChat(msg)
        self._conn.send(msg_chat.to_json())
