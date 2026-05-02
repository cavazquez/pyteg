"""Formateo HTML de mensajes del chat (errores, sistema, propios, otros)."""

from __future__ import annotations

from typing import Any


def format_error_message(text: str) -> str:
    """Formatea un mensaje de error con badge rojo.

    Returns:
        HTML del mensaje formateado.

    """
    return (
        f"<div align='left' style='margin: 5px 0;'>"
        f"<span style='background-color: #dc3545; color: white; "
        f"padding: 6px 12px; border-radius: 15px; font-weight: bold;'>"
        f"⚠️ {text}</span></div>"
    )


def format_system_message(text: str) -> str:
    """Formatea un mensaje del sistema con badge azul claro.

    Returns:
        HTML del mensaje formateado.

    """
    return (
        f"<div align='left' style='margin: 5px 0;'>"
        f"<span style='background-color: #17a2b8; color: white; "
        f"padding: 6px 12px; border-radius: 15px; font-style: italic;'>"
        f"[INFO] {text}</span></div>"
    )


def format_self_message(text: str) -> str:
    """Formatea un mensaje propio (alineado a la derecha).

    Returns:
        HTML del mensaje formateado.

    """
    return (
        f"<div align='right' style='margin: 5px 0;'>"
        f"<span style='background-color: #4361ee; color: white; "
        f"padding: 6px 12px; border-radius: 15px;'>"
        f"{text}</span></div>"
    )


def _format_other_default(text: str) -> str:
    """Formato gris por defecto cuando no hay color de usuario disponible.

    Returns:
        HTML del mensaje formateado.

    """
    return (
        f"<div align='left' style='margin: 5px 0;'>"
        f"<span style='background-color: #e9ecef; color: #212529; "
        f"padding: 6px 12px; border-radius: 15px;'>"
        f"{text}</span></div>"
    )


def _format_other_with_color(username: str, message: str, user_color: str) -> str:
    """Formatea un mensaje de otro jugador resaltando su nombre con color.

    Returns:
        HTML del mensaje formateado.

    """
    return (
        f"<div align='left' style='margin: 5px 0;'>"
        f"<span style='background-color: #e9ecef; color: #212529; "
        f"padding: 6px 12px; border-radius: 15px;'>"
        f"<span style='color: {user_color}; font-weight: bold;'>"
        f"{username}</span>: {message}"
        f"</span></div>"
    )


def get_user_color(colores_obj: Any, username: str) -> str | None:
    """Obtiene el color hexadecimal asociado a un username.

    Args:
        colores_obj: Objeto `Colores` de la ventana principal.
        username: Nombre del usuario.

    Returns:
        Hex (`#rrggbb`) o `None` si no hay colores asignados.

    """
    try:
        colores_asignados = colores_obj.colores_asignados()
        if not colores_asignados:
            return None
        user_colors = list(colores_asignados.values())
        if not user_colors:
            return None
        color_index = hash(username) % len(user_colors)
        selected_color = user_colors[color_index]

        if hasattr(selected_color, "name"):
            name_result = selected_color.name()
            if isinstance(name_result, str):
                return name_result
        if hasattr(selected_color, "red"):
            r = int(selected_color.red() * 255)
            g = int(selected_color.green() * 255)
            b = int(selected_color.blue() * 255)
            return f"#{r:02x}{g:02x}{b:02x}"
    except (AttributeError, KeyError, TypeError):
        return None
    return None


def format_other_message(colores_obj: Any, text: str) -> str:
    """Formatea un mensaje de otro jugador (con color del nombre si aplica).

    Acepta texto con o sin prefijo ``"username: "``.

    Returns:
        HTML del mensaje formateado.

    """
    if ":" in text:
        username, message = text.split(":", 1)
        username = username.strip()
        message = message.strip()
        user_color = get_user_color(colores_obj, username)
        if user_color:
            return _format_other_with_color(username, message, user_color)
    return _format_other_default(text)
