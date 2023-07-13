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
    def __init__(self, user_id, conn):
        self._user_id = user_id
        self._conn = conn

    def send(self, data):
        self._conn.send(data)

    def receiver(self):
        return self._conn.receiver()

    def close(self):
        self._conn.close()

    def run(self, server, game):
        username_set = False
        username = ""
        vivo = True
        "chau"
        while vivo:
            data = self.receiver()

            if not data:
                vivo = False
                continue

            data_json_r = json.loads(data)

            if "username" in data_json_r and not username_set:
                username = data_json_r["username"]
                print("username = ", username)
                username_set = True

            if "chat" in data_json_r:
                print("Enviando mensaje de chat")
                msg = username + ": " + data_json_r["chat"]
                data_json_s = json.dumps({"chat": msg})
                server.send_all(data_json_s, ignore_conn=self._conn)

            if "agregar_una_unidad" in data_json_r:
                print("Añadiendo una unidad")
                game.agregar_una_unidad(
                    self._user_id, data_json_r["agregar_una_unidad"]
                )

            if "mapa" in data_json_r:
                game.ver_mapa()

            if "start" in data_json_r:
                game.start(server)

            if "atacar" in data_json_r:
                atacante, defensor = data_json_r["atacar"].split()
                game.atacar(atacante, defensor)

            if "reagrupar" in data_json_r:
                desde, hacia, cantidad = data_json_r["reagrupar"].split()
                game.reagrupar(desde, hacia, int(cantidad))

            if "finalizar_turno" in data_json_r:
                game.ronda().finalizar_turno()
