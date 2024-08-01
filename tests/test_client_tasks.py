import json
import unittest

from src.client_tasks import (
    ClientTaskChat,
    ClientTaskNull,
    ClientTaskSerAdmin,
)
from src.client_tasks_manager import ClientTaskManager


class TestClientTaskManager(unittest.TestCase):

    def test_task_no_existe(self):
        data_json = json.loads('{"mensaje": "cualquiercosa"}')
        res = ClientTaskManager.msg_to_task(data_json)
        self.assertIsInstance(res, ClientTaskNull)

    def test_task_chat(self):
        data_json = json.loads('{"mensaje": "chat", "msg":"hola mundo!"}')
        res = ClientTaskManager.msg_to_task(data_json)
        self.assertIsInstance(res, ClientTaskChat)

    def test_task_ser_admin(self):
        data_json = json.loads('{"mensaje": "sosadmin"}')
        res = ClientTaskManager.msg_to_task(data_json)
        self.assertIsInstance(res, ClientTaskSerAdmin)
