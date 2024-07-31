from PySide6.QtCore import QRunnable, Slot

from src.client_tasks import ClientTask


class Receptor(QRunnable):

    def __init__(self, client, main_window, conn):
        super().__init__()
        self._client = client
        self._main_window = main_window
        self._conn = conn

    @Slot()
    def run(self):
        print("Receptor")
        while self._main_window.vivo():
            data = self._conn.get_data()
            if data:
                print(f"data: {data}")
                task = ClientTask.msg_to_task(data)
                task.run(self._main_window)
            else:
                pass
        print("Saliendo Transceiver.receiver")
