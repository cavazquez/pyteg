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
import uuid
from typing import Any

from pyteg.codecs_utils import FrameCodecError, NulDelimitedUtf8Codec
from pyteg.config import MIN_UNITS_FOR_ATTACK
from pyteg.core.turnos.unit_pool import unidades_disponibles_en_pais
from pyteg.protocol import PROTOCOL_VERSION, map_hash_for_theme
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
_NON_MUTATING_COMMANDS = {
    "chat",
    "hello",
    "solicitar_snapshot",
    "solicitar_tarjetas",
}


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
                if estado.es_finalizado():
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
                if estado.es_jugando():
                    accepted = self._server.registrar_reconexion_pendiente(uid, client)
                    error_type = "game_in_progress"
                    error_message = (
                        "La partida ya comenzó. Sólo se aceptan reconexiones de "
                        "jugadores desconectados."
                    )
                else:
                    accepted = self._server.registrar_cliente(uid, client)
                    error_type = "room_full"
                    error_message = (
                        "La sala está completa. Intenta nuevamente más tarde."
                    )
                if not accepted:
                    client.transmisor.enviar_error(
                        error_type,
                        error_message,
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
            try:  # noqa: PLW0717 - el doble mantiene el socket hasta cerrar la prueba
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

    def send(self, data: dict[str, Any], *, auto_command_id: bool = True) -> None:
        """Envía un mensaje JSON al servidor.

        Args:
            data: Datos a serializar y enviar.
            auto_command_id: Agrega un ID a mutaciones que no lo incluyan.

        """
        if self._sock:
            payload_data = dict(data)
            if (
                auto_command_id
                and payload_data.get("mensaje") not in _NON_MUTATING_COMMANDS
                and "command_id" not in payload_data
            ):
                payload_data["command_id"] = uuid.uuid4().hex
            payload = json.dumps(payload_data) + "\0"
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

    def _new_client(self, *, handshake: bool = True) -> _TestClient:
        """Crea y conecta un cliente, registrándolo para cleanup.

        Args:
            handshake: Envía el ``hello`` compatible automáticamente.

        Returns:
            Cliente conectado listo para usar.

        """
        c = _TestClient()
        c.connect("127.0.0.1", self._port)
        self._clients.append(c)
        if handshake:
            c.send({
                "mensaje": "hello",
                "protocol_version": PROTOCOL_VERSION,
                "theme": "classic",
                "map_hash": map_hash_for_theme("classic"),
                "capabilities": ["snapshots", "command_results", "reconnect"],
                "rules": ["validated_phases", "one_card_per_turn"],
            })
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

    def _assign_adjacent_countries(self, user_id: int) -> tuple[str, str]:
        """Asigna dos países vecinos al jugador y les fija unidades conocidas.

        Returns:
            País de origen y destino, ambos asignados a ``user_id``.

        """
        game = self._server.game
        self.assertIsNotNone(game, "partida no iniciada")
        if game is None:
            self.fail("partida no iniciada")
        mapa = game.mapa()
        for origin in mapa.paises():
            neighbors = mapa.obtener_paises_adyacentes(origin)
            if not neighbors:
                continue
            destination = neighbors[0]
            mapa.asignar_pais(user_id, origin)
            mapa.asignar_pais(user_id, destination)
            mapa.set_unidades(origin, 3)
            mapa.set_unidades(destination, 1)
            return origin, destination
        self.fail("el mapa no tiene países adyacentes")
        return "", ""

    def _wait_for_new_error_chat(
        self, client: _TestClient, received_before: int, expected_message: str
    ) -> dict[str, Any] | None:
        """Espera un error de chat emitido después del índice indicado.

        Returns:
            El mensaje de error esperado, o ``None`` al vencer el plazo.

        """
        deadline = time.monotonic() + _READ_TIMEOUT
        while time.monotonic() < deadline:
            for message in client.snapshot_received()[received_before:]:
                if (
                    message.get("mensaje") == "chat"
                    and message.get("msg_type") == "error"
                    and message.get("msg") == expected_message
                ):
                    return message
            time.sleep(0.05)
        return None

    def _wait_for_new_protocol_error(
        self, client: _TestClient, received_before: int, expected_error_type: str
    ) -> dict[str, Any] | None:
        """Espera un error de protocolo emitido después del índice indicado.

        Returns:
            El mensaje de error esperado, o ``None`` al vencer el plazo.

        """
        deadline = time.monotonic() + _READ_TIMEOUT
        while time.monotonic() < deadline:
            for message in client.snapshot_received()[received_before:]:
                if (
                    message.get("mensaje") == "error"
                    and message.get("error_type") == expected_error_type
                ):
                    return message
            time.sleep(0.05)
        return None

    def _wait_for_new_command_result(
        self,
        client: _TestClient,
        received_before: int,
        command_id: str,
        timeout: float = _READ_TIMEOUT,
    ) -> dict[str, Any] | None:
        """Espera el resultado de un comando posterior al índice indicado.

        Returns:
            Resultado encontrado o ``None`` si vence el tiempo de espera.

        """
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            for message in client.snapshot_received()[received_before:]:
                if (
                    message.get("mensaje") == "command_result"
                    and message.get("command_id") == command_id
                ):
                    return message
            time.sleep(0.05)
        return None

    def _wait_for_new_state(
        self,
        client: _TestClient,
        received_before: int,
        expected_state: str,
        timeout: float = _READ_TIMEOUT,
    ) -> dict[str, Any] | None:
        """Espera un estado emitido después de una transición concreta.

        Returns:
            Mensaje de estado o ``None`` si vence el plazo.

        """
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            for message in client.snapshot_received()[received_before:]:
                if (
                    message.get("mensaje") == "estado"
                    and message.get("estado") == expected_state
                ):
                    return message
            time.sleep(0.05)
        return None

    def _assert_invalid_move_amount(
        self,
        client: _TestClient,
        origin: str,
        destination: str,
        amount: object,
    ) -> None:
        """Comprueba que una cantidad TCP inválida no muta países ni desconecta."""
        game = self._server.game
        self.assertIsNotNone(game, "partida no iniciada")
        if game is None:
            return
        mapa = game.mapa()
        units_before = (
            mapa.cantidad_unidades(origin),
            mapa.cantidad_unidades(destination),
        )
        received_before = len(client.snapshot_received())
        payload: dict[str, Any] = {
            "mensaje": "mover_unidad",
            "origen": origin,
            "destino": destination,
            "cantidad": amount,
        }
        client.send(payload)

        error = self._wait_for_new_protocol_error(
            client, received_before, "invalid_field"
        )

        self.assertIsNotNone(
            error, f"La cantidad inválida {amount!r} no devolvió error"
        )
        self.assertEqual(
            (mapa.cantidad_unidades(origin), mapa.cantidad_unidades(destination)),
            units_before,
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

    def test_command_before_handshake_is_rejected_without_mutation(self) -> None:
        """Un cliente sin hello no puede configurar ni iniciar la sala."""
        client = self._new_client(handshake=False)

        received_before = len(client.snapshot_received())
        client.send({"mensaje": "empezar", "segundos": 77})
        error = self._wait_for_new_protocol_error(
            client, received_before, "handshake_required"
        )

        self.assertIsNotNone(error, "No se rechazó el comando sin handshake")
        self.assertTrue(self._server.estado.es_inicial())
        self.assertIsNone(self._server.game)

        client.send({
            "mensaje": "hello",
            "protocol_version": PROTOCOL_VERSION,
            "theme": "classic",
            "map_hash": "invalid-map-hash",
        })
        incompatible = client.wait_for(
            "error",
            extra_check=lambda data: data.get("error_type") == "incompatible_map",
        )
        self.assertIsNotNone(incompatible, "No se rechazó el mapa incompatible")
        self.assertIsNotNone(
            client.wait_for(
                "hello_ack", extra_check=lambda data: data.get("accepted") is False
            ),
            "No se informó el rechazo del handshake",
        )

    def test_start_rejects_registered_client_without_handshake(self) -> None:
        """La ausencia de hello de un jugador impide iniciar la partida."""
        admin = self._new_client()
        legacy = self._new_client(handshake=False)

        admin.send({"mensaje": "empezar", "segundos": 77})
        self.assertIsNotNone(
            admin.wait_for(
                "estado",
                extra_check=lambda data: data.get("estado") == "EsperarJugadores",
            ),
            "El administrador no pudo configurar la sala",
        )

        received_before = len(admin.snapshot_received())
        admin.send({"mensaje": "empezar_partida"})
        error = self._wait_for_new_protocol_error(
            admin, received_before, "handshake_required"
        )

        self.assertIsNotNone(error, "Se inició la partida con un cliente sin hello")
        self.assertTrue(self._server.estado.es_esperando_jugadores())
        self.assertIsNone(self._server.game)
        legacy.close()

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

        deadline = time.monotonic() + _READ_TIMEOUT
        while time.monotonic() < deadline and not game.jugador_esta_desconectado(
            first_id
        ):
            time.sleep(0.05)

        countries_after = [
            pais
            for pais in game.mapa().paises()
            if game.mapa().ocupado_por(pais) == first_id
        ]
        self.assertIn(player, game.lista_jugadores())
        self.assertEqual(countries_after, countries_before)
        self.assertIn(color, self._server.color.colores_usados())
        self.assertTrue(game.jugador_esta_desconectado(first_id))
        self.assertNotIn(first_id, game.lista_jugadores_orden_turno())

    def test_game_in_progress_rejection_uses_structured_error(self) -> None:
        """Una conexión tardía sólo puede autenticarse como reconexión."""
        first = self._new_client()
        second = self._new_client()
        self._start_two_player_game(first, second)

        pending = self._new_client()
        self.assertIsNotNone(pending.wait_for("session_token"))
        received_before = len(pending.snapshot_received())
        pending.send({"mensaje": "chat", "msg": "no soy una reconexión"})
        error = pending.wait_for(
            "error",
            extra_check=lambda data: data.get("error_type") == "reconnect_required",
        )

        self.assertIsNotNone(error, "No se recibió rechazo estructurado")
        self.assertGreaterEqual(len(pending.snapshot_received()), received_before)
        pending.close()
        self._wait_for_client_count(2)

    def test_disconnected_client_can_reconnect_with_same_identity(  # noqa: PLR0914
        self,
    ) -> None:
        """Una reconexión recupera color, territorios y turno sin duplicarlo."""
        first = self._new_client()
        second = self._new_client()
        self._new_client()  # Mantiene dos jugadores activos tras la baja.
        cached_command = {
            "mensaje": "set_username",
            "username": "Cacheado",
            "command_id": "reconnect-cache-1",
        }
        first.send(cached_command)
        cached_result = first.wait_for(
            "command_result",
            extra_check=lambda data: data.get("command_id") == "reconnect-cache-1",
        )
        self.assertIsNotNone(cached_result, "No se cacheó el resultado previo")
        first_id, _second_id = self._start_two_player_game(first, second)
        token_message = first.wait_for(
            "session_token", extra_check=lambda data: data.get("user_id") == first_id
        )
        self.assertIsNotNone(token_message, "El jugador no recibió token de sesión")
        if token_message is None:
            return
        token = str(token_message["token"])

        game = self._server.game
        self.assertIsNotNone(game, "No se creó la partida")
        if game is None:
            return
        old_player = next(
            player for player in game.lista_jugadores() if player.userid() == first_id
        )
        old_color = old_player.color_actual()
        old_countries = [
            pais
            for pais in game.mapa().paises()
            if game.mapa().ocupado_por(pais) == first_id
        ]
        self.assertTrue(old_countries, "El jugador no recibió territorios")
        card = game.mazo().asignar_tarjeta(first_id)
        self.assertIsNotNone(card, "No se pudo preparar una tarjeta para sincronizar")
        if card is None:
            return
        missile_country = old_countries[0]
        game.mapa().agregar_misil(missile_country)

        first.close()
        self._wait_for_client_count(2)
        deadline = time.monotonic() + _READ_TIMEOUT
        while time.monotonic() < deadline and not game.jugador_esta_desconectado(
            first_id
        ):
            time.sleep(0.05)
        self.assertTrue(game.jugador_esta_desconectado(first_id))

        replacement = self._new_client()
        self.assertIsNotNone(replacement.wait_for("session_token"))
        replacement.send({"mensaje": "reconectar", "user_id": first_id, "token": token})
        self.assertIsNotNone(
            replacement.wait_for(
                "reconexion",
                extra_check=lambda data: data.get("user_id") == first_id,
            ),
            "No se confirmó la reconexión",
        )
        self.assertIsNotNone(
            replacement.wait_for(
                "tarjetas_jugador",
                extra_check=lambda data: any(
                    card_data.get("pais") == card.pais
                    for card_data in data.get("tarjetas", [])
                ),
            ),
            "No se sincronizaron las tarjetas privadas",
        )
        self.assertIsNotNone(
            replacement.wait_for(
                "misil_agregado",
                extra_check=lambda data: (
                    data.get("pais") == missile_country
                    and data.get("cantidad_misiles") == 1
                ),
            ),
            "No se sincronizó el inventario de misiles",
        )
        self._wait_for_client_count(3)

        current_player = next(
            player for player in game.lista_jugadores() if player.userid() == first_id
        )
        self.assertIsNot(current_player, old_player)
        self.assertFalse(game.jugador_esta_desconectado(first_id))
        self.assertEqual(current_player.color_actual(), old_color)
        self.assertEqual(
            [
                pais
                for pais in game.mapa().paises()
                if game.mapa().ocupado_por(pais) == first_id
            ],
            old_countries,
        )
        self.assertIn(first_id, game.lista_jugadores_orden_turno())

        revision_before_retry = self._server.state_revision()
        received_before_retry = len(replacement.snapshot_received())
        replacement.send(cached_command)
        replayed = self._wait_for_new_command_result(
            replacement,
            received_before_retry,
            "reconnect-cache-1",
        )
        self.assertEqual(replayed, cached_result)
        self.assertEqual(self._server.state_revision(), revision_before_retry)

    def test_reconnected_client_recovers_private_secret_objective(self) -> None:
        """Una reconexión restaura el objetivo secreto sin filtrarlo."""
        first = self._new_client()
        second = self._new_client()
        self._new_client()  # Conserva dos jugadores conectados tras la baja.
        first_id, _second_id = self._start_two_player_game(
            first,
            second,
            objetivos_secretos=True,
        )

        first_objective = first.wait_for("objetivo_secreto")
        second_objective = second.wait_for("objetivo_secreto")
        self.assertIsNotNone(first_objective, "Faltó el objetivo privado del jugador 1")
        self.assertIsNotNone(
            second_objective, "Faltó el objetivo privado del jugador 2"
        )
        if first_objective is None or second_objective is None:
            return
        self.assertNotEqual(
            first_objective["objetivo_id"],
            second_objective["objetivo_id"],
            "Dos jugadores recibieron el mismo objetivo en la misma partida",
        )
        self.assertNotIn(
            first_objective["objetivo_id"],
            {
                message.get("objetivo_id")
                for message in second.snapshot_received()
                if message.get("mensaje") == "objetivo_secreto"
            },
        )

        token_message = first.wait_for("session_token")
        self.assertIsNotNone(token_message, "El jugador no recibió token de sesión")
        if token_message is None:
            return
        token = str(token_message["token"])

        first.close()
        self._wait_for_client_count(2)
        replacement = self._new_client()
        self.assertIsNotNone(replacement.wait_for("session_token"))
        replacement.send({"mensaje": "reconectar", "user_id": first_id, "token": token})
        self.assertIsNotNone(
            replacement.wait_for(
                "reconexion",
                extra_check=lambda data: data.get("user_id") == first_id,
            ),
            "No se confirmó la reconexión",
        )
        recovered_objective = replacement.wait_for("objetivo_secreto")
        self.assertIsNotNone(
            recovered_objective,
            "La reconexión no restauró el objetivo secreto privado",
        )
        if recovered_objective is not None:
            self.assertEqual(
                recovered_objective["objetivo_id"],
                first_objective["objetivo_id"],
            )
            self.assertEqual(
                recovered_objective["descripcion"],
                first_objective["descripcion"],
            )

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
            {
                "mensaje": "set_username",
                "username": "Café",
                "command_id": "fragmented-username",
            },
            ensure_ascii=False,
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

    def test_mutation_without_command_id_is_rejected_without_revision(self) -> None:
        """El servidor exige ID antes de ejecutar cualquier mutación TCP."""
        client = self._new_client()
        self.assertIsNotNone(client.wait_for("user_id"), "Cliente sin user_id")
        revision_before = self._server.state_revision()
        received_before = len(client.snapshot_received())

        client.send(
            {"mensaje": "set_username", "username": "SinId"},
            auto_command_id=False,
        )
        error = self._wait_for_new_protocol_error(
            client, received_before, "command_id_required"
        )

        self.assertIsNotNone(error, "No se rechazó la mutación sin command_id")
        self.assertEqual(self._server.state_revision(), revision_before)
        self.assertNotEqual(
            self._server.dame_clientes()[0].username(),
            "SinId",
        )

    def test_command_id_replay_and_conflict_are_idempotent_over_tcp(self) -> None:
        """Un retry idéntico no repite la mutación y otro payload se rechaza."""
        client = self._new_client()
        self.assertIsNotNone(client.wait_for("user_id"), "Cliente sin user_id")
        command_id = "tcp-idempotency-1"
        payload = {
            "mensaje": "set_username",
            "username": "Idempotente",
            "command_id": command_id,
        }

        received_before = len(client.snapshot_received())
        client.send(payload)
        first = self._wait_for_new_command_result(client, received_before, command_id)
        self.assertIsNotNone(first, "Faltó resultado del primer comando")
        if first is None:
            return
        revision = int(first["revision"])

        received_before = len(client.snapshot_received())
        client.send(payload)
        replay = self._wait_for_new_command_result(client, received_before, command_id)
        self.assertEqual(replay, first)
        self.assertEqual(self._server.state_revision(), revision)

        received_before = len(client.snapshot_received())
        client.send({**payload, "username": "Otro"})
        conflict = self._wait_for_new_command_result(
            client, received_before, command_id
        )
        self.assertIsNotNone(conflict, "Faltó rechazo del command_id reutilizado")
        if conflict is not None:
            self.assertFalse(conflict["accepted"])
            self.assertEqual(conflict["error_code"], "command_id_conflict")
            self.assertEqual(conflict["revision"], revision)
        self.assertEqual(self._server.state_revision(), revision)

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

    def test_move_outside_active_turn_returns_error_without_mutating_map(self) -> None:
        """Un movimiento TCP de otro jugador conserva el mapa y devuelve error."""
        first = self._new_client()
        second = self._new_client()
        first_id, second_id = self._start_two_player_game(first, second)
        turn = self._wait_latest_turno(first, second)
        active_id = turn.get("jugador_actual_id")
        self.assertIsNotNone(active_id, "turno sin jugador_actual_id")
        if active_id is None:
            return

        inactive_id = second_id if int(active_id) == first_id else first_id
        inactive_client = second if inactive_id == second_id else first
        origin, destination = self._assign_adjacent_countries(inactive_id)
        game = self._server.game
        if game is None:
            return
        mapa = game.mapa()
        units_before = (
            mapa.cantidad_unidades(origin),
            mapa.cantidad_unidades(destination),
        )

        received_before = len(inactive_client.snapshot_received())
        inactive_client.send({
            "mensaje": "mover_unidad",
            "origen": origin,
            "destino": destination,
            "cantidad": 1,
        })
        error = self._wait_for_new_error_chat(
            inactive_client, received_before, "No es tu turno"
        )

        self.assertIsNotNone(error, "El movimiento fuera de turno no devolvió error")
        self.assertEqual(
            (mapa.cantidad_unidades(origin), mapa.cantidad_unidades(destination)),
            units_before,
        )

    def test_invalid_move_amounts_preserve_map_and_tcp_connection(self) -> None:
        """Una cantidad inválida no cambia países y el cliente puede seguir jugando."""
        first = self._new_client()
        second = self._new_client()
        first_id, second_id = self._start_two_player_game(first, second)
        turn = self._wait_latest_turno(first, second)
        active_id = turn.get("jugador_actual_id")
        self.assertIsNotNone(active_id, "turno sin jugador_actual_id")
        if active_id is None:
            return

        active_client = self._client_for_user(
            first, second, first_id, second_id, int(active_id)
        )
        origin, destination = self._assign_adjacent_countries(int(active_id))
        invalid_amounts: tuple[object, ...] = (0, -5, True, 1.5, "1", None)
        for amount in invalid_amounts:
            with self.subTest(amount=amount):
                self._assert_invalid_move_amount(
                    active_client, origin, destination, amount
                )

        active_client.send({"mensaje": "chat", "msg": "Sigo conectado"})
        recovered = active_client.wait_for(
            "chat",
            extra_check=lambda message: str(message.get("msg")).endswith(
                ": Sigo conectado"
            ),
        )
        self.assertIsNotNone(recovered, "El cliente se desconectó tras el error")

    # ------------------------------------------------------------------
    # Test 5: flujo completo — inicio de partida con dos jugadores
    # ------------------------------------------------------------------
    def test_game_start_flow(self) -> None:
        """Admin inicia la partida; ambos clientes reciben estado JUGANDO."""
        c1 = self._new_client()  # admin (primer cliente = user_id 1)
        c2 = self._new_client()
        self._start_two_player_game(c1, c2)

    def test_admin_disconnects_during_game_and_successor_can_rematch(self) -> None:
        """La partida termina con un único admin sucesor capaz de revancha."""
        c1 = self._new_client()
        c2 = self._new_client()
        c3 = self._new_client()
        uid1, uid2 = self._start_two_player_game(c1, c2)
        uid3_message = c3.wait_for("user_id")
        self.assertIsNotNone(uid3_message, "c3 no recibió user_id")

        c1.close()
        self._wait_for_client_count(2)
        game = self._server.game
        self.assertIsNotNone(game, "No se creó la partida")
        if game is None:
            return
        deadline = time.monotonic() + _READ_TIMEOUT
        while time.monotonic() < deadline and not game.jugador_esta_desconectado(uid1):
            time.sleep(0.05)
        self.assertTrue(game.jugador_esta_desconectado(uid1))

        self.assertEqual(
            self._server.public_snapshot()["players"][0]["admin"],
            False,
        )
        self.assertTrue(self._server.finalizar_partida())
        successor_admin = c2.wait_for("sosadmin", timeout=4.0)
        self.assertIsNotNone(successor_admin, "c2 no recibió la autoridad de sala")
        final_snapshot = c2.wait_for(
            "snapshot",
            timeout=4.0,
            extra_check=lambda message: (
                message.get("estado") == "Finalizado"
                and any(
                    player.get("userid") == uid2 and player.get("admin")
                    for player in message.get("players", [])
                )
            ),
        )
        self.assertIsNotNone(final_snapshot, "El snapshot final no anunció al sucesor")
        c2.send({"mensaje": "volver_lobby"})
        self.assertIsNotNone(
            c2.wait_for(
                "estado",
                timeout=4.0,
                extra_check=lambda message: message.get("estado") == "EsperarJugadores",
            ),
            "El sucesor no pudo solicitar la revancha",
        )

    def test_rematch_isolates_state_after_disconnect_and_reconnect(  # noqa: C901, PLR0912, PLR0914, PLR0915
        self,
    ) -> None:
        """Dos partidas consecutivas no comparten estado privado ni cachés."""
        c1 = self._new_client()
        c2 = self._new_client()
        c3 = self._new_client()
        uid3_message = c3.wait_for("user_id")
        self.assertIsNotNone(uid3_message, "c3 no recibió user_id")
        if uid3_message is None:
            return
        uid3 = int(uid3_message["user_id"])
        token_message = c3.wait_for(
            "session_token", extra_check=lambda message: message.get("user_id") == uid3
        )
        self.assertIsNotNone(token_message, "c3 no recibió token de sesión")
        if token_message is None:
            return
        token = str(token_message["token"])

        reused_command_id = "rematch-command-id"
        received_before_first = len(c2.snapshot_received())
        c2.send({
            "mensaje": "set_username",
            "username": "Primera partida",
            "command_id": reused_command_id,
        })
        first_command = self._wait_for_new_command_result(
            c2,
            received_before_first,
            reused_command_id,
        )
        self.assertIsNotNone(
            first_command, "No se cacheó el comando de la primera partida"
        )
        first_ids = self._start_two_player_game(
            c1,
            c2,
            objetivos_secretos=True,
            misiles_habilitados=True,
        )
        uid1, uid2 = first_ids
        first_snapshot = c1.wait_for(
            "snapshot",
            extra_check=lambda message: message.get("estado") == "JUGANDO",
        )
        self.assertIsNotNone(first_snapshot, "Faltó snapshot de la primera partida")
        if first_snapshot is None:
            return

        game_one = self._server.game
        self.assertIsNotNone(game_one, "No se creó la primera partida")
        if game_one is None:
            return
        first_card = game_one.mazo().asignar_tarjeta(uid1)
        self.assertIsNotNone(first_card, "No se asignó la tarjeta de prueba")
        missile_country = next(iter(game_one.mapa().paises()))
        game_one.mapa().agregar_misil(missile_country)
        first_objective = c1.wait_for("objetivo_secreto")
        self.assertIsNotNone(first_objective, "Faltó el objetivo de la primera partida")

        c3.close()
        self._wait_for_client_count(2)
        deadline = time.monotonic() + _READ_TIMEOUT
        while time.monotonic() < deadline and not game_one.jugador_esta_desconectado(
            uid3
        ):
            time.sleep(0.05)
        self.assertTrue(game_one.jugador_esta_desconectado(uid3))

        replacement = self._new_client()
        self.assertIsNotNone(replacement.wait_for("session_token"))
        replacement.send({"mensaje": "reconectar", "user_id": uid3, "token": token})
        self.assertIsNotNone(
            replacement.wait_for(
                "reconexion",
                extra_check=lambda message: message.get("user_id") == uid3,
            ),
            "c3 no pudo reconectar antes de la revancha",
        )
        self._wait_for_client_count(3)

        revision_first = int(first_snapshot["revision"])
        self.assertTrue(self._server.finalizar_partida())
        received_before_lobby = len(c1.snapshot_received())
        c1.send({"mensaje": "volver_lobby"})
        lobby_snapshot: dict[str, Any] | None = None
        deadline = time.monotonic() + _READ_TIMEOUT
        while time.monotonic() < deadline and lobby_snapshot is None:
            for message in c1.snapshot_received()[received_before_lobby:]:
                if (
                    message.get("mensaje") == "snapshot"
                    and message.get("estado") == "EsperarJugadores"
                ):
                    lobby_snapshot = message
                    break
            time.sleep(0.05)
        self.assertIsNotNone(lobby_snapshot, "No se publicó el lobby de la revancha")
        if lobby_snapshot is None:
            return
        self.assertGreater(int(lobby_snapshot["revision"]), revision_first)
        private_reset: dict[str, dict[str, Any]] = {}
        private_reset_kinds = frozenset({
            "tarjetas_jugador",
            "unidades_disponibles",
            "objetivo_secreto",
        })
        deadline = time.monotonic() + _READ_TIMEOUT
        while time.monotonic() < deadline and len(private_reset) < len(
            private_reset_kinds
        ):
            for message in c1.snapshot_received()[received_before_lobby:]:
                kind = message.get("mensaje")
                if kind in private_reset_kinds:
                    private_reset[str(kind)] = message
            time.sleep(0.05)
        self.assertEqual(private_reset["tarjetas_jugador"].get("tarjetas"), [])
        self.assertEqual(private_reset["unidades_disponibles"].get("unidades"), {})
        self.assertEqual(
            (
                private_reset["objetivo_secreto"].get("objetivo_id"),
                private_reset["objetivo_secreto"].get("descripcion"),
            ),
            ("", ""),
        )
        self.assertIsNone(self._server.game)
        self.assertEqual(self._server.mazo.cantidad_tarjetas_asignadas(), 0)
        self.assertEqual(self._server.objetivos_secretos.objetivos_asignados, {})
        self.assertFalse(self._server.misiles_habilitados())
        self.assertTrue(
            all(
                self._server.mapa.ocupado_por(pais) is None
                for pais in self._server.mapa.paises()
            )
        )
        self.assertTrue(
            all(
                self._server.mapa.cantidad_misiles(pais) == 0
                for pais in self._server.mapa.paises()
            )
        )

        received_before_retry = len(c2.snapshot_received())
        c2.send({
            "mensaje": "set_username",
            "username": "Segunda partida",
            "command_id": reused_command_id,
        })
        second_command = self._wait_for_new_command_result(
            c2,
            received_before_retry,
            reused_command_id,
        )
        self.assertIsNotNone(
            second_command, "No se aceptó el ID de comando en la revancha"
        )
        if second_command is not None:
            self.assertTrue(second_command["accepted"])

        self._start_two_player_game(
            c1,
            c2,
            objetivos_secretos=False,
            misiles_habilitados=False,
        )
        game_two = self._server.game
        self.assertIsNotNone(game_two, "No se creó la segunda partida")
        if game_two is None:
            return
        self.assertIsNot(game_two, game_one)
        self.assertEqual(game_two.mazo().cantidad_tarjetas_asignadas(), 0)
        self.assertEqual(self._server.objetivos_secretos.objetivos_asignados, {})
        self.assertTrue(
            all(
                game_two.mapa().cantidad_misiles(pais) == 0
                for pais in game_two.mapa().paises()
            )
        )
        self.assertGreater(
            self._server.state_revision(), int(lobby_snapshot["revision"])
        )
        self.assertIn(
            uid2, [int(client.userid()) for client in self._server.dame_clientes()]
        )

    def test_non_admin_rematch_does_not_clean_finalized_game(self) -> None:
        """Una revancha no autorizada conserva intacto el estado final."""
        admin = self._new_client()
        other = self._new_client()
        self._start_two_player_game(admin, other)
        game = self._server.game
        self.assertIsNotNone(game, "No se creó la partida")
        if game is None:
            return
        card = game.mazo().asignar_tarjeta(1)
        self.assertIsNotNone(card, "No se asignó la tarjeta de prueba")
        missile_country = next(iter(game.mapa().paises()))
        game.mapa().agregar_misil(missile_country)
        self.assertTrue(self._server.finalizar_partida())

        received_before = len(other.snapshot_received())
        other.send({"mensaje": "volver_lobby"})
        error = self._wait_for_new_protocol_error(other, received_before, "not_admin")

        self.assertIsNotNone(error, "La revancha no autorizada no fue rechazada")
        self.assertTrue(self._server.estado.es_finalizado())
        self.assertIs(self._server.game, game)
        self.assertEqual(self._server.mazo.cantidad_tarjetas_asignadas(), 1)
        self.assertEqual(self._server.mapa.cantidad_misiles(missile_country), 1)

    def test_snapshot_contract_is_complete_equal_and_resyncable(self) -> None:
        """Tres clientes reciben el mismo snapshot público y pueden resincronizar."""
        c1 = self._new_client()
        c2 = self._new_client()
        c3 = self._new_client()
        self._start_two_player_game(c1, c2)

        snapshots: list[dict[str, Any]] = []
        for client in (c1, c2, c3):
            snapshot = client.wait_for(
                "snapshot",
                timeout=4.0,
                extra_check=lambda message: (
                    message.get("estado") == "JUGANDO"
                    and message.get("snapshot_version") == 1
                ),
            )
            self.assertIsNotNone(snapshot, "Faltó snapshot inicial")
            if snapshot is not None:
                snapshots.append(snapshot)

        self.assertEqual(len(snapshots), 3)
        self.assertEqual(snapshots[0], snapshots[1])
        self.assertEqual(snapshots[1], snapshots[2])
        snapshot = snapshots[0]
        self.assertIn("configuracion", snapshot)
        self.assertIn("refuerzos_pendientes", snapshot)
        self.assertTrue(
            all("misiles" in country for country in snapshot["countries"].values())
        )
        self.assertTrue(
            all(
                {
                    "userid",
                    "username",
                    "color",
                    "admin",
                    "connected",
                    "eliminated",
                }.issubset(player)
                for player in snapshot["players"]
            )
        )
        self.assertNotIn("tarjetas", snapshot)
        self.assertNotIn("objetivo_id", snapshot)

        revision = int(snapshot["revision"])
        server_revision = self._server.state_revision()
        c1.send({
            "mensaje": "solicitar_snapshot",
            "command_id": "snapshot-resync",
        })
        resync = c1.wait_for(
            "snapshot",
            timeout=4.0,
            extra_check=lambda message: message.get("resync") is True,
        )
        result = c1.wait_for(
            "command_result",
            timeout=4.0,
            extra_check=lambda message: message.get("command_id") == "snapshot-resync",
        )
        self.assertIsNotNone(resync, "No se devolvió snapshot de resincronización")
        self.assertIsNotNone(result, "Faltó confirmación de solicitar_snapshot")
        if resync is not None and result is not None:
            self.assertEqual(resync["revision"], revision)
            self.assertEqual(result["revision"], revision)
            self.assertTrue(result["accepted"])
        self.assertEqual(self._server.state_revision(), server_revision)

    def _start_two_player_game(  # noqa: PLR0913
        self,
        c1: _TestClient,
        c2: _TestClient,
        *,
        segundos: int = 60,
        paises_para_victoria: int | None = None,
        objetivos_secretos: bool | None = None,
        misiles_habilitados: bool | None = None,
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
        if misiles_habilitados is not None:
            empezar["misiles_habilitados"] = misiles_habilitados
        c1.send(empezar)
        time.sleep(0.1)
        received_before_start = {
            id(client): len(client.snapshot_received()) for client in (c1, c2)
        }
        c1.send({"mensaje": "empezar_partida"})

        self.assertIsNotNone(
            self._wait_for_new_state(c1, received_before_start[id(c1)], "JUGANDO"),
            "c1 no recibió estado JUGANDO",
        )
        self.assertIsNotNone(
            self._wait_for_new_state(c2, received_before_start[id(c2)], "JUGANDO"),
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

    def _prepare_current_turn(
        self,
        c1: _TestClient,
        c2: _TestClient,
        uid1: int,
        uid2: int,
    ) -> tuple[int, _TestClient]:
        """Completa la colocación pendiente del turno vigente.

        Returns:
            Tupla con el jugador activo y su cliente TCP.

        """
        game = self._server.game
        self.assertIsNotNone(game, "partida no iniciada")
        if game is None:
            self.fail("partida no iniciada")

        turno = game.turno_actual()
        active_id = int(turno.jugador_actual())
        client = self._client_for_user(c1, c2, uid1, uid2, active_id)

        if game.fase_actual() == "colocacion":
            deadline = time.monotonic() + _READ_TIMEOUT
            while game.fase_actual() == "colocacion" and time.monotonic() < deadline:
                turno_actual = game.turno_actual()
                country = next(
                    (
                        pais
                        for pais in game.mapa().paises()
                        if (
                            game.mapa().ocupado_por(pais) == active_id
                            and unidades_disponibles_en_pais(
                                turno_actual, game.mapa().continente(pais)
                            )
                            > 0
                        )
                    ),
                    None,
                )
                self.assertIsNotNone(country, "El jugador de turno no tiene países")
                if country is None:
                    return active_id, client
                pending_before = int(game.refuerzos_pendientes())
                client.send({
                    "mensaje": "agregar_unidad",
                    "pais": country,
                    "tipo_unidad": "infanteria",
                    "cantidad": 1,
                })
                while (
                    time.monotonic() < deadline
                    and game.fase_actual() == "colocacion"
                    and int(game.refuerzos_pendientes()) >= pending_before
                ):
                    time.sleep(0.05)
            self.assertEqual(game.fase_actual(), "acciones")

        return active_id, client

    def _finalize_current_turn(
        self,
        c1: _TestClient,
        c2: _TestClient,
        uid1: int,
        uid2: int,
    ) -> None:
        """Completa la colocación y finaliza el turno vigente en el servidor."""
        game = self._server.game
        self.assertIsNotNone(game, "partida no iniciada")
        if game is None:
            return

        _active_id, client = self._prepare_current_turn(c1, c2, uid1, uid2)
        marker_before = (
            int(game.num_ronda()),
            int(game.id_turno_actual()),
            int(game.turno_actual().jugador_actual()),
        )

        client.send({"mensaje": "finalizar_turno"})
        deadline = time.monotonic() + _READ_TIMEOUT
        while time.monotonic() < deadline:
            if self._server.estado.es_finalizado():
                return
            marker_after = (
                int(game.num_ronda()),
                int(game.id_turno_actual()),
                int(game.turno_actual().jugador_actual()),
            )
            if marker_after != marker_before:
                return
            time.sleep(0.05)
        self.fail("El servidor no avanzó al finalizar el turno")

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

        self._prepare_current_turn(c1, c2, uid1, uid2)

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
