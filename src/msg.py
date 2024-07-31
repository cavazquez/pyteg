import json
from abc import ABC, abstractmethod

class IMsg(ABC):

    @abstractmethod
    def to_json(self):
        pass

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
