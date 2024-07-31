from abc import ABC, abstractmethod

class IClientTask(ABC):

    @abstractmethod
    def run(self, main_window):
        pass

    @abstractmethod
    def asd(self, main_window):
        pass

class ClientTaskChat(IClientTask):

    def __init__(self, msg):
        self._msg = msg

    def run(self, main_window):
        main_window.chat.append(self._msg)


class ClientTask:

    @staticmethod
    def msg_to_task(data):
        if data["mensaje"] == "chat":
            msg = data["msg"]
            return ClientTaskChat(msg)

        return None
