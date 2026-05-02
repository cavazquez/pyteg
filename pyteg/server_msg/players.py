"""Lista de jugadores sincronizada."""

from __future__ import annotations

import json

from pyteg.server_msg.base import IMsg


class MsgActualizarListaJugadores(IMsg):
    """Mensaje para actualizar la lista de jugadores en el cliente."""

    def __init__(self, jugadores: list[tuple[int, dict[str, int]]]) -> None:
        """Inicializa un mensaje para actualizar la lista de jugadores en el cliente.

        Args:
            jugadores (list): Lista de tuplas (userid, color) donde color es un
                diccionario con las claves 'r', 'g', 'b'

        """
        self._tipo = "actualizar_lista_jugadores"
        self._jugadores = jugadores

    def to_json(self) -> str:
        """Convierte el mensaje a formato JSON.

        Returns:
            Representación JSON del mensaje como cadena.

        """
        # Convertir la lista de jugadores a un formato serializable
        jugadores_serializados = []
        for userid, color in self._jugadores:
            if hasattr(color, "to_json"):
                color_dict = json.loads(color.to_json())
            elif isinstance(color, dict):
                color_dict = color
            else:
                color_dict = {"r": 200, "g": 200, "b": 200}  # Color gris por defecto

            jugadores_serializados.append({"userid": userid, "color": color_dict})

        data = {"mensaje": self._tipo, "jugadores": jugadores_serializados}
        return json.dumps(data)
