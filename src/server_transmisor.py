from src.server_msg import (
    MsgChat,
    MsgColor,
    MsgColorAsignado,
    MsgEstado,
    MsgPais,
    MsgSosAdmin,
    MsgTiempo,
    MsgUnidadesDisponibles,
    MsgUserId,
    MsgUsername,
)


class ServerTransmisor:
    def __init__(self, conn):
        self._conn = conn

    def _send_message(self, msg):
        try:
            self._conn.send(msg.to_json())
        except Exception as e:
            print(f"Error sending message: {e}")

    def enviar_chat(self, msg):
        msg = MsgChat(msg)
        self._send_message(msg)

    def sos_admin(self):
        msg = MsgSosAdmin()
        self._send_message(msg)

    def color_asignado(self, id_user, color):
        msg = MsgColorAsignado(id_user, color.to_json())
        self._send_message(msg)

    def enviar_userid(self, user_id):
        msg = MsgUserId(user_id)
        self._send_message(msg)

    def enviar_username(self, userid, username):
        print(f"enviar_username, {userid=} , {username=}")
        msg = MsgUsername(userid, username)
        self._send_message(msg)

    def enviar_colores(self, colores):
        for color in colores:
            msg = MsgColor(color)
            self._send_message(msg)

    def enviar_estado(self, estado):
        msg = MsgEstado(estado)
        self._send_message(msg)

    def enviar_tiempo(self, userid_turno, tiempo_restante):
        msg = MsgTiempo(userid_turno, tiempo_restante)
        self._send_message(msg)

    def enviar_unidades_disponibles(self, unidades):
        """Envía la cantidad de unidades disponibles para colocar al jugador.

        Args:
            unidades (dict): Diccionario con el tipo de unidad y la cantidad disponible.
                Ejemplo: {"infanteria": 5, "artilleria": 2, "caballeria": 1}
        """
        msg = MsgUnidadesDisponibles(unidades)
        self._send_message(msg)

    def enviar_pais(self, pais, userid, unidades):
        msg = MsgPais(pais, userid, unidades)
        self._send_message(msg)
