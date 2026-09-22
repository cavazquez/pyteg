"""Verifica colas TCP aisladas ante un cliente que deja de leer.

El smoke usa dos conexiones TCP de loopback sobre el escritor productivo de
``ConnectionServer``. Una conexión no lee durante la inundación y debe ser
cerrada cuando alcanza la cola acotada; la otra lee en paralelo y debe seguir
recibiendo mensajes posteriores. No inicia una partida porque el objetivo es
aislar la presión de salida del transporte.

Uso desde la raíz del repositorio::

    uv run python scripts/stress_slow_clients.py
"""

from __future__ import annotations

import argparse
import contextlib
import json
import socket
import threading
import time
from typing import Any

from pyteg.codecs_utils import FrameCodecError, NulDelimitedUtf8Codec
from pyteg.server.conexion.connection import ConnectionServer

DEFAULT_FRAMES = 256
DEFAULT_PAYLOAD_BYTES = 32 * 1024
DEFAULT_TIMEOUT = 5.0
MIN_FRAMES = 2
_SOCKET_BUFFER_BYTES = 4 * 1024
_RECEIVE_BUFFER_BYTES = 64 * 1024
_HEALTHY_DURING = '{"mensaje":"healthy-during"}'
_HEALTHY_FINAL = '{"mensaje":"healthy-final"}'
_HEALTHY_AFTER = '{"mensaje":"healthy-after"}'


def _parse_args() -> argparse.Namespace:
    """Parsea los parámetros del stress de clientes lentos.

    Returns:
        Argumentos validados de la línea de comandos.

    """
    parser = argparse.ArgumentParser(
        description="Stress TCP: cliente lento frente a cliente saludable.",
    )
    parser.add_argument("--frames", type=int, default=DEFAULT_FRAMES)
    parser.add_argument("--payload-bytes", type=int, default=DEFAULT_PAYLOAD_BYTES)
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT)
    args = parser.parse_args()
    if args.frames < MIN_FRAMES:
        parser.error(f"--frames debe ser al menos {MIN_FRAMES}")
    if args.payload_bytes <= 0:
        parser.error("--payload-bytes debe ser positivo")
    if args.timeout <= 0:
        parser.error("--timeout debe ser positivo")
    return args


def _open_tcp_pair() -> tuple[socket.socket, socket.socket]:
    """Crea un par cliente-servidor TCP sobre loopback.

    Returns:
        Tupla ``(socket_del_servidor, socket_del_cliente)``.

    Raises:
        OSError: Si no se puede abrir o aceptar la conexión local.

    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener:
        listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        listener.bind(("127.0.0.1", 0))
        listener.listen(1)
        address = listener.getsockname()
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            client_socket.connect(address)
            server_socket, _address = listener.accept()
        except OSError:
            client_socket.close()
            raise
    return server_socket, client_socket


def _reader_loop(
    peer: socket.socket,
    received: list[str],
    received_lock: threading.Lock,
    stop: threading.Event,
    timeout: float,
) -> None:
    """Drena la conexión saludable y registra las tramas completas."""
    codec = NulDelimitedUtf8Codec()
    peer.settimeout(min(timeout, 0.1))
    while not stop.is_set():
        try:
            chunk = peer.recv(_RECEIVE_BUFFER_BYTES)
        except TimeoutError:
            continue
        except OSError:
            return
        if not chunk:
            return
        try:
            messages = codec.feed(chunk)
        except FrameCodecError:
            return
        with received_lock:
            received.extend(messages)


def _wait_for_message(
    received: list[str],
    received_lock: threading.Lock,
    expected: str,
    timeout: float,
) -> bool:
    """Espera un marcador recibido por el cliente saludable.

    Returns:
        ``True`` si apareció la trama esperada antes del vencimiento.

    """
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        with received_lock:
            if expected in received:
                return True
        time.sleep(0.01)
    with received_lock:
        return expected in received


def _wait_for_eof(peer: socket.socket, timeout: float) -> bool:
    """Drena los bytes ya escritos y espera EOF del cliente lento.

    Returns:
        ``True`` si se observó EOF o un cierre del socket.

    """
    deadline = time.monotonic() + timeout
    peer.settimeout(min(timeout, 0.1))
    while time.monotonic() < deadline:
        try:
            if not peer.recv(_RECEIVE_BUFFER_BYTES):
                return True
        except TimeoutError:
            continue
        except OSError:
            return True
    return False


def _build_payload(payload_bytes: int) -> str:
    """Construye una trama válida suficientemente grande para llenar TCP.

    Returns:
        JSON serializado con el payload solicitado.

    """
    return json.dumps({"mensaje": "stress", "payload": "x" * payload_bytes})


def run_stress(*, frames: int, payload_bytes: int, timeout: float) -> dict[str, Any]:
    """Ejecuta el stress y retorna evidencia serializable.

    Returns:
        Resultado con el cierre del cliente lento y los marcadores del saludable.

    Raises:
        RuntimeError: Si el cliente lento no se cierra o el saludable deja de
            recibir antes de tiempo.

    """
    started = time.monotonic()
    slow_server, slow_peer = _open_tcp_pair()
    healthy_server, healthy_peer = _open_tcp_pair()
    slow_connection = ConnectionServer(slow_server, ("slow", 1))
    healthy_connection = ConnectionServer(healthy_server, ("healthy", 2))
    received: list[str] = []
    received_lock = threading.Lock()
    reader_stop = threading.Event()
    reader = threading.Thread(
        target=_reader_loop,
        args=(healthy_peer, received, received_lock, reader_stop, timeout),
        name="pyteg-healthy-peer-reader",
        daemon=True,
    )
    reader.start()
    payload = _build_payload(payload_bytes)
    try:
        slow_server.setsockopt(
            socket.SOL_SOCKET, socket.SO_SNDBUF, _SOCKET_BUFFER_BYTES
        )
        slow_peer.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, _SOCKET_BUFFER_BYTES)
        for index in range(frames):
            slow_connection.send(payload)
            if index == 0:
                healthy_connection.send(_HEALTHY_DURING)

        slow_closed = _wait_for_eof(slow_peer, timeout)
        if not slow_closed:
            message = "El cliente lento no fue desconectado al saturar su cola"
            raise RuntimeError(message)

        healthy_connection.send(_HEALTHY_FINAL)
        if not _wait_for_message(received, received_lock, _HEALTHY_FINAL, timeout):
            message = "El cliente saludable no recibió el marcador final"
            raise RuntimeError(message)

        healthy_connection.send(_HEALTHY_AFTER)
        if not _wait_for_message(received, received_lock, _HEALTHY_AFTER, timeout):
            message = "El cliente saludable dejó de recibir después del stress"
            raise RuntimeError(message)

        with received_lock:
            healthy_messages = len(received)
        return {
            "status": "passed",
            "frames_attempted": frames,
            "payload_bytes": payload_bytes,
            "slow_peer_closed": slow_closed,
            "healthy_markers": 3,
            "healthy_messages": healthy_messages,
            "elapsed_seconds": round(time.monotonic() - started, 3),
        }
    finally:
        reader_stop.set()
        slow_connection.close(wait_for_writer=False)
        healthy_connection.close(wait_for_writer=False)
        with contextlib.suppress(OSError):
            slow_peer.close()
        with contextlib.suppress(OSError):
            healthy_peer.close()
        reader.join(timeout=1.0)


def main() -> int:
    """Ejecuta el stress y muestra JSON apto para CI.

    Returns:
        ``0`` si el cliente lento se aísla y el saludable sigue recibiendo;
        ``1`` ante cualquier incumplimiento.

    """
    args = _parse_args()
    try:
        result = run_stress(
            frames=args.frames,
            payload_bytes=args.payload_bytes,
            timeout=args.timeout,
        )
    except (OSError, RuntimeError) as error:
        result = {
            "status": "failed",
            "failure": str(error),
            "frames_attempted": args.frames,
            "payload_bytes": args.payload_bytes,
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
