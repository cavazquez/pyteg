"""Copias compactas en la red con expansión estrictamente acotada."""

from __future__ import annotations

import base64
import binascii
import json
import zlib
from typing import Any

from pyteg.persistence.archive import MAX_ARCHIVE_BYTES, canonical_bytes


def encode_envelope(envelope: dict[str, Any]) -> dict[str, Any]:
    """Comprime el memento conservando los metadatos públicos del transporte.

    Returns:
        Sobre de red con el mismo contenido al decodificarlo.

    """
    raw = canonical_bytes(envelope["checkpoint"])
    return {
        **envelope,
        "checkpoint": {
            "encoding": "zlib-json",
            "bytes": len(raw),
            "data": base64.b64encode(zlib.compress(raw)).decode("ascii"),
        },
    }


def decode_envelope(envelope: dict[str, Any]) -> dict[str, Any]:
    """Acepta mementos normales o expande una copia sin superar su límite.

    Returns:
        Sobre con checkpoint JSON validable por el protocolo.

    Raises:
        ValueError: Si la copia comprimida está dañada o excede el límite.

    """
    checkpoint = envelope.get("checkpoint")
    if not isinstance(checkpoint, dict) or checkpoint.get("encoding") is None:
        return envelope
    if (
        checkpoint.get("encoding") != "zlib-json"
        or type(checkpoint.get("bytes")) is not int
        or not 0 < checkpoint["bytes"] <= MAX_ARCHIVE_BYTES
    ):
        msg = "Copia comprimida incompatible o demasiado grande"
        raise ValueError(msg)
    try:
        compressed = base64.b64decode(checkpoint["data"], validate=True)
        decoder = zlib.decompressobj()
        raw = decoder.decompress(compressed, checkpoint["bytes"] + 1)
        if (
            len(raw) != checkpoint["bytes"]
            or not decoder.eof
            or decoder.unused_data
            or decoder.unconsumed_tail
        ):
            msg = "Copia comprimida incompleta o demasiado grande"
            raise ValueError(msg)  # noqa: TRY301 -- validación de la expansión.
        data = json.loads(raw)
        if not isinstance(data, dict):
            msg = "La copia comprimida no es un memento"
            raise ValueError(msg)  # noqa: TRY004, TRY301 -- formato de archivo.
    except (
        ValueError,
        TypeError,
        KeyError,
        zlib.error,
        binascii.Error,
        RecursionError,
    ) as error:
        msg = "Copia comprimida inválida"
        raise ValueError(msg) from error
    return {**envelope, "checkpoint": data}
