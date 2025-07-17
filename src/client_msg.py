import json
from abc import ABC, abstractmethod


class IMsg(ABC):
    @abstractmethod
    def to_json(self):
        pass


class MsgSeleccionarColor(IMsg):
    def __init__(self, color):
        print("MsgSeleccionarColor")
        self._tipo = "seleccionar_color"
        self._color = color

    def to_json(self):
        data = {"mensaje": self._tipo, "color": self._color.name()}
        print(f"{data=}")
        return json.dumps(data)


class MsgEmpezar(IMsg):
    def __init__(self):
        self._tipo = "empezar"

    def to_json(self):
        data = {"mensaje": self._tipo}
        return json.dumps(data)


class MsgChat(IMsg):
    def __init__(self, msg):
        self._tipo = "chat"
        self._msg = msg

    def to_json(self):
        data = {
            "mensaje": self._tipo,
            "msg": self._msg,
        }
        return json.dumps(data)


class MsgSetUsername(IMsg):
    def __init__(self, username):
        self._tipo = "set_username"
        self._username = username

    def to_json(self):
        data = {"mensaje": self._tipo, "username": self._username}
        return json.dumps(data)


class MsgEmpezarPartida(IMsg):
    def __init__(self):
        self._tipo = "empezar_partida"

    def to_json(self):
        data = {
            "mensaje": self._tipo,
        }
        return json.dumps(data)


class MsgAgregarUnidad(IMsg):
    def __init__(self, pais, tipo_unidad, cantidad=1):
        """
        Crea un mensaje para agregar unidades en un país específico.

        Args:
            pais (str): Nombre del país donde se agregará la unidad
            tipo_unidad (str): Tipo de unidad a agregar (ej: 'infanteria', 'misil')
            cantidad (int, optional): Cantidad de unidades a agregar. Defaults to 1.
        """
        self._tipo = "agregar_unidad"
        self._pais = pais
        self._tipo_unidad = tipo_unidad
        self._cantidad = cantidad

    def to_json(self):
        data = {
            "mensaje": self._tipo,
            "pais": self._pais,
            "tipo_unidad": self._tipo_unidad,
            "cantidad": self._cantidad,
        }
        return json.dumps(data)


class MsgMoverUnidad(IMsg):
    def __init__(self, origen, destino, cantidad=1):
        """
        Crea un mensaje para mover unidades entre países.

        Args:
            origen (str): Nombre del país de origen
            destino (str): Nombre del país de destino
            cantidad (int, optional): Cantidad de unidades a mover. Defaults to 1.
        """
        self._tipo = "mover_unidad"
        self._origen = origen
        self._destino = destino
        self._cantidad = cantidad

    def to_json(self):
        data = {
            "mensaje": self._tipo,
            "origen": self._origen,
            "destino": self._destino,
            "cantidad": self._cantidad,
        }
        return json.dumps(data)


class MsgAtacar(IMsg):
    def __init__(self, origen, destino):
        """
        Crea un mensaje para atacar de un país a otro.

        Args:
            origen (str): Nombre del país atacante
            destino (str): Nombre del país defensor
        """
        self._tipo = "atacar"
        self._origen = origen
        self._destino = destino

    def to_json(self):
        data = {
            "mensaje": self._tipo,
            "origen": self._origen,
            "destino": self._destino,
        }
        return json.dumps(data)


class MsgFinalizarTurno(IMsg):
    def __init__(self):
        """Crea un mensaje para finalizar el turno actual."""
        self._tipo = "finalizar_turno"

    def to_json(self):
        data = {"mensaje": self._tipo}
        return json.dumps(data)
