import json

from src.server_tasks import ServerTask
from src.server_transmisor import ServerTransmisor


class Client:
    def __init__(self, user_id, conn, server, username):
        self._user_id = user_id
        self._username = username
        self._conn = conn
        self._server = server
        self._tarjetas = []
        self._transmisor = ServerTransmisor(self._conn)

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
        task = ServerTask.msg_to_task(data)
        task.run(self)
        mensaje = data["mensaje"]
        print(mensaje)

        if mensaje == "username":
            username = data["nombre"]
            game.agregar_jugador(self._user_id, username)
            if not self._username:
                self._username = username
            return

        if mensaje == "obtener_username":
            data_json_s = json.dumps({"username": self._username})
            self._server.send(self._conn, data_json_s)
            return

        # if mensaje == "chat":
        #    print(f"Chat user_id: {self._user_id}")
        #    msg = self.mensaje_chat(data["chat"])
        #    data_json_s = json.dumps({"chat": msg})
        #    self._server.send_all(data_json_s)
        #    return

        if mensaje == "agregar":
            pais = data["pais"]
            cant = int(data["unidades"])
            print("cant", cant)
            print(f"Añadiendo una unidad a pais {pais}")
            for _i in range(cant):
                print(f"Añadiendo una unidad a pais {pais}")
                mapa = game.mapa()
                mapa.agregar_una_unidad(pais)
            data_json_s = json.dumps(
                {
                    "mensaje": "unidades",
                    "pais": pais,
                    "unidades": game.mapa().cantidad_unidades(pais),
                },
            )
            self._server.send(self._conn, data_json_s)
            return

        if mensaje == "mapa":
            game.ver_mapa()
            return

        if mensaje == "start":
            game.start()
            return

        if mensaje == "atacar":
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

        if "cerrar" in mensaje:
            print(f"Cerrando  user_id: {self._user_id}")
            self._server.quitarme(self._user_id)
            return

        # raise MensajeNoValidoError

    def mensaje_chat(self, data):
        return f"{self.username()}: {data}"
