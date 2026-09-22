"""Tests de ServerTransmisor y ServerMessageBroadcaster."""

from __future__ import annotations

import json
import unittest
from typing import Any, cast
from unittest.mock import MagicMock, patch

from pyteg.event_types import EVENT_CHAT, EVENT_ESTADO_CAMBIADO
from pyteg.message_bus import EventHandler, MessageBus, reset_message_bus
from pyteg.server.conexion.broadcaster import ServerMessageBroadcaster
from pyteg.server.conexion.transmisor import ServerTransmisor


class _RecordingConn:
    """Conexión mínima que guarda lo enviado por send."""

    def __init__(self) -> None:
        """Inicializa buffers vacíos."""
        self.sent: list[bytes] = []

    def send(self, data: bytes | str) -> None:
        """Registra payload como bytes."""
        if isinstance(data, str):
            self.sent.append(data.encode("utf-8"))
        else:
            self.sent.append(data)


class TestServerTransmisor(unittest.TestCase):
    """Envío de mensajes al cliente."""

    def test_enviar_chat_codifica_json(self) -> None:
        """enviar_chat serializa MsgChat y llama a send."""
        conn = _RecordingConn()
        tr = ServerTransmisor(conn)
        tr.enviar_chat("hola")
        self.assertEqual(len(conn.sent), 1)
        payload = json.loads(conn.sent[0].decode("utf-8"))
        self.assertEqual(payload.get("mensaje"), "chat")
        self.assertEqual(payload.get("msg"), "hola")

    def test_enviar_error_chat_tipo_error(self) -> None:
        """enviar_error_chat usa msg_type error."""
        conn = _RecordingConn()
        tr = ServerTransmisor(conn)
        tr.enviar_error_chat("oops")
        payload = json.loads(conn.sent[0].decode("utf-8"))
        self.assertEqual(payload.get("msg_type"), "error")

    def test_enviar_userid(self) -> None:
        """enviar_userid incluye userid en JSON."""
        conn = _RecordingConn()
        tr = ServerTransmisor(conn)
        tr.enviar_userid(42)
        payload = json.loads(conn.sent[0].decode("utf-8"))
        self.assertEqual(payload.get("user_id"), 42)

    def test_enviar_mapa_solo_difunde_paises_modificados(self) -> None:
        """Una transición de una frontera no repite todo el tablero."""
        conn = _RecordingConn()
        tr = ServerTransmisor(conn)
        mapa = MagicMock()
        mapa.paises.return_value = ["Argentina", "Brasil"]
        owners = {"Argentina": 1, "Brasil": 2}
        units = {"Argentina": 3, "Brasil": 4}
        mapa.ocupado_por.side_effect = owners.__getitem__
        mapa.cantidad_unidades.side_effect = units.__getitem__

        tr.enviar_mapa(mapa, None)
        self.assertEqual(len(conn.sent), 2)

        tr.enviar_mapa(mapa, None)
        self.assertEqual(len(conn.sent), 2)

        units["Argentina"] = 5
        tr.enviar_mapa(mapa, None)
        self.assertEqual(len(conn.sent), 3)
        payload = json.loads(conn.sent[-1].decode("utf-8"))
        self.assertEqual(payload["pais"], "Argentina")
        self.assertEqual(payload["unidades"], 5)

    def test_snapshot_actualiza_cache_del_mapa(self) -> None:
        """Una resincronización no fuerza un mapa completo posterior."""
        conn = _RecordingConn()
        tr = ServerTransmisor(conn)
        snapshot = {
            "revision": 1,
            "countries": {
                "Argentina": {"userid": 1, "unidades": 3, "misiles": 0},
            },
        }
        tr.enviar_snapshot(snapshot)

        mapa = MagicMock()
        mapa.paises.return_value = ["Argentina"]
        mapa.ocupado_por.return_value = 1
        mapa.cantidad_unidades.return_value = 3
        tr.enviar_mapa(mapa, None)

        self.assertEqual(len(conn.sent), 1)


class TestServerMessageBroadcaster(unittest.TestCase):
    """Broadcast a clientes y eventos en MessageBus."""

    def setUp(self) -> None:
        """Resetea el singleton del MessageBus."""
        reset_message_bus()

    def tearDown(self) -> None:
        """Limpia el singleton del MessageBus."""
        reset_message_bus()

    def test_enviar_estado_llama_transmisor_y_publica(self) -> None:
        """Cada cliente recibe estado y se publica EVENT_ESTADO_CAMBIADO."""
        bus = MessageBus()
        captured: list[dict[str, Any]] = []

        def on_estado(data: dict[str, Any]) -> None:
            captured.append(dict(data))

        bus.subscribe(EVENT_ESTADO_CAMBIADO, cast("EventHandler", on_estado))
        c1 = MagicMock()
        c2 = MagicMock()
        br = ServerMessageBroadcaster(lambda: [c1, c2])
        with patch(
            "pyteg.server.conexion.broadcaster.get_message_bus", return_value=bus
        ):
            br.enviar_estado("jugando")
        c1.transmisor.enviar_estado.assert_called_once_with("jugando")
        c2.transmisor.enviar_estado.assert_called_once_with("jugando")
        self.assertEqual(captured, [{"estado": "jugando"}])

    def test_enviar_chat_publica_evento(self) -> None:
        """Broadcast de chat dispara EVENT_CHAT."""
        bus = MessageBus()
        msgs: list[dict[str, Any]] = []

        def on_chat(data: dict[str, Any]) -> None:
            msgs.append(dict(data))

        bus.subscribe(EVENT_CHAT, cast("EventHandler", on_chat))
        client = MagicMock()
        br = ServerMessageBroadcaster(lambda: [client])
        with patch(
            "pyteg.server.conexion.broadcaster.get_message_bus", return_value=bus
        ):
            br.enviar_chat("ana", "hola")
        client.transmisor.enviar_chat.assert_called_once()
        self.assertEqual(msgs, [{"username": "ana", "message": "hola"}])

    def test_enviar_sistema_llega_a_todos_los_clientes(self) -> None:
        """Un aviso de sistema se difunde con el tipo de mensaje correcto."""
        bus = MessageBus()
        msgs: list[dict[str, Any]] = []

        def on_chat(data: dict[str, Any]) -> None:
            msgs.append(dict(data))

        bus.subscribe(EVENT_CHAT, cast("EventHandler", on_chat))
        c1 = MagicMock()
        c2 = MagicMock()
        br = ServerMessageBroadcaster(lambda: [c1, c2])
        with patch(
            "pyteg.server.conexion.broadcaster.get_message_bus", return_value=bus
        ):
            br.enviar_sistema("Jugador 2 fue eliminado de la partida.")

        c1.transmisor.enviar_sistema.assert_called_once_with(
            "Jugador 2 fue eliminado de la partida."
        )
        c2.transmisor.enviar_sistema.assert_called_once_with(
            "Jugador 2 fue eliminado de la partida."
        )
        self.assertEqual(
            msgs,
            [
                {
                    "username": "Sistema",
                    "message": "Jugador 2 fue eliminado de la partida.",
                }
            ],
        )

    def test_get_clients_no_lista_devuelve_vacio(self) -> None:
        """_dame_clientes tolera retorno no-lista."""
        br = ServerMessageBroadcaster(lambda: None)
        with patch(
            "pyteg.server.conexion.broadcaster.get_message_bus",
            return_value=MessageBus(),
        ):
            br.enviar_estado("x")  # no debe lanzar
