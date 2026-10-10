"""Identidades individuales y firmas con claves privadas locales."""

# ruff: noqa: DOC201, DOC501, TRY003, EM101

from __future__ import annotations

import hashlib
from copy import deepcopy
from dataclasses import dataclass, field

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)

from pyteg.persistence.archive import canonical_bytes

_MAX_IDENTITIES = 1024


def hex_bytes(value: object, size: int) -> bytes:
    """Acepta solamente una codificación hexadecimal canónica y acotada."""
    if not isinstance(value, str) or len(value) != size * 2:
        raise ValueError("Clave o firma de red inválida")
    raw = bytes.fromhex(value)
    if len(raw) != size or raw.hex() != value:
        raise ValueError("Clave o firma de red inválida")
    return raw


def public_key(value: object) -> str:
    """Valida una clave pública Ed25519 recibida por la red."""
    return hex_bytes(value, 32).hex()


def verify(key: str, value: object, signature: object) -> bool:
    """Verifica autoría sin disponer de la clave privada del participante."""
    try:
        Ed25519PublicKey.from_public_bytes(hex_bytes(key, 32)).verify(
            hex_bytes(signature, 64), canonical_bytes(value)
        )
    except InvalidSignature, ValueError, TypeError:
        return False
    return True


@dataclass(frozen=True)
class Identity:
    """Clave individual; su exportación privada nunca forma parte de una réplica."""

    key: Ed25519PrivateKey = field(
        default_factory=Ed25519PrivateKey.generate, repr=False
    )

    @property
    def public_key(self) -> str:
        """Obtiene la identidad que pueden conservar los otros jugadores."""
        return self.key.public_key().public_bytes_raw().hex()

    def export_private(self) -> str:
        """Exporta sólo para el guardado local de esta identidad."""
        return self.key.private_bytes_raw().hex()

    @classmethod
    def restore(cls, secret: object) -> Identity:
        """Recupera la misma identidad al reabrir su guardado local."""
        return cls(Ed25519PrivateKey.from_private_bytes(hex_bytes(secret, 32)))

    def sign(self, value: object) -> str:
        """Firma un valor JSON canónico con la clave de este participante."""
        return self.key.sign(canonical_bytes(value)).hex()


def engine_token(key: str) -> str:
    """Identificador interno del motor; nunca autentica una conexión de red."""
    return hashlib.sha256(
        canonical_bytes({"engine_identity": public_key(key)})
    ).hexdigest()


def validate_identities(value: object) -> dict[str, str]:
    """Valida el registro histórico, que conserva sólo claves públicas."""
    if not isinstance(value, dict) or not 1 <= len(value) <= _MAX_IDENTITIES:
        raise ValueError("Registro de identidades inválido")
    for uid, key in value.items():
        if (
            not isinstance(uid, str)
            or not uid.isdecimal()
            or str(int(uid)) != uid
            or not 1 <= int(uid) <= 2**31
        ):
            raise ValueError("Identificador criptográfico inválido")
        public_key(key)
    return deepcopy(value)
