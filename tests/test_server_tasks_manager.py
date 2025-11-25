"""Tests para el módulo de gestión de tareas del servidor."""

import json
import unittest

from src.server_tasks import (
    ServerTaskChat,
    ServerTaskNull,
)
from src.server_tasks_manager import ServerTaskManager


class TestClientTaskManager(unittest.TestCase):
    """Tests para ServerTaskManager."""

    def test_task_no_existe(self) -> None:
        """Prueba cuando se solicita una tarea que no existe."""
        data_json = json.loads('{"mensaje": "cualquiercosa"}')
        res = ServerTaskManager.msg_to_task(data_json)
        self.assertIsInstance(res, ServerTaskNull)

    def test_task_chat(self) -> None:
        """Prueba crear una tarea de chat."""
        data_json = json.loads('{"mensaje": "chat", "msg":"hola mundo!"}')
        res = ServerTaskManager.msg_to_task(data_json)
        self.assertIsInstance(res, ServerTaskChat)
