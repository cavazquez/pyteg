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

from pyteg.codecs_utils import FrameCodecError, NulDelimitedUtf8Codec
from pyteg.config import MIN_UNITS_FOR_ATTACK
from pyteg.server.app import Server
from pyteg.server.conexion.build_cliente import ServerBuildClient
from pyteg.server.conexion.connection import ConnectionServer
from pyteg.server.msg import MsgError

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
                    rejection = MsgError(
                        "game_in_progress",
                        "El juego ya está en progreso. "
                        "No se pueden conectar nuevos jugadores.",
                    ).to_json()
                    with contextlib.suppress(OSError):
                        conn.sendall(NulDelimitedUtf8Codec.encode_frame(rejection))
                    conn.close()
                    continue

                connection = ConnectionServer(conn, addr)
                uid, client = build_client.build(connection, self._server)
                if not self._server.registrar_cliente(uid, client):
                    client.transmisor.enviar_error(
                        "room_full",
                        "La sala está completa. Intenta nuevamente más tarde.",
                    )
                    client.cerrar(flush_outgoing=True)
                    continue
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
        self._server.detener()


class _TestClient:
    r"""Cliente simplificado de socket para tests.

    Lee mensajes JSON delimitados por ``\0`` y los acumula en ``received``.
    """

    def __init__(self) -> None:
        """Inicializa el cliente de test."""
        self._sock: socket.socket | None = None
        self.received: list[dict[str, Any]] = []
        self._codec = NulDelimitedUtf8Codec()
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
                for raw_message in self._codec.feed(chunk):
                    msg_str = raw_message.strip()
                    if not msg_str:
                        continue
                    try:
                        msg = json.loads(msg_str)
                        with self._lock:
                            self.received.append(msg)
                    except json.JSONDecodeError:
                        pass
            except FrameCodecError:
                break
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

    def send_bytes(self, data: bytes) -> None:
        """Envía bytes sin aplicar framing adicional.

        Args:
            data: Fragmento de una o más tramas TCP para enviar al servidor.

        """
        if self._sock:
            self._sock.sendall(data)

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

    def snapshot_received(self) -> list[dict[str, Any]]:
        """Copia thread-safe de los mensajes recibidos hasta el momento.

        Returns:
            Lista de mensajes JSON ya parseados.

        """
        with self._lock:
            return list(self.received)

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

    def _wait_for_client_count(self, expected: int, timeout: float = 3.0) -> None:
        """Espera a que el registro alcance una cantidad concreta de clientes."""
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if self._server.cant_clients() == expected:
                return
            time.sleep(0.05)
        self.fail(
            f"El servidor retuvo {self._server.cant_clients()} clientes; "
            f"se esperaban {expected}"
        )

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

    def test_lobby_disconnect_cycles_return_all_colors(self) -> None:
        """Veinte altas y bajas no agotan colores ni retienen jugadores."""
        total_colores = len(self._server.color.colores())

        for _ in range(20):
            client = self._new_client()
            self.assertIsNotNone(client.wait_for("user_id"), "Cliente sin user_id")
            client.close()
            self._wait_for_client_count(0)

        self.assertEqual(self._server.dame_clientes(), [])
        self.assertEqual(len(self._server.color.colores_disponibles()), total_colores)

    def test_ninth_lobby_client_is_rejected_without_consuming_a_color(self) -> None:
        """La conexión que excede los ocho colores recibe room_full y se cierra."""
        total_colores = len(self._server.color.colores())
        accepted = [self._new_client() for _ in range(total_colores)]
        for client in accepted:
            self.assertIsNotNone(client.wait_for("user_id"), "Cliente sin user_id")

        rejected = self._new_client()
        error = rejected.wait_for(
            "error", extra_check=lambda data: data.get("error_type") == "room_full"
        )
        self.assertIsNotNone(error, "La sala llena no informó room_full")
        self.assertEqual(self._server.cant_clients(), total_colores)
        self.assertEqual(len(self._server.color.colores_disponibles()), 0)

        accepted[0].close()
        self._wait_for_client_count(total_colores - 1)
        replacement = self._new_client()
        self.assertIsNotNone(
            replacement.wait_for("user_id"), "No se reutilizó el color liberado"
        )
        self.assertEqual(self._server.cant_clients(), total_colores)

    def test_disconnect_during_game_keeps_player_identity_and_color(self) -> None:
        """Una baja en partida conserva color, jugador y ocupación del mapa."""
        first = self._new_client()
        second = self._new_client()
        first_id, _second_id = self._start_two_player_game(first, second)
        game = self._server.game
        self.assertIsNotNone(game, "No se creó la partida")
        if game is None:
            return

        player = next(
            player for player in game.lista_jugadores() if player.userid() == first_id
        )
        color = player.color_actual()
        countries_before = [
            pais
            for pais in game.mapa().paises()
            if game.mapa().ocupado_por(pais) == first_id
        ]
        self.assertTrue(countries_before, "El jugador no recibió territorios")

        first.close()
        self._wait_for_client_count(1)

        countries_after = [
            pais
            for pais in game.mapa().paises()
            if game.mapa().ocupado_por(pais) == first_id
        ]
        self.assertIn(player, game.lista_jugadores())
        self.assertEqual(countries_after, countries_before)
        self.assertIn(color, self._server.color.colores_usados())

    def test_game_in_progress_rejection_uses_structured_error(self) -> None:
        """Una conexión tardía recibe error JSON, no texto libre del servidor."""
        first = self._new_client()
        second = self._new_client()
        self._start_two_player_game(first, second)

        rejected = self._new_client()
        error = rejected.wait_for(
            "error",
            extra_check=lambda data: data.get("error_type") == "game_in_progress",
        )

        self.assertIsNotNone(error, "No se recibió rechazo estructurado")
        self.assertEqual(self._server.cant_clients(), 2)

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

    def test_server_reassembles_fragmented_utf8_command(self) -> None:
        """Un comando partido dentro de UTF-8 no desconecta ni pierde datos."""
        client = self._new_client()
        self.assertIsNotNone(client.wait_for("user_id"), "Cliente sin user_id")
        payload = json.dumps(
            {"mensaje": "set_username", "username": "Café"}, ensure_ascii=False
        )
        frame = NulDelimitedUtf8Codec.encode_frame(payload)
        split_at = frame.index("é".encode()) + 1

        client.send_bytes(frame[:split_at])
        time.sleep(0.05)
        client.send_bytes(frame[split_at:])

        message = client.wait_for(
            "username",
            extra_check=lambda data: data.get("username") == "Café",
        )
        self.assertIsNotNone(message, "El servidor descartó el comando fragmentado")

    def test_invalid_tcp_messages_return_errors_and_connection_recovers(self) -> None:
        """JSON inválido y escalares no tumban el lector ni alteran el registro."""
        client = self._new_client()
        self.assertIsNotNone(client.wait_for("user_id"), "Cliente sin user_id")

        client.send_bytes(b'{"mensaje":\0')
        malformed_error = client.wait_for(
            "error",
            extra_check=lambda data: data.get("error_type") == "invalid_json",
        )
        self.assertIsNotNone(malformed_error, "No se informó el JSON inválido")

        client.send_bytes(b"[]\0")
        scalar_error = client.wait_for(
            "error",
            extra_check=lambda data: data.get("error_type") == "invalid_payload",
        )
        self.assertIsNotNone(scalar_error, "No se informó el payload escalar")
        self.assertEqual(self._server.cant_clients(), 1)

        client.send({"mensaje": "set_username", "username": "Recuperado"})
        recovered = client.wait_for(
            "username",
            extra_check=lambda data: data.get("username") == "Recuperado",
        )
        self.assertIsNotNone(recovered, "El lector no se recuperó tras el error")

    # ------------------------------------------------------------------
    # Test 4: sólo el administrador puede configurar o empezar la partida
    # ------------------------------------------------------------------
    def test_non_admin_cannot_configure_or_start_game(self) -> None:
        """Un no-admin no altera configuración ni estado y recibe error TCP."""
        admin = self._new_client()
        non_admin = self._new_client()

        self.assertIsNotNone(admin.wait_for("user_id"), "Admin sin user_id")
        self.assertIsNotNone(non_admin.wait_for("user_id"), "Jugador sin user_id")

        non_admin.send({
            "mensaje": "empezar",
            "segundos": 1,
            "paises_para_victoria": 2,
            "objetivos_secretos": True,
            "misiles_habilitados": True,
        })
        first_error = non_admin.wait_for(
            "error", extra_check=lambda data: data.get("error_type") == "not_admin"
        )
        self.assertIsNotNone(first_error, "No se rechazó la configuración no-admin")
        self.assertTrue(self._server.estado.es_inicial())
        self.assertIsNone(self._server.game)

        received_before_start = len(non_admin.snapshot_received())
        non_admin.send({"mensaje": "empezar_partida"})
        deadline = time.monotonic() + _READ_TIMEOUT
        second_error: dict[str, Any] | None = None
        while time.monotonic() < deadline:
            for message in non_admin.snapshot_received()[received_before_start:]:
                if (
                    message.get("mensaje") == "error"
                    and message.get("error_type") == "not_admin"
                ):
                    second_error = message
                    break
            if second_error is not None:
                break
            time.sleep(0.05)

        self.assertIsNotNone(second_error, "No se rechazó el inicio no-admin")
        self.assertTrue(self._server.estado.es_inicial())
        self.assertIsNone(self._server.game)

        admin.send({"mensaje": "empezar", "segundos": 77})
        self.assertIsNotNone(
            admin.wait_for(
                "estado",
                extra_check=lambda data: data.get("estado") == "EsperarJugadores",
            ),
            "El administrador no pudo configurar la sala",
        )
        admin.send({"mensaje": "empezar_partida"})
        self.assertIsNotNone(
            admin.wait_for(
                "estado",
                timeout=4.0,
                extra_check=lambda data: data.get("estado") == "JUGANDO",
            ),
            "El administrador no pudo iniciar la partida",
        )
        config = admin.wait_for("configuracion_partida", timeout=4.0)
        self.assertIsNotNone(config, "No se difundió la configuración de partida")
        if config is not None:
            self.assertEqual(config["segundos_por_turno"], 77)
            self.assertEqual(config["paises_para_victoria"], 0)
            self.assertFalse(config["objetivos_secretos"])
            self.assertFalse(config["misiles_habilitados"])

    # ------------------------------------------------------------------
    # Test 5: flujo completo — inicio de partida con dos jugadores
    # ------------------------------------------------------------------
    def test_game_start_flow(self) -> None:
        """Admin inicia la partida; ambos clientes reciben estado JUGANDO."""
        c1 = self._new_client()  # admin (primer cliente = user_id 1)
        c2 = self._new_client()
        self._start_two_player_game(c1, c2)

    def _start_two_player_game(
        self,
        c1: _TestClient,
        c2: _TestClient,
        *,
        segundos: int = 60,
        paises_para_victoria: int | None = None,
        objetivos_secretos: bool | None = None,
    ) -> tuple[int, int]:
        """Configura usernames y arranca partida con c1 como admin.

        Returns:
            Tupla ``(user_id_c1, user_id_c2)``.

        """
        uid1_msg = c1.wait_for("user_id")
        uid2_msg = c2.wait_for("user_id")
        self.assertIsNotNone(uid1_msg, "c1 sin user_id")
        self.assertIsNotNone(uid2_msg, "c2 sin user_id")
        if uid1_msg is None or uid2_msg is None:
            self.fail("Faltan mensajes user_id")
        uid1 = int(uid1_msg["user_id"])
        uid2 = int(uid2_msg["user_id"])

        c1.send({"mensaje": "set_username", "username": "Admin"})
        c2.send({"mensaje": "set_username", "username": "Jugador2"})
        time.sleep(0.1)

        empezar: dict[str, Any] = {"mensaje": "empezar", "segundos": segundos}
        if paises_para_victoria is not None:
            empezar["paises_para_victoria"] = paises_para_victoria
        if objetivos_secretos is not None:
            empezar["objetivos_secretos"] = objetivos_secretos
        c1.send(empezar)
        time.sleep(0.1)
        c1.send({"mensaje": "empezar_partida"})

        self.assertIsNotNone(
            c1.wait_for(
                "estado",
                timeout=4.0,
                extra_check=lambda m: m.get("estado") == "JUGANDO",
            ),
            "c1 no recibió estado JUGANDO",
        )
        self.assertIsNotNone(
            c2.wait_for(
                "estado",
                timeout=4.0,
                extra_check=lambda m: m.get("estado") == "JUGANDO",
            ),
            "c2 no recibió estado JUGANDO",
        )
        return uid1, uid2

    def _latest_turno(self, *clients: _TestClient) -> dict[str, Any] | None:
        """Devuelve el mensaje ``turno`` más reciente recibido por algún cliente.

        Returns:
            Último mensaje ``turno`` visto, o ``None`` si aún no llegó ninguno.

        """
        latest: dict[str, Any] | None = None
        for client in clients:
            for msg in client.snapshot_received():
                if msg.get("mensaje") == "turno":
                    latest = msg
        return latest

    def _wait_latest_turno(
        self, *clients: _TestClient, timeout: float = 4.0
    ) -> dict[str, Any]:
        """Espera hasta recibir un mensaje ``turno`` en algún cliente.

        Returns:
            Primer mensaje ``turno`` disponible tras la espera.

        """
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            turno = self._latest_turno(*clients)
            if turno is not None:
                return turno
            time.sleep(0.05)
        self.fail("No se recibió mensaje turno")
        return {}

    def _client_for_user(
        self,
        c1: _TestClient,
        c2: _TestClient,
        uid1: int,
        uid2: int,
        user_id: int,
    ) -> _TestClient:
        """Devuelve el cliente de test asociado a un ``user_id``.

        Returns:
            Cliente cuyo ``user_id`` coincide.

        """
        if user_id == uid1:
            return c1
        if user_id == uid2:
            return c2
        self.fail(f"user_id {user_id} no corresponde a ningún cliente")
        return c1

    def _finalize_current_turn(
        self,
        c1: _TestClient,
        c2: _TestClient,
        uid1: int,
        uid2: int,
    ) -> None:
        """Finaliza el turno del jugador activo según el último mensaje ``turno``."""
        turno = self._wait_latest_turno(c1, c2)
        active_id = turno.get("jugador_actual_id")
        self.assertIsNotNone(active_id, "turno sin jugador_actual_id")
        if active_id is None:
            return
        client = self._client_for_user(c1, c2, uid1, uid2, int(active_id))
        client.send({"mensaje": "finalizar_turno"})
        time.sleep(0.2)

    def _find_adjacent_enemy_pair(self, attacker_id: int) -> tuple[str, str] | None:
        """Busca origen/destino adyacentes entre enemigos (sin exigir unidades).

        Returns:
            Par ``(origen, destino)`` o ``None`` si no hay frontera enemiga.

        """
        game = self._server.game
        self.assertIsNotNone(game, "partida no iniciada")
        if game is None:
            return None
        mapa = game.mapa()
        for pais in mapa.paises():
            if mapa.ocupado_por(pais) != attacker_id:
                continue
            for vecino in mapa.obtener_paises_adyacentes(pais):
                owner = mapa.ocupado_por(vecino)
                if owner is not None and owner != attacker_id:
                    return pais, vecino
        return None

    def test_receives_turno_after_game_start(self) -> None:
        """Tras iniciar la partida, los clientes reciben el mensaje de turno."""
        c1 = self._new_client()
        c2 = self._new_client()
        self._start_two_player_game(c1, c2)

        turno_c1 = c1.wait_for("turno", timeout=4.0)
        turno_c2 = c2.wait_for("turno", timeout=4.0)

        self.assertIsNotNone(turno_c1, "c1 no recibió mensaje turno")
        self.assertIsNotNone(turno_c2, "c2 no recibió mensaje turno")
        if turno_c1 is not None:
            self.assertIn("num_turno", turno_c1)
            self.assertIn("num_ronda", turno_c1)

    def test_receives_tiempo_during_active_turn(self) -> None:
        """El temporizador de turno envía mensajes tiempo a los clientes."""
        c1 = self._new_client()
        c2 = self._new_client()
        self._start_two_player_game(c1, c2, segundos=30)

        tiempo_c1 = c1.wait_for(
            "tiempo",
            timeout=5.0,
            extra_check=lambda m: int(m.get("tiempo", 0)) > 0,
        )
        tiempo_c2 = c2.wait_for(
            "tiempo",
            timeout=5.0,
            extra_check=lambda m: int(m.get("tiempo", 0)) > 0,
        )

        self.assertIsNotNone(tiempo_c1, "c1 no recibió mensaje tiempo")
        self.assertIsNotNone(tiempo_c2, "c2 no recibió mensaje tiempo")

    def test_receives_victory_after_round_with_low_threshold(self) -> None:
        """Al completar una ronda con umbral bajo, se difunde victoria."""
        c1 = self._new_client()
        c2 = self._new_client()
        uid1, uid2 = self._start_two_player_game(
            c1,
            c2,
            paises_para_victoria=1,
            objetivos_secretos=False,
        )

        self._finalize_current_turn(c1, c2, uid1, uid2)
        self._finalize_current_turn(c1, c2, uid1, uid2)

        victoria_c1 = c1.wait_for("victoria", timeout=5.0)
        victoria_c2 = c2.wait_for("victoria", timeout=5.0)

        self.assertIsNotNone(victoria_c1, "c1 no recibió mensaje victoria")
        self.assertIsNotNone(victoria_c2, "c2 no recibió mensaje victoria")
        if victoria_c1 is not None:
            self.assertIn("ganador_id", victoria_c1)
            self.assertIn("ganador_nombre", victoria_c1)

        self.assertIsNotNone(
            c1.wait_for(
                "estado",
                timeout=5.0,
                extra_check=lambda m: m.get("estado") == "Finalizado",
            ),
            "c1 no recibió estado Finalizado",
        )
        self.assertIsNotNone(
            c2.wait_for(
                "estado",
                timeout=5.0,
                extra_check=lambda m: m.get("estado") == "Finalizado",
            ),
            "c2 no recibió estado Finalizado",
        )
        self.assertTrue(self._server.estado.es_finalizado())
        timer = self._server._game_coordinator.turno_timer()  # noqa: SLF001
        self.assertIsNotNone(timer)
        if timer is not None:
            self.assertTrue(timer._stop_event.is_set())  # noqa: SLF001

        turnos_antes = [
            len([m for m in client.snapshot_received() if m.get("mensaje") == "turno"])
            for client in (c1, c2)
        ]
        c1.send({"mensaje": "finalizar_turno"})
        self.assertIsNotNone(
            c1.wait_for(
                "chat",
                timeout=2.0,
                extra_check=lambda m: m.get("msg_type") == "error",
            ),
            "el servidor aceptó finalizar un turno después de la victoria",
        )
        time.sleep(0.3)
        turnos_despues = [
            len([m for m in client.snapshot_received() if m.get("mensaje") == "turno"])
            for client in (c1, c2)
        ]
        self.assertEqual(turnos_despues, turnos_antes)

    def test_attack_sends_battle_result(self) -> None:
        """Tras los turnos iniciales, un ataque válido difunde resultado_batalla."""
        c1 = self._new_client()
        c2 = self._new_client()
        uid1, uid2 = self._start_two_player_game(
            c1,
            c2,
            segundos=30,
            paises_para_victoria=30,
            objetivos_secretos=False,
        )

        for _ in range(4):
            self._finalize_current_turn(c1, c2, uid1, uid2)

        turno = self._wait_latest_turno(c1, c2)
        attacker_id = turno.get("jugador_actual_id")
        self.assertIsNotNone(attacker_id)
        if attacker_id is None:
            return

        pair = self._find_adjacent_enemy_pair(int(attacker_id))
        self.assertIsNotNone(pair, "no hay par adyacente atacable en el mapa")
        if pair is None:
            return
        origen, destino = pair

        game = self._server.game
        self.assertIsNotNone(game)
        if game is not None:
            game.mapa().set_unidades(origen, MIN_UNITS_FOR_ATTACK)

        attacker = self._client_for_user(c1, c2, uid1, uid2, int(attacker_id))
        attacker.send({
            "mensaje": "atacar",
            "origen": origen,
            "destino": destino,
            "cantidad_unidades": 1,
        })

        resultado_c1 = c1.wait_for("resultado_batalla", timeout=5.0)
        resultado_c2 = c2.wait_for("resultado_batalla", timeout=5.0)

        self.assertIsNotNone(resultado_c1, "c1 no recibió resultado_batalla")
        self.assertIsNotNone(resultado_c2, "c2 no recibió resultado_batalla")
        if resultado_c1 is not None:
            self.assertEqual(resultado_c1.get("origen"), origen)
            self.assertEqual(resultado_c1.get("destino"), destino)
            self.assertIn("dados_atacante", resultado_c1)
            self.assertIn("dados_defensor", resultado_c1)


if __name__ == "__main__":
    unittest.main()
