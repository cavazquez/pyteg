import json
import socket


class ConnectionServer:
    def __init__(self, connection, addr):
        self._conn = connection
        self._addr = addr

    def receiver(self):
        return self._conn.recv(1024).decode()

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
        self._tarjetas = []

    def send(self, data):
        self._conn.send(data)

    def receiver(self):
        return self._conn.receiver()

    def close(self):
        self._conn.close()

    def tarjetas(self):
        return self._tarjetas

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
            self.ejecutar_mensaje(data_json_r, game)

    def ejecutar_mensaje(self, data, game):
        mensaje = data["mensaje"]

        if "username" in mensaje:
            username = data["nombre"]
            game.agregar_jugador(self._user_id, username)
            if not self._username:
                self._username = username
            return

        if "chat" in mensaje:
            print("Enviando mensaje de chat")
            msg = self.mensaje_chat(data["chat"])
            data_json_s = json.dumps({"chat": msg})
            self._server.send_all(data_json_s, ignore_conn=self._conn)
            return

        if "agregar_una_unidad" in mensaje:
            print("Añadiendo una unidad")
            game.agregar_una_unidad(self._user_id, data["agregar_una_unidad"])
            return

        if "mapa" in mensaje:
            game.ver_mapa()
            return

        if "start" in mensaje:
            game.start()
            return

        if "atacar" in mensaje:
            atacante, defensor = data["atacar"].split()
            game.atacar(atacante, defensor)
            return

        if "reagrupar" in mensaje:
            desde, hacia, cantidad = data["reagrupar"].split()
            game.reagrupar(desde, hacia, int(cantidad))
            return

        if "obtener_tarjeta" in mensaje:
            self._tarjetas.append(game.dame_una_tarjeta())
            return

        if "finalizar_turno" in mensaje:
            game.ronda().finalizar_turno()
            return

        raise Exception("Mensaje no valido")

    def mensaje_chat(self, data):
        return f"{self.username()}: {data}"
