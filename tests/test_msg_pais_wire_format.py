"""Wire format de MsgPais (userid int | null)."""

from __future__ import annotations

import json
import unittest

from pyteg.server.msg.map_turn import MsgPais


class MsgPaisWireFormatTests(unittest.TestCase):
    """Documenta el JSON serializado de MsgPais."""

    def test_userid_int_en_wire(self) -> None:
        """El campo JSON `userid` debe ser número (int), no string."""
        raw = MsgPais("Uruguay", 7, 3).to_json()
        data = json.loads(raw)
        self.assertEqual(data["mensaje"], "pais")
        self.assertEqual(data["pais"], "Uruguay")
        self.assertEqual(data["unidades"], 3)
        self.assertIsInstance(data["userid"], int)
        self.assertEqual(data["userid"], 7)

    def test_sin_dueno_userid_null(self) -> None:
        """Sin propietario, userid puede ser null en JSON."""
        raw = MsgPais("Antártida", None, 0).to_json()
        data = json.loads(raw)
        self.assertIsNone(data["userid"])


if __name__ == "__main__":
    unittest.main()
