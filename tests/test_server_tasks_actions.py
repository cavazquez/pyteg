"""Tests para las acciones de tareas del servidor."""

import unittest
from typing import Any

from pyteg.server.tasks import (
    ServerTaskAgregarUnidad,
    ServerTaskAtacar,
    ServerTaskMoverUnidad,
)
from pyteg.server_estado import Estado
from pyteg.turnos import PrimerTurno


class DummyValidator:
    """Validador dummy para tests."""

    def validar_accion(self, action_name: str, server: object) -> None:
        """Valida una acción guardando los parámetros.

        Args:
            action_name: Nombre de la acción.
            server: Instancia del servidor.

        """
        self.last_action = action_name
        self.last_server = server


class FakeTransmisor:
    """Transmisor falso para tests."""

    def __init__(self) -> None:
        """Inicializa el transmisor falso."""
        self.error_chat_messages: list[str] = []
        self.resultados_batalla: list[dict[str, object]] = []

    def enviar_error_chat(self, msg: str) -> None:
        """Envía un mensaje de error al chat.

        Args:
            msg: Mensaje de error.

        """
        self.error_chat_messages.append(msg)

    def enviar_resultado_batalla(self, data: dict[str, object]) -> None:
        """Envía el resultado de una batalla.

        Args:
            data: Datos del resultado de batalla.

        """
        self.resultados_batalla.append(data)


class FakeMapa:
    """Mapa falso para tests."""

    def __init__(self) -> None:
        """Inicializa el mapa falso."""
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
        """Configura un país en el mapa.

        Args:
            nombre: Nombre del país.
            owner: Propietario del país.
            unidades: Cantidad de unidades.
            adyacentes: Países adyacentes.

        """
        self.owners[nombre] = owner
        self.units[nombre] = unidades
        self.adyacentes[nombre] = list(adyacentes)

    def ocupado_por(self, pais: str) -> str:
        """Obtiene el propietario de un país.

        Args:
            pais: Nombre del país.

        Returns:
            ID del propietario del país como string.

        """
        owner = self.owners.get(pais)
        if owner is None:
            return ""
        # Si el propietario tiene userid(), retornar su ID como string
        if hasattr(owner, "userid"):
            return str(owner.userid())
        # Si es un objeto genérico, retornar su representación como string
        return str(id(owner))

    def agregar_una_unidad(self, pais: str) -> None:
        """Agrega una unidad a un país.

        Args:
            pais: Nombre del país.

        """
        self.units[pais] = self.units.get(pais, 0) + 1

    def cantidad_unidades(self, pais: str) -> int:
        """Obtiene la cantidad de unidades de un país.

        Args:
            pais: Nombre del país.

        Returns:
            Cantidad de unidades.

        """
        return self.units.get(pais, 0)

    def obtener_paises_adyacentes(self, pais: str) -> list[str]:
        """Obtiene los países adyacentes.

        Args:
            pais: Nombre del país.

        Returns:
            Lista de países adyacentes.

        """
        return self.adyacentes.get(pais, [])

    def mover(self, origen: str, destino: str, cantidad: int) -> None:
        """Mueve unidades entre países.

        Args:
            origen: País de origen.
            destino: País de destino.
            cantidad: Cantidad de unidades a mover.

        """
        self.units[origen] -= cantidad
        self.units[destino] = self.units.get(destino, 0) + cantidad


class FakeTurno:
    """Turno falso para tests."""

    def __init__(self, jugador: object, unidades: int = 5) -> None:
        """Inicializa el turno falso.

        Args:
            jugador: Jugador del turno.
            unidades: Cantidad de unidades disponibles.

        """
        self._jugador = jugador
        self._unidades = unidades

    def jugador_actual(self) -> object:
        """Obtiene el jugador actual.

        Returns:
            Jugador del turno.

        """
        return self._jugador

    def cant_unidades(self) -> int:
        """Obtiene la cantidad de unidades disponibles.

        Returns:
            Cantidad de unidades.

        """
        return self._unidades

    def usar_unidad(self) -> None:
        """Usa una unidad del turno."""
        self._unidades -= 1


class FakeGame:
    """Juego falso para tests."""

    def __init__(self, turno: FakeTurno | PrimerTurno) -> None:
        """Inicializa el juego falso.

        Args:
            turno: Turno actual.

        """
        self._turno = turno
        self.atacar_called_with: tuple[str, str, int] | None = None
        self.tarjeta_marcada = False

    def turno_actual(self) -> FakeTurno | PrimerTurno:
        """Obtiene el turno actual.

        Returns:
            Turno actual.

        """
        return self._turno

    def set_turno(self, turno: FakeTurno | PrimerTurno) -> None:
        """Establece el turno actual.

        Args:
            turno: Nuevo turno.

        """
        self._turno = turno

    def atacar(self, origen: str, destino: str, cantidad: int) -> dict[str, object]:
        """Simula un ataque.

        Args:
            origen: País atacante.
            destino: País defensor.
            cantidad: Cantidad de unidades atacantes.

        Returns:
            Resultado simulado de la batalla.

        """
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
        """Marca que el jugador puede reclamar tarjeta.

        Args:
            _: Jugador (no usado).

        """
        self.tarjeta_marcada = True


class FakeServer:
    """Servidor falso para tests."""

    def __init__(self, jugador_actual: object, mapa: FakeMapa) -> None:
        """Inicializa el servidor falso.

        Args:
            jugador_actual: Jugador actual.
            mapa: Mapa del juego.

        """
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
        """Marca que se envió el mapa."""
        self.sent_map = True

    def enviar_unidades_disponibles(self) -> None:
        """Marca que se enviaron las unidades disponibles."""
        self.sent_units = True

    def enviar_turno_actual(self) -> None:
        """Marca que se envió el turno actual."""
        self.sent_turno = True

    def enviar_resultado_batalla(self, resultado_data: dict[str, Any]) -> None:
        """Envía el resultado de una batalla a todos los clientes."""
        for client in self.dame_clientes():
            client.transmisor.enviar_resultado_batalla(resultado_data)

    def dame_clientes(self) -> list["FakeClient"]:
        """Obtiene la lista de clientes.

        Returns:
            Lista de clientes.

        """
        return self._clientes

    def add_client(self, client: "FakeClient") -> None:
        """Agrega un cliente al servidor.

        Args:
            client: Cliente a agregar.

        """
        self._clientes.append(client)


class FakeClient:
    """Cliente falso para tests."""

    _next_id = 1

    def __init__(self, name: str = "Tester") -> None:
        """Inicializa el cliente falso.

        Args:
            name: Nombre del cliente.

        """
        self._name = name
        self._id = FakeClient._next_id
        FakeClient._next_id += 1
        self.transmisor = FakeTransmisor()
        self.server: FakeServer | None = None

    def username(self) -> str:
        """Obtiene el nombre de usuario.

        Returns:
            Nombre de usuario.

        """
        return self._name

    def userid(self) -> int:
        """Obtiene el ID de usuario.

        Returns:
            ID de usuario.

        """
        return self._id


class ServerTaskTests(unittest.TestCase):
    """Tests para las tareas del servidor."""

    def setUp(self) -> None:
        """Configura el entorno de prueba."""
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
        """Crea una tarea con un validador dummy.

        Args:
            task_cls: Clase de la tarea.
            payload: Datos de la tarea.

        Returns:
            Instancia de la tarea.

        """
        task = task_cls(payload)
        task._validator = DummyValidator()  # noqa: SLF001
        return task

    def test_agregar_unidad_success(self) -> None:
        """Prueba agregar unidad exitosamente."""
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
        """Prueba que agregar unidad rechaza cuando el jugador no es dueño."""
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
        """Prueba que mover unidad valida adyacencia."""
        payload = {"origen": "Origen", "destino": "Isla", "cantidad": 1}
        task = self._make_task(ServerTaskMoverUnidad, payload)

        task.run(self.client)

        self.assertIn("no es adyacente", self.client.transmisor.error_chat_messages[0])

    def test_atacar_bloqueado_en_primer_turno(self) -> None:
        """Prueba que atacar está bloqueado en el primer turno."""
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
        """Prueba que atacar exitosamente envía el resultado."""
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
