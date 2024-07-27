import json
import time

from PySide6.QtCore import QRunnable, Slot


class Receptor(QRunnable):

    def __init__(self, client, gui, conn):
        super().__init__()
        self._client = client
        self._gui = gui
        self._conn = conn

    @Slot()
    def run(self):
        data_b = ""
        print("Receptor")
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
                else:
                    print("Comando no reconocido")

            time.sleep(1)
            print("self.gui.vivo(): ", self._gui.vivo())
        print("Saliendo Transceiver.receiver")
