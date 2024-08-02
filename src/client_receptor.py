from PySide6.QtCore import QRunnable, Slot

from src.client_tasks_manager import ClientTaskManager


class Receptor(QRunnable):

    def __init__(self, main_window, conn):
        super().__init__()
        self._main_window = main_window
        self._conn = conn

    @Slot()
    def run(self):
        print("Receptor")
        while self._main_window.vivo():
            data = self._conn.get_data()
            if data:
                print(f"data: {data}")
                task = ClientTaskManager.msg_to_task(data)
                print(f"task: {task}")
                task.run(self._main_window)
            else:
                pass
        print("Saliendo Transceiver.receiver")
