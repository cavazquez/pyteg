# ruff: noqa: DOC201

"""Pruebas de pactos, bloqueos y países en condominio."""

from __future__ import annotations

import unittest
from dataclasses import dataclass, field

from pyteg.core.partida.pactos import NoPactManager, PactManager
from pyteg.protocol_validation import MessageValidationError, validate_server_command
from pyteg.server.juego.mapa import Mapa


def build_map() -> dict[str, list[object]]:
    """Construye un mapa pequeño con una frontera y un país bloqueable."""
    return {
        "Origen": [3, "A", 1, ["Objetivo"]],
        "Objetivo": [2, "A", 2, ["Origen", "Flanco1", "Flanco2"]],
        "Flanco1": [2, "A", 3, ["Objetivo"]],
        "Flanco2": [2, "A", 3, ["Objetivo"]],
        "Reserva": [1, "A", 2, []],
    }


@dataclass
class ReinforcementPool:
    """Pool mínimo que usa el mismo contrato de consumo de los turnos."""

    units: dict[str, int] = field(
        default_factory=lambda: {"infanteria": 3, "A": 4, "B": 2}
    )

    def jugador_actual(self) -> int:
        """Devuelve el jugador que recibe refuerzos."""
        return 2

    def unidades_por_tipo(self) -> dict[str, int]:
        """Entrega una copia de sus unidades disponibles."""
        return dict(self.units)

    def usar_unidad(self) -> None:
        """Consume una unidad general."""
        self.units["infanteria"] -= 1

    def usar_unidad_por_continente(self, continent: str) -> None:
        """Consume una unidad del continente indicado."""
        self.units[continent] -= 1


class RevanchaPactTests(unittest.TestCase):
    """Verifica reglas públicas sin levantar sockets."""

    def setUp(self) -> None:
        """Crea un mapa y su gestor de pactos."""
        self.mapa = Mapa(build_map)
        self.pactos = PactManager(self.mapa)

    def test_condominio_conserva_aportes_y_movimiento(self) -> None:
        """Cada jugador sólo puede mover o reforzar su propio aporte."""
        self.mapa.crear_condominio("Objetivo", {1: 1, 2: 1})

        self.assertIsNone(self.mapa.ocupado_por("Objetivo"))
        self.assertTrue(self.mapa.jugador_posee_pais(1, "Objetivo"))
        self.assertEqual(self.mapa.ocupantes("Objetivo"), {1: 1, 2: 1})
        self.mapa.agregar_unidad_jugador("Objetivo", 1)
        self.assertEqual(self.mapa.ocupantes("Objetivo"), {1: 2, 2: 1})
        self.mapa.mover_jugador("Origen", "Objetivo", 1, 1)
        self.assertEqual(self.mapa.ocupantes("Objetivo"), {1: 3, 2: 1})
        self.assertEqual(self.mapa.cantidad_unidades("Origen"), 2)

    def test_expulsar_un_ocupante_normaliza_a_dueno_exclusivo(self) -> None:
        """Cuando queda un solo color, desaparece el estado compartido."""
        self.mapa.crear_condominio("Objetivo", {1: 1, 2: 1})
        self.mapa.expulsar_ocupante("Objetivo", 2)

        self.assertFalse(self.mapa.es_condominio("Objetivo"))
        self.assertEqual(self.mapa.ocupado_por("Objetivo"), 1)
        self.assertEqual(self.mapa.cantidad_unidades("Objetivo"), 1)

    def test_bloqueo_exige_todos_los_vecinos_con_dos_unidades(self) -> None:
        """Un país bloqueado puede detectarse y la excepción de último país aplica."""
        self.mapa.asignar_pais(3, "Origen")
        self.assertTrue(self.pactos.esta_bloqueado("Objetivo", 2))
        self.mapa.set_unidades("Flanco1", 1)
        self.assertFalse(self.pactos.esta_bloqueado("Objetivo", 2))

    def test_disabled_pacts_never_block_countries_or_discard_units(self) -> None:
        """El Null Object respeta desactivar la mecánica completa."""
        self.mapa.asignar_pais(3, "Origen")
        self.assertTrue(self.pactos.esta_bloqueado("Objetivo", 2))
        disabled = NoPactManager(self.mapa)
        self.assertFalse(disabled.esta_bloqueado(pais="Objetivo", jugador=2))
        self.assertTrue(
            disabled.puede_atacar(
                atacante=1, defensor=2, origen="Origen", destino="Objetivo", ronda=3
            )
        )
        self.assertEqual(disabled.public_snapshot(), {"pactos": [], "bloqueos": []})
        pool = ReinforcementPool()
        disabled.prepare_reinforcements(turno=pool)
        self.assertEqual(pool.units, {"infanteria": 3, "A": 4, "B": 2})

    def test_all_destinations_blocked_discards_unplaceable_reinforcements(self) -> None:
        """Todos los refuerzos imposibles se consumen una sola vez."""
        data = build_map()
        data["Origen"][2] = 3
        data["Reserva"][3] = ["Flanco1"]
        manager = PactManager(Mapa(lambda: data))
        pool = ReinforcementPool()
        manager.prepare_reinforcements(pool)
        self.assertEqual(pool.units, {"infanteria": 0, "A": 0, "B": 0})
        manager.prepare_reinforcements(pool)
        self.assertEqual(pool.units, {"infanteria": 0, "A": 0, "B": 0})

    def test_free_continent_preserves_general_and_eligible_bonus_units(self) -> None:
        """Bloquear un continente conserva refuerzos que sí tienen destino."""
        data = build_map()
        data["Origen"][2] = 3
        data["Reserva"][3] = ["Flanco1"]
        data["Libre"] = [1, "B", 2, []]
        pool = ReinforcementPool()
        PactManager(Mapa(lambda: data)).prepare_reinforcements(pool)
        self.assertEqual(pool.units, {"infanteria": 3, "A": 0, "B": 2})

    def test_last_country_exception_keeps_available_reinforcements(self) -> None:
        """La excepción del último país conserva refuerzos para sobrevivir."""
        data = build_map()
        data["Origen"][2] = 3
        data["Reserva"][2] = 3
        pool = ReinforcementPool()
        PactManager(Mapa(lambda: data)).prepare_reinforcements(pool)
        self.assertEqual(pool.units, {"infanteria": 3, "A": 4, "B": 0})

    def test_pacto_requiere_aceptacion_y_bloquea_hasta_la_ruptura(self) -> None:
        """Sólo el invitado acepta y la ruptura conserva el bloqueo una ronda."""
        propuesta = self.pactos.proponer(
            proponente=1,
            jugador_objetivo=2,
            tipo="no_agresion",
            ronda=3,
            paises=("Origen", "Objetivo"),
        )
        self.assertTrue(self.pactos.puede_atacar(1, 2, "Origen", "Objetivo", 3))
        self.pactos.aceptar(propuesta.id, 2)
        self.assertFalse(self.pactos.puede_atacar(1, 2, "Origen", "Objetivo", 3))
        self.pactos.romper(propuesta.id, 1, 3)
        self.assertFalse(self.pactos.puede_atacar(1, 2, "Origen", "Objetivo", 4))
        self.pactos.expirar(5)
        self.assertTrue(self.pactos.puede_atacar(1, 2, "Origen", "Objetivo", 5))

    def test_protocolo_de_pactos_rechaza_campos_faltantes(self) -> None:
        """Los comandos TCP no llegan al juego con payload incompleto."""
        with self.assertRaises(MessageValidationError):
            validate_server_command({"mensaje": "aceptar_pacto"})
        payload = validate_server_command({
            "mensaje": "proponer_pacto",
            "tipo": "no_agresion",
            "jugador_objetivo": 2,
            "paises": ["Origen", "Objetivo"],
        })
        self.assertEqual(payload["mensaje"], "proponer_pacto")

    def test_agresion_identifica_objetivo_y_condominio_crea_no_agresion(self) -> None:
        """La conquista pactada puede registrar el condominio resultante."""
        self.mapa.asignar_pais(4, "Objetivo")
        propuesta = self.pactos.proponer(
            proponente=1,
            jugador_objetivo=2,
            tipo="agresion",
            ronda=1,
            paises=("Origen",),
            pais_objetivo="Objetivo",
        )
        self.pactos.aceptar(propuesta.id, 2)
        self.assertIsNotNone(self.pactos.aggression_for_conquest(1, 4, "Objetivo", 1))
        self.mapa.crear_condominio("Objetivo", {1: 1, 2: 1})
        self.pactos.invalidar_por_conquista("Objetivo")
        pacto_condominio = self.pactos.registrar_condominio("Objetivo", (1, 2), 1)
        self.assertFalse(self.pactos.puede_atacar(1, 2, "Origen", "Objetivo", 1))
        self.assertTrue(pacto_condominio.automatico)


if __name__ == "__main__":
    unittest.main()
