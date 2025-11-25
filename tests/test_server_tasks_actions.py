import unittest
from typing import Any

from src.server_estado import Estado
from src.server_tasks import (
    ServerTaskAgregarUnidad,
    ServerTaskAtacar,
    ServerTaskMoverUnidad,
)
from src.turnos import PrimerTurno


class DummyValidator:
    def validar_accion(self, action_name: str, server: object) -> None:
        self.last_action = action_name
        self.last_server = server


class FakeTransmisor:
    def __init__(self) -> None:
        self.error_chat_messages: list[str] = []
        self.resultados_batalla: list[dict[str, object]] = []

    def enviar_error_chat(self, msg: str) -> None:
        self.error_chat_messages.append(msg)

    def enviar_resultado_batalla(self, data: dict[str, object]) -> None:
        self.resultados_batalla.append(data)


class FakeMapa:
    def __init__(self) -> None:
        self.owners: dict[str, object] = {}
        self.units: dict[str, int] = {}
        self.adyacentes: dict[str, list[str]] = {}

    def set_pais(
        self,
        nombre: str,
        owner: object,
        unidades: int,
        adyacentes: tuple[str, ...] = (),
    ) -> None:
        self.owners[nombre] = owner
        self.units[nombre] = unidades
        self.adyacentes[nombre] = list(adyacentes)

    def ocupado_por(self, pais: str) -> object:
        return self.owners.get(pais)

    def agregar_una_unidad(self, pais: str) -> None:
        self.units[pais] = self.units.get(pais, 0) + 1

    def cantidad_unidades(self, pais: str) -> int:
        return self.units.get(pais, 0)

    def obtener_paises_adyacentes(self, pais: str) -> list[str]:
        return self.adyacentes.get(pais, [])

    def mover(self, origen: str, destino: str, cantidad: int) -> None:
        self.units[origen] -= cantidad
        self.units[destino] = self.units.get(destino, 0) + cantidad


class FakeTurno:
    def __init__(self, jugador: object, unidades: int = 5) -> None:
        self._jugador = jugador
        self._unidades = unidades

    def jugador_actual(self) -> object:
        return self._jugador

    def cant_unidades(self) -> int:
        return self._unidades

    def usar_unidad(self) -> None:
        self._unidades -= 1


class FakeGame:
    def __init__(self, turno: FakeTurno | PrimerTurno) -> None:
        self._turno = turno
        self.atacar_called_with: tuple[str, str, int] | None = None
        self.tarjeta_marcada = False

    def turno_actual(self) -> FakeTurno | PrimerTurno:
        return self._turno

    def set_turno(self, turno: FakeTurno | PrimerTurno) -> None:
        self._turno = turno

    def atacar(self, origen: str, destino: str, cantidad: int) -> dict[str, object]:
        self.atacar_called_with = (origen, destino, cantidad)
        return {
            "atacante": "A",
            "defensor": "B",
            "dados_atacante": [6, 5],
            "dados_defensor": [4],
            "resultado": {"restar": ["B"]},
            "conquistado": True,
        }

    def marcar_jugador_puede_reclamar(self, _: object) -> None:
        self.tarjeta_marcada = True


class FakeServer:
    def __init__(self, jugador_actual: object, mapa: FakeMapa) -> None:
        self.estado = Estado()
        self.estado.esperar_jugadores()
        self.estado.empezar_partida()
        self.mapa = mapa
        self.game = FakeGame(FakeTurno(jugador_actual))
        self.sent_map = False
        self.sent_units = False
        self.sent_turno = False
        self._clientes: list[FakeClient] = []

    def enviar_mapa(self) -> None:
        self.sent_map = True

    def enviar_unidades_disponibles(self) -> None:
        self.sent_units = True

    def enviar_turno_actual(self) -> None:
        self.sent_turno = True

    def dame_clientes(self) -> list["FakeClient"]:
        return self._clientes

    def add_client(self, client: "FakeClient") -> None:
        self._clientes.append(client)


class FakeClient:
    def __init__(self, name: str = "Tester") -> None:
        self._name = name
        self.transmisor = FakeTransmisor()
        self.server: FakeServer | None = None

    def username(self) -> str:
        return self._name

    def userid(self) -> int:
        return 1


class ServerTaskTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = FakeClient()
        self.mapa = FakeMapa()
        self.mapa.set_pais("Origen", self.client, 3, ("Vecino", "Enemigo"))
        self.mapa.set_pais("Vecino", self.client, 1, ("Origen",))
        self.mapa.set_pais("Enemigo", object(), 2, ("Origen",))
        self.mapa.set_pais("Isla", self.client, 1, ())
        self.server = FakeServer(self.client, self.mapa)
        self.server.add_client(self.client)
        self.client.server = self.server

    def _make_task(self, task_cls: type, payload: dict[str, object]) -> Any:
        task = task_cls(payload)
        task._validator = DummyValidator()  # noqa: SLF001
        return task

    def test_agregar_unidad_success(self) -> None:
        payload = {
            "pais": "Origen",
            "tipo_unidad": "infanteria",
            "cantidad": 2,
        }
        task = self._make_task(ServerTaskAgregarUnidad, payload)

        task.run(self.client)

        self.assertEqual(self.mapa.cantidad_unidades("Origen"), 5)
        self.assertEqual(self.server.game.turno_actual().cant_unidades(), 3)
        self.assertTrue(self.server.sent_map)
        self.assertTrue(self.server.sent_units)

    def test_agregar_unidad_rejects_wrong_owner(self) -> None:
        other_owner = FakeClient("Otro")
        self.mapa.set_pais("Origen", other_owner, 3, ("Vecino",))
        payload = {
            "pais": "Origen",
            "tipo_unidad": "infanteria",
            "cantidad": 1,
        }
        task = self._make_task(ServerTaskAgregarUnidad, payload)

        task.run(self.client)

        self.assertIn("No eres dueño", self.client.transmisor.error_chat_messages[0])
        self.assertEqual(self.mapa.cantidad_unidades("Origen"), 3)

    def test_mover_unidad_validates_adyacencia(self) -> None:
        payload = {"origen": "Origen", "destino": "Isla", "cantidad": 1}
        task = self._make_task(ServerTaskMoverUnidad, payload)

        task.run(self.client)

        self.assertIn("no es adyacente", self.client.transmisor.error_chat_messages[0])

    def test_atacar_bloqueado_en_primer_turno(self) -> None:
        # Usar PrimerTurno real para que el código detecte que es el primer turno
        self.server.game.set_turno(PrimerTurno(self.client.username()))
        payload = {
            "origen": "Origen",
            "destino": "Enemigo",
            "cantidad_unidades": 3,
        }
        task = self._make_task(ServerTaskAtacar, payload)

        task.run(self.client)

        self.assertIn(
            "No se puede atacar en los primeros 2 turnos",
            self.client.transmisor.error_chat_messages[0],
        )

    def test_atacar_exitoso_envia_resultado(self) -> None:
        self.server.game.set_turno(FakeTurno(self.client, unidades=4))
        self.mapa.set_pais("Enemigo", object(), 2, ("Origen",))
        payload = {
            "origen": "Origen",
            "destino": "Enemigo",
            "cantidad_unidades": 3,
        }
        task = self._make_task(ServerTaskAtacar, payload)

        task.run(self.client)

        self.assertTrue(self.server.sent_map)
        self.assertTrue(self.server.game.tarjeta_marcada)
        self.assertGreater(len(self.client.transmisor.resultados_batalla), 0)


if __name__ == "__main__":
    unittest.main()
