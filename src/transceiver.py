import json
import time


class Transceiver:
    def __init__(self, client, gui):
        self.client = client
        self.gui = gui

    def receiver(self):
        data_b = ""
        while self.gui.vivo():
            if self.client.is_connected():
                data_b = self.client.get_data()

            if data_b:
                data = data_b.decode()
                data_json = json.loads(data)
                print(data_json)

                if "chat" in data_json:
                    msg = data_json["chat"]
                    self.gui.msg_chat(msg)
                elif "mapa" in data_json:
                    self.client.update_mapa(data_json["mapa"])
                elif "jugadores" in data_json:
                    self.gui.update(data_json["jugadores"])
                else:
                    print("Comando no reconocido")

            time.sleep(1)
