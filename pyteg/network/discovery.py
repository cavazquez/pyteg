"""Descubrimiento UDP de salas; nunca publica identidad privada ni copias."""

from __future__ import annotations

import json
import socket
import threading
import time
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from pyteg.logger import get_logger
from pyteg.protocol import PROTOCOL_VERSION, map_hash_for_theme

if TYPE_CHECKING:
    from collections.abc import Callable

DISCOVERY_PORT = 45471
DISCOVERY_GROUP = "239.255.71.67"
ROOM_EXPIRY_SECONDS = 5.0
_DATAGRAM_LIMIT = 2048
_MAX_ROOMS = 64
_MAX_ROOM_TEXT = 120
_LOG = get_logger(__name__)


@dataclass(frozen=True)
class Room:
    """Anuncio público validado de una autoridad de sala."""

    session_id: str
    epoch: int
    name: str
    theme: str
    map_hash: str
    host: str
    port: int
    players: int
    state: str
    mode: str = "host"

    @classmethod
    def parse(cls, raw: bytes, host: str) -> Room | None:
        """Acepta sólo anuncios pequeños compatibles con nuestros mapas.

        Returns:
            Sala compatible o None si el anuncio no es válido.

        """
        if len(raw) > _DATAGRAM_LIMIT:
            return None
        try:
            data = json.loads(raw)
            mode = data.get("mode", "host") if isinstance(data, dict) else None
            if (
                not isinstance(data, dict)
                or mode not in {"host", "peer"}
                or (data.get("message"), data.get("protocol"))
                != ("pyteg_room", PROTOCOL_VERSION)
                or data.get("theme") not in {"classic", "revancha"}
                or data.get("map_hash") != map_hash_for_theme(data["theme"])
            ):
                return None
            for field in ("session_id", "name", "state"):
                if (
                    not isinstance(data.get(field), str)
                    or not 0 < len(data[field]) <= _MAX_ROOM_TEXT
                ):
                    return None
            for field, lower, upper in (
                ("epoch", 0, 2**31),
                ("port", 1, 65535),
                ("players", 0, 8),
            ):
                value = data.get(field)
                if type(value) is not int or not lower <= value <= upper:
                    return None
            return cls(
                data["session_id"],
                data["epoch"],
                data["name"],
                data["theme"],
                data["map_hash"],
                host,
                data["port"],
                data["players"],
                data["state"],
                data.get("mode", "host"),
            )
        except ValueError, TypeError, KeyError, OSError:
            return None


class RoomCatalog:
    """Deduplica autoridades por sala y descarta anuncios vencidos."""

    def __init__(self, clock: Callable[[], float] = time.monotonic) -> None:
        """Inicializa la lista con un reloj reemplazable."""
        self._clock = clock
        self._rooms: dict[str, tuple[Room, float]] = {}
        self._lock = threading.Lock()

    def receive(self, raw: bytes, host: str) -> None:
        """Incorpora una sala válida usando la dirección de origen del datagrama."""
        room = Room.parse(raw, host)
        if room is None:
            return
        with self._lock:
            previous = self._rooms.get(room.session_id)
            if previous is not None and room.epoch < previous[0].epoch:
                return
            if previous is None and len(self._rooms) >= _MAX_ROOMS:
                return
            self._rooms[room.session_id] = room, self._clock()

    def rooms(self) -> list[Room]:
        """Obtiene las salas que se anunciaron recientemente.

        Returns:
            Salas ordenadas por nombre y dirección.

        """
        with self._lock:
            now = self._clock()
            self._rooms = {
                key: value
                for key, value in self._rooms.items()
                if now - value[1] < ROOM_EXPIRY_SECONDS
            }
            return sorted(
                (value[0] for value in self._rooms.values()),
                key=lambda room: (room.name, room.host, room.port),
            )


class DiscoveryService:
    """Listener común con cierre explícito y multicast limitado a la LAN."""

    def __init__(
        self,
        *,
        port: int = DISCOVERY_PORT,
        interface: str = "0.0.0.0",  # noqa: S104
    ) -> None:
        """Reserva el puerto compartido de anuncios y consultas.

        Raises:
            OSError: Si la interfaz no permite descubrimiento UDP.

        """
        self.port = port
        self._stop = threading.Event()
        self._socket = socket.socket(
            socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP
        )
        try:
            self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            if hasattr(socket, "SO_REUSEPORT"):
                # macOS exige ambos flags para compartir el puerto multicast.
                self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
            self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            self._socket.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 1)
            self._socket.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_LOOP, 1)
            if interface != "0.0.0.0":  # noqa: S104
                self._socket.setsockopt(
                    socket.IPPROTO_IP,
                    socket.IP_MULTICAST_IF,
                    socket.inet_aton(interface),
                )
            self._socket.bind(("", port))
            membership = socket.inet_aton(DISCOVERY_GROUP) + socket.inet_aton(interface)
            self._socket.setsockopt(
                socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, membership
            )
            self._socket.settimeout(0.2)
        except OSError:
            self._socket.close()
            raise
        self._thread = threading.Thread(
            target=self._run, name="pyteg-lan-discovery", daemon=True
        )

    def start(self) -> None:
        """Arranca una única escucha."""
        self._thread.start()

    def send(
        self, data: dict[str, Any], address: tuple[str, int] | None = None
    ) -> None:
        """Publica o responde con un anuncio acotado."""
        raw = json.dumps(data, ensure_ascii=False).encode("utf-8")
        if len(raw) > _DATAGRAM_LIMIT or self._stop.is_set():
            return
        destinations = (
            [address]
            if address
            else [(DISCOVERY_GROUP, self.port), ("255.255.255.255", self.port)]
        )
        for destination in destinations:
            try:
                self._socket.sendto(raw, destination)
            except OSError as error:
                _LOG.debug("No se pudo enviar descubrimiento LAN: %s", error)

    def _run(self) -> None:
        next_tick = 0.0
        while not self._stop.is_set():
            if time.monotonic() >= next_tick:
                self.tick()
                next_tick = time.monotonic() + 1.0
            try:
                raw, address = self._socket.recvfrom(_DATAGRAM_LIMIT + 1)
            except TimeoutError:
                continue
            except OSError:
                break
            self.receive(raw, address)

    def tick(self) -> None:
        """Procesa un intervalo de descubrimiento."""

    def receive(self, raw: bytes, address: tuple[str, int]) -> None:
        """Procesa un datagrama recibido."""

    def close(self) -> None:
        """Detiene la escucha y libera el socket compartido."""
        self._stop.set()
        self._socket.close()
        if self._thread.is_alive() and threading.current_thread() is not self._thread:
            self._thread.join(timeout=1.0)


class RoomAnnouncer(DiscoveryService):
    """Anuncia la sala activa y contesta búsquedas explícitas."""

    def __init__(
        self,
        describe: Callable[[], dict[str, Any]],
        *,
        port: int = DISCOVERY_PORT,
        interface: str = "0.0.0.0",  # noqa: S104
    ) -> None:
        """Asocia el anuncio con datos públicos del anfitrión."""
        super().__init__(port=port, interface=interface)
        self._describe = describe

    def tick(self) -> None:
        """Publica el estado actual de la sala."""
        self.send(self._describe())

    def receive(self, raw: bytes, address: tuple[str, int]) -> None:
        """Responde sólo a consultas de Pyteg compatibles."""
        if len(raw) > _DATAGRAM_LIMIT:
            return
        try:
            data = json.loads(raw)
        except ValueError, UnicodeError:
            return
        if (
            isinstance(data, dict)
            and data.get("message") == "pyteg_find"
            and data.get("protocol") == PROTOCOL_VERSION
        ):
            self.send(self._describe(), address)


class RoomBrowser(DiscoveryService):
    """Busca salas sin bloquear el hilo gráfico."""

    def __init__(
        self,
        *,
        port: int = DISCOVERY_PORT,
        interface: str = "0.0.0.0",  # noqa: S104
    ) -> None:
        """Crea un catálogo vacío y una escucha UDP."""
        super().__init__(port=port, interface=interface)
        self.catalog = RoomCatalog()

    def tick(self) -> None:
        """Consulta las salas disponibles en la LAN."""
        self.send({"message": "pyteg_find", "protocol": PROTOCOL_VERSION})

    def receive(self, raw: bytes, address: tuple[str, int]) -> None:
        """Conserva las salas usando la IP real del anunciante."""
        self.catalog.receive(raw, address[0])
