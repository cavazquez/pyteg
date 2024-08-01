import json
import unittest

from src.server_tasks import (
    ServerTaskChat,
    ServerTaskNull,
)
from src.server_tasks_manager import ServerTaskManager


class TestClientTaskManager(unittest.TestCase):

    def test_task_no_existe(self):
        data_json = json.loads('{"mensaje": "cualquiercosa"}')
        res = ServerTaskManager.msg_to_task(data_json)
        self.assertIsInstance(res, ServerTaskNull)

    def test_task_chat(self):
        data_json = json.loads('{"mensaje": "chat", "msg":"hola mundo!"}')
        res = ServerTaskManager.msg_to_task(data_json)
        self.assertIsInstance(res, ServerTaskChat)
