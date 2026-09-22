"""Pruebas unitarias del contrato JSON de la conexión TCP."""

from __future__ import annotations

import unittest

from pyteg.protocol_validation import (
    MessageValidationError,
    validate_client_event,
    validate_server_command,
)


class TestServerCommandValidation(unittest.TestCase):
    """Valida los mensajes que llegan desde un cliente al servidor."""

    def test_rejects_scalar_json_payloads(self) -> None:
        """Los escalares JSON no pueden llegar al constructor de tareas."""
        scalar_payloads: tuple[object, ...] = (None, [], 7, "chat")
        for payload in scalar_payloads:
            with self.subTest(payload=payload):
                with self.assertRaises(MessageValidationError) as raised:
                    validate_server_command(payload)
                self.assertEqual(raised.exception.code, "invalid_payload")

    def test_rejects_missing_wrong_and_unknown_commands(self) -> None:
        """Los campos obligatorios, sus tipos y el discriminador son estrictos."""
        invalid_cases = [
            ({"mensaje": "set_username"}, "missing_field"),
            (
                {
                    "mensaje": "agregar_unidad",
                    "pais": "Argentina",
                    "tipo_unidad": "infanteria",
                    "cantidad": True,
                },
                "invalid_field",
            ),
            (
                {
                    "mensaje": "mover_unidad",
                    "origen": "Argentina",
                    "destino": "Uruguay",
                    "cantidad": -1,
                },
                "invalid_field",
            ),
            ({"mensaje": "noexiste"}, "unknown_message"),
        ]

        for payload, expected_code in invalid_cases:
            with self.subTest(payload=payload):
                with self.assertRaises(MessageValidationError) as raised:
                    validate_server_command(payload)
                self.assertEqual(raised.exception.code, expected_code)

    def test_accepts_attack_without_optional_dice_count(self) -> None:
        """El cliente puede pedir al servidor que elija los dados del ataque."""
        payload = {"mensaje": "atacar", "origen": "Argentina", "destino": "Chile"}

        self.assertEqual(validate_server_command(payload), payload)

    def test_accepts_heartbeat_pong(self) -> None:
        """El servidor acepta la respuesta opaca de un cliente vivo."""
        payload = {"mensaje": "pong", "heartbeat_id": "probe-1"}

        self.assertEqual(validate_server_command(payload), payload)

    def test_rejects_every_invalid_move_amount(self) -> None:
        """El contrato TCP exige un entero positivo y no acepta bool como int."""
        invalid_amounts: tuple[object, ...] = (0, -1, True, 1.5, "1", None)
        for amount in invalid_amounts:
            with self.subTest(amount=amount):
                payload = {
                    "mensaje": "mover_unidad",
                    "origen": "Argentina",
                    "destino": "Uruguay",
                    "cantidad": amount,
                }
                with self.assertRaises(MessageValidationError) as raised:
                    validate_server_command(payload)
                self.assertEqual(raised.exception.code, "invalid_field")


class TestClientEventValidation(unittest.TestCase):
    """Valida los eventos que un servidor entrega a un cliente Qt."""

    def test_accepts_complete_forward_compatible_snapshot(self) -> None:
        """El snapshot exige el contrato base y tolera campos futuros."""
        payload = {
            "mensaje": "snapshot",
            "snapshot_version": 1,
            "revision": 4,
            "estado": "JUGANDO",
            "theme": "classic",
            "map_hash": "hash",
            "configuracion": {
                "segundos_por_turno": 20,
                "paises_para_victoria": 30,
                "objetivos_secretos": False,
                "misiles_habilitados": True,
                "regla_futura": "ignorada",
            },
            "players": [
                {
                    "userid": 1,
                    "username": "Admin",
                    "color": {"r": 255, "g": 0, "b": 0},
                    "admin": True,
                    "connected": True,
                    "eliminated": False,
                    "campo_futuro": 1,
                }
            ],
            "countries": {
                "Argentina": {
                    "userid": 1,
                    "unidades": 3,
                    "misiles": 2,
                    "dato_futuro": True,
                }
            },
            "fase": "colocacion",
            "turno": {"num_turno": 0, "num_ronda": 1, "jugador_id": 1},
            "refuerzos_pendientes": 5,
            "campo_futuro": {"version": 2},
        }

        self.assertEqual(validate_client_event(payload), payload)

    def test_rejects_invalid_or_unknown_events(self) -> None:
        """Un peer defectuoso no construye tareas con payloads inseguros."""
        invalid_cases = [
            ([], "invalid_payload"),
            ({"mensaje": "error", "error_type": "invalid_json"}, "missing_field"),
            ({"mensaje": "desconocido"}, "unknown_message"),
        ]

        for payload, expected_code in invalid_cases:
            with self.subTest(payload=payload):
                with self.assertRaises(MessageValidationError) as raised:
                    validate_client_event(payload)
                self.assertEqual(raised.exception.code, expected_code)

    def test_accepts_structured_connection_rejection(self) -> None:
        """El rechazo de una partida en curso usa el evento error normalizado."""
        payload = {
            "mensaje": "error",
            "error_type": "game_in_progress",
            "message": "El juego ya está en progreso.",
        }

        self.assertEqual(validate_client_event(payload), payload)

    def test_accepts_heartbeat_ping(self) -> None:
        """El cliente acepta un ping sin proyectarlo como estado de partida."""
        payload = {"mensaje": "ping", "heartbeat_id": "probe-1"}

        self.assertEqual(validate_client_event(payload), payload)

    def test_accepts_battle_result_with_public_participants(self) -> None:
        """El resultado real incluye países además de la lista de pérdidas."""
        payload = {
            "mensaje": "resultado_batalla",
            "origen": "A",
            "destino": "B",
            "atacante_id": 1,
            "defensor_id": 2,
            "atacante": "A",
            "defensor": "B",
            "dados_atacante": [6],
            "dados_defensor": [1],
            "resultado": {
                "atacante": "1",
                "defensor": "2",
                "restar": ["2"],
            },
            "conquistado": False,
        }

        self.assertEqual(validate_client_event(payload), payload)
