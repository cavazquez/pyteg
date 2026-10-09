"""Copias TCP compactas con límites de expansión y datos JSON inertes."""

from __future__ import annotations

import base64
import unittest
import zlib
from copy import deepcopy

from pyteg.persistence.archive import MAX_ARCHIVE_BYTES, canonical_bytes
from pyteg.persistence.wire import decode_envelope, encode_envelope


class CheckpointWireTests(unittest.TestCase):
    """La compresión conserva el memento sin ampliar los límites del protocolo."""

    def test_round_trip_large_history_and_legacy_envelope(self) -> None:
        """Un historial que supera 1 MiB cabe en una trama comprimida."""
        envelope = {
            "sequence": 10,
            "checkpoint": {"historial": ["país con misil"] * 100000},
        }
        encoded = encode_envelope(envelope)
        self.assertGreater(len(canonical_bytes(envelope)), 1024 * 1024)
        self.assertLess(len(canonical_bytes(encoded)), 1024 * 1024)
        self.assertEqual(decode_envelope(encoded), envelope)
        self.assertEqual(decode_envelope(envelope), envelope)

    def test_rejects_invalid_encoding_base64_and_wrong_size(self) -> None:
        """Los metadatos dañados no se aceptan como un estado completo."""
        original = encode_envelope({"checkpoint": {"dato": 1}})
        for changes in (
            {"encoding": "pickle"},
            {"data": "not base64!"},
            {"bytes": True},
            {"bytes": 2},
            {"bytes": MAX_ARCHIVE_BYTES + 1},
        ):
            with self.subTest(changes=changes):
                encoded = deepcopy(original)
                encoded["checkpoint"].update(changes)
                with self.assertRaises(ValueError):
                    decode_envelope(encoded)

    def test_rejects_truncated_or_trailing_stream(self) -> None:
        """La trama debe contener exactamente un flujo comprimido completo."""
        encoded = encode_envelope({"checkpoint": {"dato": 1}})
        compressed = base64.b64decode(encoded["checkpoint"]["data"])
        for bad in (compressed[:-1], compressed + b"extra", compressed + compressed):
            with self.subTest(length=len(bad)):
                encoded["checkpoint"]["data"] = base64.b64encode(bad).decode()
                with self.assertRaises(ValueError):
                    decode_envelope(encoded)

    def test_expansion_is_bounded_by_declared_size(self) -> None:
        """Un flujo pequeño no puede expandirse más que su tamaño declarado."""
        compressed = zlib.compress(b" " * (1024 * 1024))
        with self.assertRaises(ValueError):
            decode_envelope({
                "checkpoint": {
                    "encoding": "zlib-json",
                    "bytes": 8,
                    "data": base64.b64encode(compressed).decode(),
                }
            })

    def test_rejects_non_object_json(self) -> None:
        """Sólo los objetos JSON pueden representar el estado del motor."""
        raw = b"[]"
        with self.assertRaises(ValueError):
            decode_envelope({
                "checkpoint": {
                    "encoding": "zlib-json",
                    "bytes": len(raw),
                    "data": base64.b64encode(zlib.compress(raw)).decode(),
                }
            })
