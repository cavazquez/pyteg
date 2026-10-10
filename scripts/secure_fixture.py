"""Conexiones seguras compartidas por los recorridos Qt y el simulador."""

from __future__ import annotations

import threading
from queue import Empty, Queue
from typing import TYPE_CHECKING

from pyteg.network.security import (
    Invitation,
    connect_tls,
    proof,
    receive_json,
    send_json,
)

if TYPE_CHECKING:
    import ssl
    import subprocess

    from pyteg.network.identity import Identity


def server_invitation(process: subprocess.Popen[str], timeout: float) -> Invitation:
    """Lee el enlace inicial sin mostrar sus credenciales en la evidencia.

    Returns:
        Invitación emitida por el proceso servidor local.

    Raises:
        RuntimeError: Si el proceso no produce una invitación válida a tiempo.

    """
    replies: Queue[str] = Queue()

    def read() -> None:
        if process.stdout is not None:
            for line in process.stdout:
                if "pyteg://" in line:
                    replies.put("pyteg://" + line.partition("pyteg://")[2].strip())
                    return
        replies.put("")

    threading.Thread(target=read, name="smoke-invitation", daemon=True).start()
    try:
        value = replies.get(timeout=timeout)
    except Empty as error:
        msg = "El servidor no entregó una invitación dentro del plazo"
        raise RuntimeError(msg) from error
    if not value:
        msg = "El servidor terminó antes de entregar la invitación"
        raise RuntimeError(msg)
    return Invitation.parse(value)


def player_channel(
    invitation: Invitation, identity: Identity, user_id: int | None, timeout: float
) -> tuple[ssl.SSLSocket, str]:
    """Autentica un cliente de prueba antes de enviar comandos de juego.

    Returns:
        Socket TLS y desafío usado para firmar cada comando del canal.

    Raises:
        ValueError: Si la sala rechaza la identidad.

    """
    connection = connect_tls(
        (invitation.host, invitation.port), invitation.public_key, timeout
    )
    try:
        greeting = receive_json(connection, limit=4096)
        send_json(
            connection,
            proof(
                identity,
                greeting,
                {
                    "message": "connect",
                    "session_id": invitation.session_id,
                    "invite": invitation.token,
                    "user_id": user_id,
                },
            ),
        )
        if receive_json(connection, limit=4096).get("accepted") is not True:
            msg = "La sala rechazó la identidad del cliente de prueba"
            raise ValueError(msg)  # noqa: TRY301 -- el socket debe cerrarse ante el rechazo.
        connection.settimeout(timeout)
    except Exception:
        connection.close()
        raise
    return connection, greeting["nonce"]
