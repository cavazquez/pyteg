import unittest

from src.server_estado import Estado
from src.server_tasks import (
    ServerTaskAgregarUnidad,
    ServerTaskAtacar,
    ServerTaskMoverUnidad,
)
from src.turnos import PrimerTurno


class DummyValidator:
    def validar_accion(self, action_name, server):
        self.last_action = action_name
        self.last_server = server


class FakeTransmisor:
    def __init__(self):
        self.error_chat_messages = []
        self.resultados_batalla = []

    def enviar_error_chat(self, msg):
        self.error_chat_messages.append(msg)

    def enviar_resultado_batalla(self, data):
        self.resultados_batalla.append(data)


class FakeMapa:
    def __init__(self):
        self.owners = {}
        self.units = {}
        self.adyacentes = {}

    def set_pais(self, nombre, owner, unidades, adyacentes=()):
        self.owners[nombre] = owner
        self.units[nombre] = unidades
        self.adyacentes[nombre] = list(adyacentes)

    def ocupado_por(self, pais):
        return self.owners.get(pais)

    def agregar_una_unidad(self, pais):
        self.units[pais] = self.units.get(pais, 0) + 1

    def cantidad_unidades(self, pais):
        return self.units.get(pais, 0)

    def obtener_paises_adyacentes(self, pais):
        return self.adyacentes.get(pais, [])

    def mover(self, origen, destino, cantidad):
        self.units[origen] -= cantidad
        self.units[destino] = self.units.get(destino, 0) + cantidad


class FakeTurno:
    def __init__(self, jugador, unidades=5):
        self._jugador = jugador
        self._unidades = unidades

    def jugador_actual(self):
        return self._jugador

    def cant_unidades(self):
        return self._unidades

    def usar_unidad(self):
        self._unidades -= 1


class FakeGame:
    def __init__(self, turno):
        self._turno = turno
        self.atacar_called_with = None
        self.tarjeta_marcada = False

    def turno_actual(self):
        return self._turno

    def set_turno(self, turno):
        self._turno = turno

    def atacar(self, origen, destino, cantidad):
        self.atacar_called_with = (origen, destino, cantidad)
        return {
            "atacante": "A",
            "defensor": "B",
            "dados_atacante": [6, 5],
            "dados_defensor": [4],
            "resultado": {"restar": ["B"]},
            "conquistado": True,
        }

    def marcar_jugador_puede_reclamar(self, _):
        self.tarjeta_marcada = True


class FakeServer:
    def __init__(self, jugador_actual, mapa):
        self.estado = Estado()
        self.estado.esperar_jugadores()
        self.estado.empezar_partida()
        self.mapa = mapa
        self.game = FakeGame(FakeTurno(jugador_actual))
        self.sent_map = False
        self.sent_units = False
        self.sent_turno = False
        self._clientes = []

    def enviar_mapa(self):
        self.sent_map = True

    def enviar_unidades_disponibles(self):
        self.sent_units = True

    def enviar_turno_actual(self):
        self.sent_turno = True

    def dame_clientes(self):
        return self._clientes

    def add_client(self, client):
        self._clientes.append(client)


class FakeClient:
    def __init__(self, name="Tester"):
        self._name = name
        self.transmisor = FakeTransmisor()
        self.server = None

    def username(self):
        return self._name

    def userid(self):
        return 1


class ServerTaskTests(unittest.TestCase):
    def setUp(self):
        self.client = FakeClient()
        self.mapa = FakeMapa()
        self.mapa.set_pais("Origen", self.client, 3, ["Vecino", "Enemigo"])
        self.mapa.set_pais("Vecino", self.client, 1, ["Origen"])
        self.mapa.set_pais("Enemigo", object(), 2, ["Origen"])
        self.mapa.set_pais("Isla", self.client, 1, [])
        self.server = FakeServer(self.client, self.mapa)
        self.server.add_client(self.client)
        self.client.server = self.server

    def _make_task(self, task_cls, payload):
        task = task_cls(payload)
        task._validator = DummyValidator()  # noqa: SLF001
        return task

    def test_agregar_unidad_success(self):
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

    def test_agregar_unidad_rejects_wrong_owner(self):
        other_owner = FakeClient("Otro")
        self.mapa.set_pais("Origen", other_owner, 3, ["Vecino"])
        payload = {
            "pais": "Origen",
            "tipo_unidad": "infanteria",
            "cantidad": 1,
        }
        task = self._make_task(ServerTaskAgregarUnidad, payload)

        task.run(self.client)

        self.assertIn("No eres dueño", self.client.transmisor.error_chat_messages[0])
        self.assertEqual(self.mapa.cantidad_unidades("Origen"), 3)

    def test_mover_unidad_validates_adyacencia(self):
        payload = {"origen": "Origen", "destino": "Isla", "cantidad": 1}
        task = self._make_task(ServerTaskMoverUnidad, payload)

        task.run(self.client)

        self.assertIn("no es adyacente", self.client.transmisor.error_chat_messages[0])

    def test_atacar_bloqueado_en_primer_turno(self):
        primer_turno = PrimerTurno(self.client)
        self.server.game.set_turno(primer_turno)
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

    def test_atacar_exitoso_envia_resultado(self):
        self.server.game.set_turno(FakeTurno(self.client, unidades=4))
        self.mapa.set_pais("Enemigo", object(), 2, ["Origen"])
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
