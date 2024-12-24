import json
from abc import ABC, abstractmethod


class IMsg(ABC):
    @abstractmethod
    def to_json(self):
        pass


class MsgSeleccionarColor(IMsg):
    def __init__(self, color):
        print("MsgSeleccionarColor")
        self._tipo = "seleccionar_color"
        self._color = color

    def to_json(self):
        data = {"mensaje": self._tipo, "color": self._color.name()}
        print(f"{data=}")
        return json.dumps(data)


class MsgEmpezar(IMsg):
    def __init__(self):
        self._tipo = "empezar"

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


class MsgEmpezarPartida(IMsg):
    def __init__(self):
        self._tipo = "empezar_partida"

    def to_json(self):
        data = {
            "mensaje": self._tipo,
        }
        return json.dumps(data)
