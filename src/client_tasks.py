from abc import ABC, abstractmethod


class IClientTask(ABC):

    @abstractmethod
    def run(self, main_window):
        pass


class ClientTaskChat(IClientTask):

    def __init__(self, msg):
        self._msg = msg

    def run(self, main_window):
        main_window.chat.append(self._msg)


class ClientTaskSerAdmin(IClientTask):

    def __init__(self):
        pass

    def run(self, main_window):
        main_window.soy_admin = True
        main_window.ventana_admin()


class ClientTask:

    @staticmethod
    def msg_to_task(data):
        try:
            mensaje = data["mensaje"]
            if mensaje == "chat":
                msg = data["msg"]
                return ClientTaskChat(msg)
            if mensaje == "sosadmin":
                return ClientTaskSerAdmin()
        except KeyError as e:
            print(e)
        return None
