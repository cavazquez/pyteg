"""Validación pura de los datos del formulario de conexión.

Mantenerla aquí permite testearla sin instanciar Qt.
"""

from __future__ import annotations

from dataclasses import dataclass

from pyteg.i18n import translate as _

TCP_MIN_PORT = 1
TCP_MAX_PORT = 65535


@dataclass(frozen=True)
class ValidationError:
    """Resultado de una validación inválida.

    Attributes:
        message: Mensaje (ya traducido) listo para mostrar al usuario.
        field: Identificador del campo origen (`"addr"`, `"port"`,
            `"username"`).

    """

    message: str
    field: str


def validate(
    addr: str, port_text: str, username: str
) -> tuple[str, int, str] | ValidationError:
    """Valida los tres campos del formulario y devuelve valores parseados.

    Args:
        addr: Dirección del servidor.
        port_text: Puerto como texto (se convierte a entero).
        username: Nombre del usuario.

    Returns:
        Tupla ``(addr, port, username_stripped)`` si todo es válido, o un
        `ValidationError` con el primer problema encontrado.

    """
    address = addr.strip()
    if not address:
        return ValidationError(
            _("Por favor ingresa una dirección de servidor válida"),
            "addr",
        )
    try:
        port = int(port_text.strip())
    except TypeError, ValueError:
        return ValidationError(_("Por favor ingresa un puerto válido"), "port")
    if not TCP_MIN_PORT <= port <= TCP_MAX_PORT:
        return ValidationError(_("Por favor ingresa un puerto válido"), "port")
    name = username.strip()
    if not name:
        return ValidationError(
            _("Por favor ingresa un nombre de usuario"),
            "username",
        )
    return (address, port, name)
