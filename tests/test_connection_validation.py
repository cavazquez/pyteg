"""Pruebas de validación del formulario para conectarse al servidor."""

from __future__ import annotations

import unittest

from pyteg.gui.dialogs.conectar.validation import (
    TCP_MAX_PORT,
    TCP_MIN_PORT,
    ValidationError,
    validate,
)


class ConnectionValidationTests(unittest.TestCase):
    """Valida y normaliza los campos que ingresa quien se conecta."""

    def test_recorta_direccion_y_usuario(self) -> None:
        """Elimina espacios externos de dirección y nombre."""
        self.assertEqual(
            validate(" localhost ", "65432", " Ana "),
            (
                "localhost",
                65432,
                "Ana",
            ),
        )

    def test_rechaza_direccion_vacia_o_solo_espacios(self) -> None:
        """No acepta una dirección que quede vacía después de recortarla."""
        for address in ("", "   "):
            with self.subTest(address=address):
                result = validate(address, "65432", "Ana")
                if not isinstance(result, ValidationError):
                    self.fail("Se aceptó una dirección vacía")
                self.assertEqual(result.field, "addr")

    def test_acepta_los_limites_del_rango_tcp(self) -> None:
        """Acepta los puertos TCP primero y último."""
        for port in (str(TCP_MIN_PORT), str(TCP_MAX_PORT)):
            with self.subTest(port=port):
                result = validate("localhost", port, "Ana")
                if isinstance(result, ValidationError):
                    self.fail(f"Se rechazó el puerto válido {port}")
                self.assertEqual(result[1], int(port))

    def test_rechaza_puertos_fuera_del_rango_tcp(self) -> None:
        """Rechaza puertos fuera del rango TCP y entradas no numéricas."""
        for port in (
            str(TCP_MIN_PORT - 1),
            str(TCP_MAX_PORT + 1),
            "999999",
            "no es puerto",
        ):
            with self.subTest(port=port):
                result = validate("localhost", port, "Ana")
                if not isinstance(result, ValidationError):
                    self.fail(f"Se aceptó el puerto inválido {port}")
                self.assertEqual(result.field, "port")

    def test_rechaza_usuario_vacio_o_solo_espacios(self) -> None:
        """No acepta un nombre vacío después de recortar espacios."""
        for username in ("", "   "):
            with self.subTest(username=username):
                result = validate("localhost", "65432", username)
                if not isinstance(result, ValidationError):
                    self.fail("Se aceptó un nombre vacío")
                self.assertEqual(result.field, "username")


if __name__ == "__main__":
    unittest.main()
