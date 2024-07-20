import json
import time

from PySide6.QtCore import QRunnable, Slot


class Transceiver(QRunnable):

    def __init__(self, client, gui, conn):
        super().__init__()
        self._client = client
        self._gui = gui
        self._conn = conn

    @Slot()
    def run(self):
        data_b = ""
        print("receiver")
        while self._gui.vivo():
            if self._conn.is_connected():
                print("Obteniendo datos")
                data_b = self._conn.get_data()

            print(data_b)

            if data_b:
                data = data_b.decode()
                data_json = json.loads(data)
                print(data_json)

                if "chat" in data_json:
                    msg = data_json["chat"]
                    self._gui.msg_chat(msg)
                elif "mapa" in data_json:
                    self._client.update_mapa(data_json["mapa"])
                elif "jugadores" in data_json:
                    self._gui.update(data_json["jugadores"])
                elif "username" in data_json:
                    self._client.set_username(data_json["username"])
                elif "unidades" in data_json:
                    pais = data_json["pais"]
                    cant = data_json["unidades"]
                    self._gui.update_unidades(pais, cant)
                else:
                    print("Comando no reconocido")

            time.sleep(1)
            print("self.gui.vivo(): ", self._gui.vivo())
        print("Saliendo Transceiver.receiver")
