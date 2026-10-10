"""Autenticación del canal de juego y autoría de sus comandos."""

# ruff: noqa: DOC201, DOC501, TRY003, EM101

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from pyteg.network.identity import Identity, public_key, verify
from pyteg.network.security import (
    RoomAccess,
    TlsCredentials,
    authenticate,
    challenge,
    receive_json,
    send_json,
)

if TYPE_CHECKING:
    import socket
    import ssl
    from collections.abc import Callable


def signed_command(
    identity: Identity, session: str, nonce: str, sequence: int, command: dict[str, Any]
) -> dict[str, Any]:
    """Firma un comando para una única sala, conexión y posición."""
    content = {
        "session": session,
        "nonce": nonce,
        "sequence": sequence,
        "command": command,
    }
    return {
        "sequence": sequence,
        "command": command,
        "signature": identity.sign(content),
    }


@dataclass
class GameChannel:
    """Identidad ya comprobada y contador de comandos de una conexión TLS."""

    public_key: str
    session_id: str
    nonce: str
    sequence: int = 0

    def unwrap(self, packet: object) -> dict[str, Any]:
        """Rechaza firmas inválidas y comandos repetidos antes de validarlos."""
        if not isinstance(packet, dict) or set(packet) != {
            "sequence",
            "command",
            "signature",
        }:
            raise ValueError("El comando debe incluir la firma de su jugador")
        sequence, command = packet["sequence"], packet["command"]
        if (
            type(sequence) is not int
            or sequence != self.sequence + 1
            or not isinstance(command, dict)
        ):
            raise ValueError("La secuencia del comando no corresponde a esta conexión")
        content = {
            "session": self.session_id,
            "nonce": self.nonce,
            "sequence": sequence,
            "command": command,
        }
        if not verify(self.public_key, content, packet["signature"]):
            raise ValueError("La firma del comando no corresponde a su jugador")
        self.sequence = sequence
        return command


class GameSecurity:
    """Admisión previa al registro de un jugador o su reconexión."""

    def __init__(
        self,
        credentials: TlsCredentials,
        access: RoomAccess,
        keys: Callable[[], dict[int, str]],
    ) -> None:
        """Usa el registro público del motor como autoridad de identidades."""
        self.credentials, self.access, self._keys = credentials, access, keys

    def _authorize(self, request: dict[str, Any], key: str) -> None:
        if (
            set(request) != {"message", "session_id", "invite", "user_id"}
            or request["message"] != "connect"
            or request["session_id"] != self.access.session_id
        ):
            raise ValueError("La conexión no corresponde a esta sala")
        user_id = request["user_id"]
        if user_id is not None:
            if type(user_id) is not int or self._keys().get(user_id) != key:
                raise ValueError(
                    "La reconexión requiere la clave privada de su jugador"
                )
        elif not self.access.admits(request):
            raise ValueError("La sala requiere una invitación válida")

    def accept(self, raw: socket.socket) -> tuple[ssl.SSLSocket, GameChannel]:
        """Cifra y autentica antes de asignar IDs o enviar estado de la partida."""
        connection = self.credentials.accept(raw)
        try:
            greeting = challenge()
            send_json(connection, greeting)
            request, key = authenticate(greeting, receive_json(connection, limit=4096))
            self._authorize(request, key)
            public_key(key)
            channel = GameChannel(key, self.access.session_id, greeting["nonce"])
            send_json(connection, {"security": greeting["security"], "accepted": True})
            connection.settimeout(None)
        except Exception:
            connection.close()
            raise
        return connection, channel
