# ruff: noqa: SLF001
"""Regresiones de la copia privada y la promoción del anfitrión."""

from __future__ import annotations

import json
import random
import unittest
from copy import deepcopy
from typing import Any, cast
from unittest.mock import MagicMock, patch

from pyteg.core.partida.pactos import Pact
from pyteg.core.turnos.timer import NullTurnTimer
from pyteg.protocol_validation import MessageValidationError, validate_client_event
from pyteg.server.app import Server
from pyteg.server.conexion.cliente import Client
from pyteg.server.hosting.checkpoint import export_checkpoint, restore_checkpoint
from pyteg.server.hosting.data import capture, pack, restore, unpack
from pyteg.server.hosting.replication import HostReplication
from pyteg.server.hosting.runtime import HostRuntime
from pyteg.server.hosting.sessions import finish_migration


class _HostFixture(unittest.TestCase):
    """Crea jugadores reales con conexiones inertes para las regresiones."""

    def _server(self, theme: str = "classic", profile: str = "classic") -> Server:
        server = Server(theme, rules_profile=profile)
        self.addCleanup(server.detener)
        for user_id in range(1, 4):
            client = Client(
                user_id,
                MagicMock(),
                server,
                f"Jugador {user_id}",
                soy_admin=False,
                reconnect_token=f"test-token-{user_id}",
            )
            self.assertTrue(server.registrar_cliente(user_id, client))
        return server

    def _start(self, server: Server) -> None:
        server.set_paises_para_victoria(0)
        server.set_objetivos_secretos(activados=True)
        server.estado.esperar_jugadores()
        with patch(
            "pyteg.server.juego.coordinator.TurnoTimer", return_value=NullTurnTimer()
        ):
            server._command_executor.call_serialized(server.empezar_partida)

    def _copy(self, server: Server) -> dict[str, Any]:
        return cast(
            "dict[str, Any]",
            server._command_executor.call_serialized(lambda: export_checkpoint(server)),
        )


class HostCheckpointTests(_HostFixture):
    """Comprueba todos los módulos de ambos mapas sin serializar conexiones."""

    def test_round_trip_all_maps_and_profiles(self) -> None:
        """Geografía y reglas se conservan en las cuatro combinaciones."""
        for theme in ("classic", "revancha"):
            for profile in ("classic", "revancha"):
                with self.subTest(theme=theme, profile=profile):
                    original = self._server(theme, profile)
                    self._start(original)
                    game = original.game
                    if game is None:
                        self.fail("No se creó la partida")
                    for _round_step in range(6):
                        original._command_executor.call_serialized(game.finalizar_turno)
                    country = original.mapa.paises()[0]
                    original.mapa._mapa[country].unidades = 11
                    original.mapa._mapa[country].misiles = 2
                    original.mapa.crear_condominio(country, {1: 6, 2: 5})
                    original.mazo.asignar_tarjeta(1)
                    game._card_manager._cant_canjes[1] = 3
                    game._card_manager._jugadores_reclamaron[2] = (
                        game._turn_manager.clave_turno()
                    )
                    game.pactos()._pactos["pacto-test"] = Pact(
                        "pacto-test", "no_agresion", (1, 2), 1, 5, estado="activo"
                    )
                    original.dame_clientes()[0].remember_command_result(
                        "applied",
                        {"command_id": "applied", "accepted": True, "revision": 7},
                        {"mensaje": "agregar_unidad", "pais": country},
                    )
                    checkpoint = json.loads(json.dumps(self._copy(original)))
                    resumed = Server(theme)
                    self.addCleanup(resumed.detener)
                    resumed.migration_sessions = restore_checkpoint(resumed, checkpoint)
                    actual = self._copy(resumed)
                    actual["connected"] = checkpoint["connected"]
                    self.assertEqual(actual, checkpoint)

    def test_lobby_round_trip_and_authenticated_reconnection(self) -> None:
        """La recuperación de un lobby mantiene usuario, administrador y color."""
        original = self._server()
        checkpoint = self._copy(original)
        resumed = Server()
        self.addCleanup(resumed.detener)
        resumed.migration_sessions = restore_checkpoint(resumed, checkpoint)
        incoming = Client(10, MagicMock(), resumed, "Temporal", soy_admin=False)
        self.assertTrue(resumed.registrar_reconexion_pendiente(10, incoming))
        self.assertFalse(resumed.reconectar_cliente(incoming, 1, "invalid"))
        self.assertTrue(resumed.reconectar_cliente(incoming, 1, "test-token-1"))
        self.assertEqual(incoming.userid(), 1)
        self.assertTrue(incoming.es_admin())
        self.assertEqual(incoming.username(), "Jugador 1")
        self.assertEqual(
            incoming.color_actual(), original.dame_clientes()[0].color_actual()
        )

    def test_reconnecting_keeps_pending_turn_and_command_cache(self) -> None:
        """Cambiar el socket no desplaza el turno ni permite repetir una acción."""
        original = self._server()
        self._start(original)
        player = original.dame_clientes()[0]
        player.remember_command_result(
            "already-applied",
            {
                "command_id": "already-applied",
                "accepted": True,
                "revision": original.state_revision(),
            },
            {"mensaje": "finalizar_turno"},
        )
        resumed = Server()
        self.addCleanup(resumed.detener)
        resumed.migration_sessions = restore_checkpoint(resumed, self._copy(original))
        game = resumed.game
        if game is None:
            self.fail("No se recuperó la partida")
        turn_before = game.turno_actual().jugador_actual()
        incoming = Client(10, MagicMock(), resumed, "Temporal", soy_admin=False)
        self.assertTrue(resumed.registrar_reconexion_pendiente(10, incoming))
        self.assertTrue(resumed.reconectar_cliente(incoming, 1, "test-token-1"))
        self.assertEqual(game.turno_actual().jugador_actual(), turn_before)
        self.assertEqual(
            incoming.command_result("already-applied"),
            player.command_result("already-applied"),
        )
        self.assertEqual(game.lista_jugadores_orden_turno(), [1, 2, 3])

    def test_seeded_random_state_survives(self) -> None:
        """Los dados de una simulación continúan desde la misma secuencia."""
        original = self._server()
        self._start(original)
        game = original.game
        if game is None:
            self.fail("No se creó la partida")
        game._dice_rng = random.Random(77)  # noqa: S311 -- dados reproducibles.
        game._dice_rng.randint(1, 6)
        resumed = Server()
        self.addCleanup(resumed.detener)
        restore_checkpoint(resumed, self._copy(original))
        recovered_game = resumed.game
        if recovered_game is None or recovered_game._dice_rng is None:
            self.fail("No se recuperó el generador de dados")
        self.assertEqual(
            [game._dice_rng.randint(1, 6) for _roll in range(12)],
            [recovered_game._dice_rng.randint(1, 6) for _roll in range(12)],
        )

    def test_situation_deck_and_dice_keep_the_same_generator(self) -> None:
        """El mazo y Crisis conservan su generador compartido en las simulaciones."""
        original = self._server("revancha", "revancha")
        original._game_coordinator._situation_rng = random.Random(83)  # noqa: S311 -- simulación.
        self._start(original)
        resumed = Server("revancha")
        self.addCleanup(resumed.detener)
        restore_checkpoint(resumed, self._copy(original))
        game = resumed.game
        if game is None:
            self.fail("No se recuperó la partida")
        self.assertIs(
            game._situation_runtime._deck._rng, resumed._game_coordinator._situation_rng
        )
        self.assertIs(
            getattr(game._situation_runtime._dice_source, "_rng"),  # noqa: B009 -- protocolo DiceSource.
            resumed._game_coordinator._situation_rng,
        )

    def test_turn_clock_resumes_remaining_seconds(self) -> None:
        """Una migración no regala un turno entero si el jugador sigue en turno."""
        from pyteg.core.turnos.timer import TurnoTimer  # noqa: PLC0415

        server = MagicMock()
        server.turno_snapshot.return_value = (2, 1)
        timer = TurnoTimer(server, segundos_por_turno=20, resume_seconds=7)
        self.assertEqual(timer.remaining_seconds(), 7)
        timer._resume_seconds = None
        timer._countdown_snapshot = (2, 1)
        timer._remaining = 6
        self.assertEqual(timer.remaining_seconds(), 6)
        server.turno_snapshot.return_value = (3, 2)
        self.assertEqual(timer.remaining_seconds(), 20)

    def test_reject_incompatible_or_incomplete_copy(self) -> None:
        """No inicia un motor sobre otro mapa ni una copia parcial."""
        original = self._server()
        checkpoint = self._copy(original)
        for field, value in (("version", 99), ("map_hash", "wrong"), ("countries", {})):
            with self.subTest(field=field):
                invalid = deepcopy(checkpoint)
                invalid[field] = value
                resumed = Server()
                self.addCleanup(resumed.detener)
                with self.assertRaises(ValueError):
                    restore_checkpoint(resumed, invalid)

    def test_data_codec_rejects_executable_types_and_extra_fields(self) -> None:
        """El contrato no carga clases, funciones ni atributos enviados por el peer."""
        self.assertEqual(
            unpack(json.loads(json.dumps(pack({2: ("x", {1, 3})})))), {2: ("x", {1, 3})}
        )
        with self.assertRaises(ValueError):
            unpack({"kind": "os.system", "items": ["anything"]})
        with self.assertRaises(ValueError):
            pack(lambda: None)
        obj = MagicMock(value=1)
        with self.assertRaises(ValueError):
            restore(obj, {"value": 1, "other": 2}, ("value",))
        self.assertEqual(capture(obj, ("value",)), {"value": 1})

    def test_public_snapshot_excludes_private_recovery_data(self) -> None:
        """Cartas, objetivos y tokens no se incorporan al snapshot visible."""
        server = self._server()
        self._start(server)
        serialized = json.dumps(server.public_snapshot())
        self.assertNotIn("test-token", serialized)
        self.assertNotIn("objetivos_asignados", serialized)
        self.assertNotIn("cache", serialized)

    def test_recovery_events_validate_metadata(self) -> None:
        """La validación de protocolo rechaza puertos e identidades inválidos."""
        server = self._server()
        event: dict[str, Any] = {
            "mensaje": "host_checkpoint",
            "session_id": "test-session",
            "epoch": 0,
            "owner_id": 1,
            "sequence": 1,
            "peers": [{"userid": 1, "host": "127.0.0.1", "port": 65432}],
            "checkpoint": self._copy(server),
        }
        self.assertEqual(validate_client_event(event), event)
        event["peers"][0]["port"] = 0
        with self.assertRaises(MessageValidationError):
            validate_client_event(event)

    def test_only_negotiated_candidates_receive_private_copies(self) -> None:
        """Las copias completas requieren handshake y capacidad de migración."""
        server = self._server()
        client = server.dame_clientes()[0]
        replication = HostReplication(server, lambda _copy: None)
        replication.register(client, 65432)
        self.assertEqual(replication.peers, {})
        client.marcar_handshake(True)  # noqa: FBT003
        replication.register(client, 65432)
        self.assertEqual(replication.peers, {})
        client.configurar_migracion(enabled=True)
        replication.register(client, 65432)
        self.assertEqual(list(replication.peers), [client.userid()])


class HostRuntimeTests(_HostFixture):
    """Comprueba la autoridad y autenticación del servicio TCP de recuperación."""

    def _runtime_copy(self) -> tuple[HostRuntime, dict[str, Any]]:
        original = self._server()
        runtime = HostRuntime(bind_host="127.0.0.1")
        self.addCleanup(runtime.close)
        envelope = {
            "mensaje": "host_checkpoint",
            "session_id": "session-test",
            "epoch": 0,
            "owner_id": 1,
            "sequence": 1,
            "peers": [{"userid": 2, "host": "127.0.0.1", "port": runtime.control_port}],
            "checkpoint": self._copy(original),
        }
        self.assertTrue(runtime.store_checkpoint(envelope, user_id=2))
        request = {
            "session_id": "session-test",
            "epoch": 0,
            "user_id": 3,
            "token": "test-token-3",
        }
        return runtime, request

    def test_recovery_is_authenticated_and_promotion_is_idempotent(self) -> None:
        """Varios clientes obtienen la misma autoridad, puerto y época."""
        runtime, request = self._runtime_copy()
        with self.assertRaises(ValueError):
            runtime.recover({**request, "token": "invalid"})
        self.assertIsNone(runtime.server)
        first = runtime.recover(request)
        second = runtime.recover(request)
        self.assertEqual(first, second)
        self.assertEqual(first["epoch"], 1)
        self.assertEqual(first["owner_id"], 2)
        server = cast("Server", runtime.server)
        self.assertEqual(server._admin_user_id, 1)

    def test_connected_standby_does_not_create_another_server(self) -> None:
        """Una caída de un cliente conserva al anfitrión que los demás aún ven."""
        runtime, request = self._runtime_copy()
        runtime.primary_connection(("127.0.0.1", 65432))
        self.assertEqual(runtime.recover(request)["mensaje"], "host_alive")
        self.assertIsNone(runtime.server)

    def test_isolated_candidate_checks_another_connected_player(self) -> None:
        """Perder sólo una conexión no crea dos partidas en la misma red."""
        runtime, request = self._runtime_copy()
        other = HostRuntime(bind_host="127.0.0.1")
        self.addCleanup(other.close)
        envelope = runtime.latest_checkpoint()
        if envelope is None:
            self.fail("No se guardó la copia")
        envelope["sequence"] += 1
        envelope["peers"].append({
            "userid": 3,
            "host": "127.0.0.1",
            "port": other.control_port,
        })
        runtime.store_checkpoint(envelope, user_id=2)
        other.store_checkpoint(envelope, user_id=3)
        other.primary_connection(("127.0.0.1", 65432))
        response = runtime.recover(request)
        self.assertEqual(response["mensaje"], "host_alive")
        self.assertEqual(response["port"], 65432)
        self.assertIsNone(runtime.server)
        self.assertIsNone(other.server)

    def test_status_requires_authentication_and_never_promotes(self) -> None:
        """Una consulta válida no convierte a un suplente en anfitrión."""
        runtime, request = self._runtime_copy()
        with self.assertRaises(ValueError):
            runtime.status({**request, "token": "invalid"})
        self.assertEqual(runtime.status(request)["mensaje"], "host_standby")
        self.assertIsNone(runtime.server)

    def test_rejects_old_epochs_and_wrong_sessions(self) -> None:
        """Una solicitud obsoleta no reemplaza a la autoridad actual."""
        runtime, request = self._runtime_copy()
        for invalid in (
            {**request, "epoch": -1},
            {**request, "epoch": 5},
            {**request, "session_id": "wrong"},
        ):
            with self.assertRaises(ValueError):
                runtime.recover(invalid)

    def test_ignores_old_or_foreign_copies(self) -> None:
        """Copias repetidas y de otra sala no reemplazan el punto vigente."""
        runtime, _request = self._runtime_copy()
        envelope = runtime.latest_checkpoint()
        if envelope is None:
            self.fail("No se guardó la copia")
        self.assertFalse(runtime.store_checkpoint(envelope))
        self.assertFalse(
            runtime.store_checkpoint({**envelope, "session_id": "wrong", "sequence": 2})
        )

    def test_expired_lobby_identity_cannot_enter_next_game(self) -> None:
        """El lobby libera colores y descarta a quienes no recuperan su sesión."""
        runtime, request = self._runtime_copy()
        runtime.recover(request)
        server = cast("Server", runtime.server)
        server._command_executor.call_serialized(lambda: finish_migration(server, None))
        self.assertEqual(server.migration_sessions, {})
        self.assertFalse(server.host_migrating)
