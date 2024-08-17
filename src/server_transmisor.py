from src.msg import (
    MsgChat,
    MsgColor,
    MsgColorAsignado,
    MsgEsperarJugadores,
    MsgSosAdmin,
)


class ServerTransmisor:

    def __init__(self, conn):
        self._conn = conn

    def enviar_chat(self, msg):
        msg_chat = MsgChat(msg)
        self._conn.send(msg_chat.to_json())

    def sos_admin(self):
        msg_admin = MsgSosAdmin()
        self._conn.send(msg_admin.to_json())

    def esperar_jugadores(self):
        msg_esperar_jugadores = MsgEsperarJugadores()
        self._conn.send(msg_esperar_jugadores.to_json())

    def color_asignado(self, id_user, color):
        msg_color_asignado = MsgColorAsignado(id_user, color.to_json())
        self._conn.send(msg_color_asignado.to_json())

    def enviar_colores(self, colores):
        for color in colores:
            msg_color = MsgColor(color)
            self._conn.send(msg_color.to_json())
