from src.server_msg import (
    MsgChat,
    MsgColor,
    MsgColorAsignado,
    MsgEsperarJugadores,
    MsgSosAdmin,
    MsgUserId,
    MsgUsername,
)


class ServerTransmisor:
    def __init__(self, conn):
        self._conn = conn

    def enviar_chat(self, msg):
        msg = MsgChat(msg)
        self._conn.send(msg.to_json())

    def sos_admin(self):
        msg = MsgSosAdmin()
        self._conn.send(msg.to_json())

    def esperar_jugadores(self):
        msg = MsgEsperarJugadores()
        self._conn.send(msg.to_json())

    def color_asignado(self, id_user, color):
        msg = MsgColorAsignado(id_user, color.to_json())
        self._conn.send(msg.to_json())

    def enviar_id(self, user_id):
        msg = MsgUserId(user_id)
        self._conn.send(msg.to_json())

    def enviar_username(self, username):
        msg = MsgUsername(username)
        self._conn.send(msg.to_json())

    def enviar_colores(self, colores):
        for color in colores:
            msg = MsgColor(color)
            self._conn.send(msg.to_json())
