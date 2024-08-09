import json
from abc import ABC, abstractmethod


class IMsg(ABC):

    @abstractmethod
    def to_json(self):
        pass


class MsgSosAdmin(IMsg):

    def __init__(self):
        self._tipo = "sosadmin"

    def to_json(self):
        data = {"mensaje": self._tipo}
        return json.dumps(data)


class MsgChat(IMsg):

    def __init__(self, msg):
        self._tipo = "chat"
        self._msg = msg

    def to_json(self):
        data = {
            "mensaje": self._tipo,
            "msg": self._msg,
        }
        return json.dumps(data)


class MsgEmpezar(IMsg):

    def __init__(self):
        self._tipo = "empezar"

    def to_json(self):
        data = {"mensaje": self._tipo}
        return json.dumps(data)


class MsgEsperarJugadores(IMsg):

    def __init__(self):
        self._tipo = "esperar_jugadores"

    def to_json(self):
        data = {"mensaje": self._tipo}
        return json.dumps(data)


class MsgColorAsignado(IMsg):

    def __init__(self, rgb_json):
        self._tipo = "color_asignado"
        self._rgb_json = rgb_json
        print(rgb_json)

    def to_json(self):
        data = {
            "mensaje": self._tipo,
        }
        rgb_dict = json.loads(self._rgb_json)
        return json.dumps(data | rgb_dict)
