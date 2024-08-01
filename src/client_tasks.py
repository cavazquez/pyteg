from abc import ABC, abstractmethod


class IClientTask(ABC):

    @abstractmethod
    def run(self, main_window):
        pass


class ClientTaskChat(IClientTask):

    def __init__(self, data):
        self._msg = data.get("msg")

    def run(self, main_window):
        main_window.chat.append(self._msg)


class ClientTaskSerAdmin(IClientTask):

    def __init__(self, data):
        pass

    def run(self, main_window):
        main_window.soy_admin = True
        main_window.ventana_admin()


class ClientTaskNull(IClientTask):

    def __init__(self, data):
        pass

    def run(self, main_window):
        pass


dict_task = {
    "chat": ClientTaskChat,
    "sosadmin": ClientTaskSerAdmin,
}
