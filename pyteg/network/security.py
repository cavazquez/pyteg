"""TLS con identidad fijada por invitación y pruebas de posesión frescas."""

# ruff: noqa: DOC201, DOC501, TRY003, EM101

from __future__ import annotations

import json
import secrets
import socket
import ssl
import time
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any
from urllib.parse import parse_qs, urlencode, urlsplit

from cryptography import x509
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from cryptography.x509.oid import NameOID

from pyteg.codecs_utils import NulDelimitedUtf8Codec
from pyteg.network.identity import Identity, hex_bytes, public_key, verify
from pyteg.persistence.archive import MAX_ARCHIVE_BYTES, canonical_bytes

SECURITY_VERSION = 1
HANDSHAKE_TIMEOUT = 3.0
_READ_SIZE = 65536
_MAX_PORT = 65535
_MAX_INVITATION_LENGTH = 1024


def certificate_key(certificate: bytes) -> str:
    """Extrae la identidad Ed25519 del certificado recibido durante TLS."""
    key = x509.load_der_x509_certificate(certificate).public_key()
    if not isinstance(key, Ed25519PublicKey):
        raise TypeError("El certificado no contiene una identidad de Pyteg")
    return key.public_bytes_raw().hex()


def check_certificate(certificate: bytes, expected_key: str) -> None:
    """Comprueba la identidad antes de enviar credenciales o datos de juego."""
    if not secrets.compare_digest(
        certificate_key(certificate), public_key(expected_key)
    ):
        raise ValueError("La identidad remota no coincide con la invitación")


class TlsCredentials:
    """Certificado efímero asociado a una identidad individual estable."""

    def __init__(self, identity: Identity) -> None:
        """Carga TLS sin dejar claves privadas en carpetas compartidas."""
        self.identity = identity
        self._directory = TemporaryDirectory(prefix="pyteg-tls-")
        subject = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "Pyteg")])
        now = datetime.now(UTC)
        certificate = (
            x509
            .CertificateBuilder()
            .subject_name(subject)
            .issuer_name(subject)
            .public_key(identity.key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(now - timedelta(minutes=5))
            .not_valid_after(now + timedelta(days=90))
            .sign(identity.key, None)
        )
        directory = Path(self._directory.name)
        cert_path, key_path = directory / "certificate.pem", directory / "identity.pem"
        cert_path.write_bytes(certificate.public_bytes(serialization.Encoding.PEM))
        key_path.touch(mode=0o600)
        key_path.write_bytes(
            identity.key.private_bytes(
                serialization.Encoding.PEM,
                serialization.PrivateFormat.PKCS8,
                serialization.NoEncryption(),
            )
        )
        self.context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        self.context.minimum_version = ssl.TLSVersion.TLSv1_3
        self.context.load_cert_chain(cert_path, key_path)
        # OpenSSL conserva el material cargado; los PEM dejan de ser necesarios.
        self._directory.cleanup()

    def accept(self, connection: socket.socket) -> ssl.SSLSocket:
        """Negocia TLS dentro del límite de tiempo de la conexión entrante."""
        connection.settimeout(HANDSHAKE_TIMEOUT)
        return self.context.wrap_socket(connection, server_side=True)


def connect_tls(
    address: tuple[str, int], expected_key: str, timeout: float
) -> ssl.SSLSocket:
    """Cifra la conexión y verifica la clave fijada, antes de enviar datos."""
    public_key(expected_key)
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    context.minimum_version = ssl.TLSVersion.TLSv1_3
    context.check_hostname = False
    # Las salas LAN no usan una CA pública: la invitación fija la clave exacta.
    context.verify_mode = ssl.CERT_NONE
    raw = socket.create_connection(address, timeout=timeout)
    connection = None
    try:
        connection = context.wrap_socket(raw, server_hostname=address[0])
        check_certificate(connection.getpeercert(binary_form=True) or b"", expected_key)
    except Exception:
        if connection is not None:
            connection.close()
        else:
            raw.close()
        raise
    return connection


def receive_json(
    connection: socket.socket, *, limit: int = MAX_ARCHIVE_BYTES
) -> dict[str, Any]:
    """Recibe exactamente una trama JSON dentro del límite establecido."""
    codec = NulDelimitedUtf8Codec(limit)
    deadline = time.monotonic() + (connection.gettimeout() or HANDSHAKE_TIMEOUT)
    while True:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise TimeoutError("Venció el plazo del handshake de red")
        connection.settimeout(remaining)
        chunk = connection.recv(_READ_SIZE)
        if not chunk:
            break
        frames = codec.feed(chunk)
        if frames:
            if len(frames) != 1 or codec.pending_bytes:
                raise ValueError("El handshake contiene tramas adicionales")
            value = json.loads(frames[0])
            if not isinstance(value, dict):
                raise ValueError("El mensaje de red debe ser un objeto")
            return value
    raise ConnectionError("La conexión terminó antes de completar el mensaje")


def send_json(connection: socket.socket, value: object) -> None:
    """Envía una trama canónica acotada."""
    raw = canonical_bytes(value)
    if len(raw) > MAX_ARCHIVE_BYTES:
        raise ValueError("El mensaje excede el tamaño permitido")
    connection.sendall(raw + b"\0")


def challenge() -> dict[str, Any]:
    """Obtiene una prueba nueva para cada conexión y evita reutilizar firmas."""
    return {"security": SECURITY_VERSION, "nonce": secrets.token_hex(32)}


def proof(
    identity: Identity, greeting: dict[str, Any], request: dict[str, Any]
) -> dict[str, Any]:
    """Vincula una petición y su autor con el desafío de este canal."""
    if greeting.get("security") != SECURITY_VERSION:
        raise ValueError("La conexión no admite el protocolo seguro de Pyteg")
    hex_bytes(greeting.get("nonce"), 32)
    content = {
        "security": SECURITY_VERSION,
        "nonce": greeting["nonce"],
        "request": request,
    }
    return {
        "request": request,
        "public_key": identity.public_key,
        "signature": identity.sign(content),
    }


def authenticate(
    greeting: dict[str, Any], response: dict[str, Any]
) -> tuple[dict[str, Any], str]:
    """Verifica posesión de la identidad antes de ejecutar la petición."""
    if set(response) != {"request", "public_key", "signature"}:
        raise ValueError("Prueba de identidad inválida")
    request = response["request"]
    key = public_key(response["public_key"])
    if not isinstance(request, dict) or any(name.startswith("_") for name in request):
        raise ValueError("Petición autenticada inválida")
    content = {
        "security": SECURITY_VERSION,
        "nonce": greeting["nonce"],
        "request": request,
    }
    if not verify(key, content, response["signature"]):
        raise ValueError("La firma no corresponde al desafío de esta conexión")
    return request, key


def receive_authenticated(
    connection: socket.socket, *, limit: int = MAX_ARCHIVE_BYTES
) -> dict[str, Any]:
    """Autentica una petición y agrega la identidad comprobada por el transporte."""
    greeting = challenge()
    send_json(connection, greeting)
    request, key = authenticate(greeting, receive_json(connection, limit=limit))
    return {**request, "_sender_key": key}


@dataclass(frozen=True)
class Invitation:
    """Destino, identidad y autorización compartidos por un medio de confianza."""

    mode: str
    host: str
    port: int
    session_id: str
    public_key: str
    token: str = field(repr=False)
    root_key: str = ""
    theme: str = "classic"

    def __post_init__(self) -> None:
        """Rechaza destinos ambiguos y credenciales no canónicas."""
        if (
            self.mode not in {"host", "peer"}
            or not self.host
            or any(char.isspace() or char in "/?#@\\" for char in self.host)
        ):
            raise ValueError("Invitación de Pyteg inválida")
        if type(self.port) is not int or not 1 <= self.port <= _MAX_PORT:
            raise ValueError("Puerto de invitación inválido")
        hex_bytes(self.session_id, 16)
        public_key(self.public_key)
        if not self.root_key:
            object.__setattr__(self, "root_key", self.public_key)
        public_key(self.root_key)
        hex_bytes(self.token, 32)
        if self.theme not in {"classic", "revancha"}:
            raise ValueError("Mapa de invitación inválido")

    def encode(self) -> str:
        """Obtiene un enlace para copiar y compartir con los jugadores."""
        query = urlencode({
            "v": SECURITY_VERSION,
            "room": self.session_id,
            "key": self.public_key,
            "root": self.root_key,
            "invite": self.token,
            "map": self.theme,
        })
        return f"pyteg://{self.mode}/{self.host}:{self.port}?{query}"

    @classmethod
    def parse(cls, value: str) -> Invitation:
        """Lee una invitación sin abrir conexiones ni aceptar campos desconocidos."""
        if len(value) > _MAX_INVITATION_LENGTH:
            raise ValueError("La invitación excede el tamaño permitido")
        parsed = urlsplit(value.strip())
        query = parse_qs(parsed.query, strict_parsing=True)
        valid_query = (
            set(query) == {"v", "room", "key", "root", "invite", "map"}
            and all(len(items) == 1 for items in query.values())
            and query["v"] == [str(SECURITY_VERSION)]
        )
        if (
            parsed.scheme != "pyteg"
            or parsed.netloc not in {"host", "peer"}
            or parsed.fragment
            or not valid_query
        ):
            raise ValueError("Invitación de Pyteg inválida")
        host, separator, port = parsed.path.removeprefix("/").rpartition(":")
        if not separator or not port.isdecimal():
            raise ValueError("Destino de invitación inválido")
        return cls(
            parsed.netloc,
            host,
            int(port),
            query["room"][0],
            query["key"][0],
            query["invite"][0],
            query["root"][0],
            query["map"][0],
        )


@dataclass
class RoomAccess:
    """Autorización de ingreso distinta de las claves privadas de los jugadores."""

    session_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    token: str = field(default_factory=lambda: secrets.token_hex(32), repr=False)

    def admits(self, request: dict[str, Any]) -> bool:
        """Exige la invitación antes de revelar el estado de una sala."""
        return (
            request.get("session_id") == self.session_id
            and isinstance(request.get("invite"), str)
            and secrets.compare_digest(self.token, request["invite"])
        )

    def invitation(
        self,
        mode: str,
        host: str,
        port: int,
        identity: Identity,
        theme: str = "classic",
    ) -> Invitation:
        """Fija la identidad del participante que recibirá el primer contacto."""
        return Invitation(
            mode,
            host,
            port,
            self.session_id,
            identity.public_key,
            self.token,
            theme=theme,
        )
