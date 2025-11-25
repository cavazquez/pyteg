import unittest
from dataclasses import dataclass

from src.exception import EstadoInvalidoError
from src.server_estado import Estado
from src.server_state_validator import ServerStateValidator


@dataclass
class FakeServer:
    estado: Estado


class ServerStateValidatorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.validator = ServerStateValidator()

    def test_valid_action_in_current_state(self) -> None:
        estado = Estado()
        estado.esperar_jugadores()
        estado.empezar_partida()
        server = FakeServer(estado)

        self.assertTrue(self.validator.puede_ejecutar("agregar_unidad", server))

    def test_invalid_action_raises(self) -> None:
        estado = Estado()  # Inicial no permite atacar
        server = FakeServer(estado)

        with self.assertRaises(EstadoInvalidoError) as ctx:
            self.validator.validar_accion("atacar", server)

        self.assertIn("atacar", str(ctx.exception))
        self.assertIn(Estado.JUGANDO, ctx.exception.estados_validos)


if __name__ == "__main__":
    unittest.main()
