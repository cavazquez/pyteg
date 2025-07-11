from src.server_msg import (
    MsgActualizarListaJugadores,
    MsgChat,
    MsgColor,
    MsgColorAsignado,
    MsgEstado,
    MsgPais,
    MsgSosAdmin,
    MsgTiempo,
    MsgTurno,
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

    def enviar_turno(
        self,
        num_turno,
        num_ronda,
        jugador_actual_id=None,
        jugador_actual_nombre=None,
        jugador_actual_color=None,
    ):
        """Envía el número de turno y ronda actuales a los clientes.

        Args:
            num_turno (int): El número de turno actual
            num_ronda (int): El número de ronda actual
            jugador_actual_id (int, optional): ID del jugador actual
            jugador_actual_nombre (str, optional): Nombre del jugador actual
            jugador_actual_color (str, optional): Color del jugador actual
        """
        msg = MsgTurno(
            num_turno,
            num_ronda,
            jugador_actual_id,
            jugador_actual_nombre,
            jugador_actual_color,
        )
        self._send_message(msg)

    def actualizar_lista_jugadores(self, jugadores):
        """Envía la lista actualizada de jugadores al cliente.

        Args:
            jugadores (list): Lista de tuplas (userid, color) donde color es un
                diccionario con las claves 'r', 'g', 'b'
        """
        msg = MsgActualizarListaJugadores(jugadores)
        self._send_message(msg)

    def enviar_mapa(self, mapa, game):
        """Envía el estado actual del mapa al cliente.

        Args:
            mapa: Instancia del mapa del juego
            game: Instancia del juego actual
        """
        # Enviar información de cada país
        for pais in mapa.paises():
            unidades = mapa.cantidad_unidades(pais)
            userid = mapa.ocupado_por(pais).userid()
            print(f"{pais} {userid} {unidades}")
            self.enviar_pais(pais, userid, unidades)

        # Enviar unidades disponibles si el juego ha comenzado
        if game is not None and hasattr(game, "turno_actual"):
            # Buscar el turno del jugador actual
            turno_jugador = None
            for turno in game.turnos():
                if (
                    hasattr(turno, "jugador_actual")
                    and turno.jugador_actual() == self._conn
                ):
                    turno_jugador = turno
                    break

            if turno_jugador is not None:
                unidades_disponibles = {
                    "infanteria": turno_jugador.cant_unidades(),
                    "misiles": turno_jugador.cant_misiles()
                    if hasattr(turno_jugador, "cant_misiles")
                    else 0,
                }
                self.enviar_unidades_disponibles(unidades_disponibles)
