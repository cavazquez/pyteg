"""Tests para el módulo de gestión de tareas del servidor."""

import json
import unittest

from pyteg.server.tasks import (
    ServerTaskChat,
    ServerTaskNull,
    ServerTaskSeleccionarColor,
)
from pyteg.server.tasks.manager import ServerTaskManager


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

    def test_task_seleccionar_color(self) -> None:
        """seleccionar_color debe mapear a la tarea de lobby, no a null."""
        data_json = json.loads('{"mensaje": "seleccionar_color", "color": "#00ff00"}')
        res = ServerTaskManager.msg_to_task(data_json)
        self.assertIsInstance(res, ServerTaskSeleccionarColor)
