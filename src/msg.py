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
    def __init__(self, id_user, rgb_json):
        self._tipo = "color_asignado"
        self._id_user = id_user
        self._rgb_json = rgb_json
        print(rgb_json)

    def to_json(self):
        data = {
            "mensaje": self._tipo,
            "id": self._id_user,
        }
        rgb_dict = json.loads(self._rgb_json)
        return json.dumps(data | rgb_dict)


class MsgColor(IMsg):
    def __init__(self, color):
        self._tipo = "color"
        self._color = color

    def to_json(self):
        color_json = json.loads(self._color.to_json())
        data = {
            "mensaje": self._tipo,
        }
        return json.dumps(data | color_json)


class MsgUserId(IMsg):
    def __init__(self, user_id):
        self._tipo = "user_id"
        self._user_id = user_id

    def to_json(self):
        data = {"mensaje": self._tipo, "user_id": self._user_id}
        return json.dumps(data)
