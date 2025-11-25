"""Tests para el módulo de validación de estado del servidor."""

import unittest
from dataclasses import dataclass

from src.exception import EstadoInvalidoError
from src.server_estado import Estado
from src.server_state_validator import ServerStateValidator


@dataclass
class FakeServer:
    """Servidor falso para tests."""

    estado: Estado


class ServerStateValidatorTests(unittest.TestCase):
    """Tests para ServerStateValidator."""

    def setUp(self) -> None:
        """Configura el entorno de prueba."""
        self.validator = ServerStateValidator()

    def test_valid_action_in_current_state(self) -> None:
        """Prueba que una acción válida en el estado actual sea permitida."""
        estado = Estado()
        estado.esperar_jugadores()
        estado.empezar_partida()
        server = FakeServer(estado)

        self.assertTrue(self.validator.puede_ejecutar("agregar_unidad", server))

    def test_invalid_action_raises(self) -> None:
        """Prueba que una acción inválida en el estado actual lance excepción."""
        estado = Estado()  # Inicial no permite atacar
        server = FakeServer(estado)

        with self.assertRaises(EstadoInvalidoError) as ctx:
            self.validator.validar_accion("atacar", server)

        self.assertIn("atacar", str(ctx.exception))
        self.assertIn(Estado.JUGANDO, ctx.exception.estados_validos)


if __name__ == "__main__":
    unittest.main()
