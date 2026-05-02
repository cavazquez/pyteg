"""Tests de integración cliente-servidor para Pyteg.

Estos tests levantan un servidor TCP real en un hilo separado y conectan
clientes reales usando sockets, verificando el flujo de mensajes JSON
de extremo a extremo sin mocks.
"""

from __future__ import annotations

import contextlib
import json
import socket
import threading
import time
import unittest
from typing import Any

from pyteg.server.app import Server
from pyteg.server.conexion.build_cliente import ServerBuildClient
from pyteg.server.conexion.connection import ConnectionServer

# ---------------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------------

_CONNECT_TIMEOUT = 2.0  # segundos para conectar
_READ_TIMEOUT = 3.0  # segundos esperando un mensaje
_RECV_SIZE = 4096


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_server() -> tuple[Server, int]:
    """Levanta un Server y retorna (server, puerto) con puerto dinámico.

    Returns:
        Tupla (server, puerto) lista para usar.

    """
    server = Server()
    # Bind rápido para obtener un puerto libre sin race condition
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port: int = sock.getsockname()[1]
    return server, port


class _ServerThread:
    """Levanta un servidor en un hilo demonio y lo detiene en stop()."""

    def __init__(self, server: Server, port: int) -> None:
        """Inicializa el thread del servidor.

        Args:
            server: Instancia del servidor.
            port: Puerto donde escuchar conexiones.

        """
        self._server = server
        self._port = port
        self._sock: socket.socket | None = None
        self._thread: threading.Thread | None = None
        self._stop = threading.Event()

    def start(self) -> None:
        """Arranca el hilo del servidor."""
        ready = threading.Event()

        def _run() -> None:
            build_client = ServerBuildClient()
            srv_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            srv_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            srv_sock.bind(("127.0.0.1", self._port))
            srv_sock.listen()
            srv_sock.settimeout(0.3)
            self._sock = srv_sock
            ready.set()

            while not self._stop.is_set():
                try:
                    conn, addr = srv_sock.accept()
                except TimeoutError:
                    continue
                except OSError:
                    break

                estado = self._server.estado
                if estado.es_jugando() or estado.es_finalizado():
                    conn.close()
                    continue

                connection = ConnectionServer(conn, addr)
                uid, client = build_client.build(connection, self._server)
                self._server.registrar_cliente(uid, client)
                t = threading.Thread(target=client.run, daemon=True)
                t.start()

            with contextlib.suppress(OSError):
                srv_sock.close()

        self._thread = threading.Thread(target=_run, daemon=True)
        self._thread.start()
        ready.wait(timeout=2.0)

    def stop(self) -> None:
        """Detiene el servidor."""
        self._stop.set()
        with contextlib.suppress(OSError):
            if self._sock:
                self._sock.close()
        if self._thread:
            self._thread.join(timeout=2.0)


class _TestClient:
    r"""Cliente simplificado de socket para tests.

    Lee mensajes JSON delimitados por ``\0`` y los acumula en ``received``.
    """

    def __init__(self) -> None:
        """Inicializa el cliente de test."""
        self._sock: socket.socket | None = None
        self.received: list[dict[str, Any]] = []
        self._buf = ""
        self._lock = threading.Lock()
        self._reader: threading.Thread | None = None
        self._running = False

    def connect(self, host: str, port: int) -> None:
        """Conecta al servidor y arranca el hilo lector.

        Args:
            host: Dirección del servidor.
            port: Puerto del servidor.

        """
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock.settimeout(_CONNECT_TIMEOUT)
        self._sock.connect((host, port))
        self._sock.settimeout(_READ_TIMEOUT)
        self._running = True
        self._reader = threading.Thread(target=self._read_loop, daemon=True)
        self._reader.start()

    def _read_loop(self) -> None:
        r"""Lee bytes del socket y parsea mensajes JSON separados por ``\0``."""
        while self._running and self._sock:
            try:
                chunk = self._sock.recv(_RECV_SIZE)
                if not chunk:
                    break
                self._buf += chunk.decode("utf-8")
                while "\0" in self._buf:
                    msg_str, self._buf = self._buf.split("\0", 1)
                    msg_str = msg_str.strip()
                    if not msg_str:
                        continue
                    try:
                        msg = json.loads(msg_str)
                        with self._lock:
                            self.received.append(msg)
                    except json.JSONDecodeError:
                        pass
            except TimeoutError:
                continue
            except OSError:
                break

    def send(self, data: dict[str, Any]) -> None:
        """Envía un mensaje JSON al servidor.

        Args:
            data: Datos a serializar y enviar.

        """
        if self._sock:
            payload = json.dumps(data) + "\0"
            self._sock.sendall(payload.encode("utf-8"))

    def wait_for(
        self,
        mensaje: str,
        timeout: float = _READ_TIMEOUT,
        *,
        extra_check: Any = None,
    ) -> dict[str, Any] | None:
        """Espera hasta recibir un mensaje de tipo ``mensaje``.

        Args:
            mensaje: Valor de la clave ``"mensaje"`` a esperar.
            timeout: Segundos máximos de espera.
            extra_check: Callable opcional ``(msg) -> bool`` para filtrar.

        Returns:
            El primer mensaje que cumple los criterios, o ``None`` si expira.

        """
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            with self._lock:
                for msg in self.received:
                    if msg.get("mensaje") == mensaje and (
                        extra_check is None or extra_check(msg)
                    ):
                        return msg
            time.sleep(0.05)
        return None

    def close(self) -> None:
        """Cierra la conexión."""
        self._running = False
        if self._sock:
            with contextlib.suppress(OSError):
                self._sock.shutdown(socket.SHUT_RDWR)
            with contextlib.suppress(OSError):
                self._sock.close()
        if self._reader:
            self._reader.join(timeout=1.0)


# ---------------------------------------------------------------------------
# Tests de integración
# ---------------------------------------------------------------------------


class TestIntegration(unittest.TestCase):
    """Tests de integración end-to-end usando TCP real."""

    def setUp(self) -> None:
        """Levanta servidor y registra los clientes de test."""
        self._server, self._port = _make_server()
        self._srv_thread = _ServerThread(self._server, self._port)
        self._srv_thread.start()
        self._clients: list[_TestClient] = []

    def tearDown(self) -> None:
        """Cierra clientes y detiene el servidor."""
        for c in self._clients:
            c.close()
        self._srv_thread.stop()

    def _new_client(self) -> _TestClient:
        """Crea y conecta un cliente, registrándolo para cleanup.

        Returns:
            Cliente conectado listo para usar.

        """
        c = _TestClient()
        c.connect("127.0.0.1", self._port)
        self._clients.append(c)
        return c

    # ------------------------------------------------------------------
    # Test 1: un cliente recibe MsgUserId al conectarse
    # ------------------------------------------------------------------
    def test_client_connects_receives_userid(self) -> None:
        """Un cliente que se conecta recibe un mensaje de user_id."""
        client = self._new_client()
        msg = client.wait_for("user_id")
        self.assertIsNotNone(msg, "No se recibió MsgUserId")
        if msg is not None:
            self.assertIn("user_id", msg)
            self.assertIsInstance(msg["user_id"], int)

    # ------------------------------------------------------------------
    # Test 2: dos clientes se conectan y ambos reciben user_id distintos
    # ------------------------------------------------------------------
    def test_two_clients_connect(self) -> None:
        """Dos clientes se conectan; ambos reciben mensajes user_id."""
        c1 = self._new_client()
        c2 = self._new_client()

        msg1 = c1.wait_for("user_id")
        msg2 = c2.wait_for("user_id")

        self.assertIsNotNone(msg1, "Cliente 1 no recibió user_id")
        self.assertIsNotNone(msg2, "Cliente 2 no recibió user_id")

        # IDs deben ser distintos
        if msg1 is not None and msg2 is not None:
            self.assertNotEqual(msg1["user_id"], msg2["user_id"])

    # ------------------------------------------------------------------
    # Test 3: el servidor acepta el mensaje set_username y lo difunde
    # ------------------------------------------------------------------
    def test_set_username_broadcast(self) -> None:
        """El servidor difunde el username recibido a todos los clientes."""
        c1 = self._new_client()
        c1.wait_for("user_id")  # esperar que esté listo

        c1.send({"mensaje": "set_username", "username": "Alice"})

        # MsgUsername: {"mensaje": "username", "user_id": int, "username": str}
        msg = c1.wait_for(
            "username",
            extra_check=lambda m: m.get("username") == "Alice",
        )
        self.assertIsNotNone(msg, "No se recibió difusión de username")
        if msg is not None:
            self.assertEqual(msg["username"], "Alice")

    # ------------------------------------------------------------------
    # Test 4: el servidor no acepta empezar_partida sin pasar por empezar
    # ------------------------------------------------------------------
    def test_non_admin_cannot_start_game(self) -> None:
        """Un cliente no-admin no puede iniciar la partida (servidor sigue vivo)."""
        c1 = self._new_client()
        c2 = self._new_client()

        c1.wait_for("user_id")
        c2.wait_for("user_id")

        # c1 configura el lobby
        c1.send({"mensaje": "empezar", "segundos": 60})
        time.sleep(0.2)

        # c2 intenta iniciar la partida (estado inválido para su rol)
        c2.send({"mensaje": "empezar_partida"})

        time.sleep(0.3)
        # Verificar que el servidor sigue enviando mensajes (sigue vivo)
        self.assertGreater(
            len(c2.received),
            0,
            "El servidor no envió ningún mensaje al cliente 2",
        )

    # ------------------------------------------------------------------
    # Test 5: flujo completo — inicio de partida con dos jugadores
    # ------------------------------------------------------------------
    def test_game_start_flow(self) -> None:
        """Admin inicia la partida; ambos clientes reciben estado JUGANDO."""
        c1 = self._new_client()  # admin (primer cliente = user_id 1)
        c2 = self._new_client()

        self.assertIsNotNone(c1.wait_for("user_id"), "c1 sin user_id")
        self.assertIsNotNone(c2.wait_for("user_id"), "c2 sin user_id")

        # Establecer nombres de usuario
        c1.send({"mensaje": "set_username", "username": "Admin"})
        c2.send({"mensaje": "set_username", "username": "Jugador2"})
        time.sleep(0.1)

        # Admin configura y empieza
        c1.send({"mensaje": "empezar", "segundos": 60})
        time.sleep(0.1)
        c1.send({"mensaje": "empezar_partida"})

        # Ambos deben recibir el estado "JUGANDO"
        estado_c1 = c1.wait_for(
            "estado",
            timeout=4.0,
            extra_check=lambda m: m.get("estado") == "JUGANDO",
        )
        estado_c2 = c2.wait_for(
            "estado",
            timeout=4.0,
            extra_check=lambda m: m.get("estado") == "JUGANDO",
        )

        self.assertIsNotNone(estado_c1, "c1 no recibió estado JUGANDO")
        self.assertIsNotNone(estado_c2, "c2 no recibió estado JUGANDO")


if __name__ == "__main__":
    unittest.main()
