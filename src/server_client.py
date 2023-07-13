import socket
import json


class ConnectionServer:
    def __init__(self, connection, addr):
        self._conn = connection
        self._addr = addr

    def receiver(self):
        data_r = self._conn.recv(1024).decode()
        return data_r

    def send(self, data):
        self._conn.sendall(data.encode())

    def close(self):
        self._conn.shutdown(socket.SHUT_RDWR)
        self._conn.close()


class Client:
    def __init__(self, user_id, conn, server):
        self._user_id = user_id
        self._username = None
        self._conn = conn
        self._server = server

    def send(self, data):
        self._conn.send(data)

    def receiver(self):
        return self._conn.receiver()

    def close(self):
        self._conn.close()

    def username(self):
        return self._username

    def run(self, game):
        vivo = True

        while vivo:
            data = self.receiver()

            if not data:
                vivo = False
                continue

            data_json_r = json.loads(data)
            self.ejecutar_mensaje(data_json_r, game, self)


    def ejecutar_mensaje(self, data, game):

        if "username" in data['mensaje']:
            username = data["nombre"]
            game.agregar_jugador(self._user_id, username)
            if not self._username:
                self._username = username 

        if "chat" in data:
            print("Enviando mensaje de chat")
            msg = self.mensaje_chat(data['chat'])
            data_json_s = json.dumps({"chat": msg})
            self._server.send_all(data_json_s, ignore_conn=self._conn)

        if "agregar_una_unidad" in data:
            print("Añadiendo una unidad")
            game.agregar_una_unidad(
                self._user_id, data["agregar_una_unidad"]
            )

        if "mapa" in data['mensaje']:
            game.ver_mapa()

        if "start" in data:
            game.start(self._server)

        if "atacar" in data:
            atacante, defensor = data["atacar"].split()
            game.atacar(atacante, defensor)

        if "reagrupar" in data:
            desde, hacia, cantidad = data["reagrupar"].split()
            game.reagrupar(desde, hacia, int(cantidad))

        if "finalizar_turno" in data:
            game.ronda().finalizar_turno()

    def mensaje_chat(self, data):
        return f'{self.username()}: {data}'
