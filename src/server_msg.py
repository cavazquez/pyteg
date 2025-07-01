import json
from abc import ABC, abstractmethod


class IMsg(ABC):
    @abstractmethod
    def to_json(self):
        pass


class MsgSosAdmin(IMsg):
    def __init__(self):
        self._tipo = "sosadmin"

    def to_json(self):
        data = {"mensaje": self._tipo}
        return json.dumps(data)


class MsgColorAsignado(IMsg):
    def __init__(self, id_user, rgb_json):
        self._tipo = "color_asignado"
        self._id_user = id_user
        self._rgb_json = rgb_json
        print(rgb_json)

    def to_json(self):
        data = {
            "mensaje": self._tipo,
            "id": self._id_user,
        }
        rgb_dict = json.loads(self._rgb_json)
        return json.dumps(data | rgb_dict)


class MsgColor(IMsg):
    def __init__(self, color):
        self._tipo = "color"
        self._color = color

    def to_json(self):
        color_json = json.loads(self._color.to_json())
        data = {
            "mensaje": self._tipo,
        }
        return json.dumps(data | color_json)


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


class MsgUserId(IMsg):
    def __init__(self, user_id):
        self._tipo = "user_id"
        self._user_id = user_id

    def to_json(self):
        data = {"mensaje": self._tipo, "user_id": self._user_id}
        return json.dumps(data)


class MsgUsername(IMsg):
    def __init__(self, userid, username):
        self._tipo = "username"
        self._userid = userid
        self._username = username

    def to_json(self):
        data = {
            "mensaje": self._tipo,
            "username": self._username,
            "user_id": self._userid,
        }
        return json.dumps(data)


class MsgEstado(IMsg):
    def __init__(self, estado):
        self._tipo = "estado"
        self._estado = estado

    def to_json(self):
        data = {"mensaje": self._tipo, "estado": self._estado}
        return json.dumps(data)


class MsgTiempo(IMsg):
    def __init__(self, userid_turno, tiempo_restante):
        self._tipo = "tiempo"
        self._userid_turno = userid_turno
        self._tiempo_restante = tiempo_restante

    def to_json(self):
        data = {
            "mensaje": self._tipo,
            "user_id": self._userid_turno,
            "tiempo": self._tiempo_restante,
        }
        return json.dumps(data)


class MsgPais(IMsg):
    def __init__(self, pais, userid, unidades):
        self._tipo = "pais"
        self._pais = pais
        self._userid = userid
        self._unidades = unidades

    def to_json(self):
        data = {
            "mensaje": self._tipo,
            "pais": self._pais,
            "userid": self._userid,
            "unidades": self._unidades,
        }
        print(data)
        return json.dumps(data)


class MsgAgregarUnidad(IMsg):
    def __init__(self, pais, tipo_unidad, cantidad):
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


class MsgUnidadesDisponibles(IMsg):
    def __init__(self, unidades):
        self._tipo = "unidades_disponibles"
        self._unidades = (
            unidades  # Diccionario con el tipo de unidad y la cantidad disponible
        )

    def to_json(self):
        data = {
            "mensaje": self._tipo,
            "unidades": self._unidades,
        }
        return json.dumps(data)


class MsgMoverUnidad(IMsg):
    def __init__(self, origen, destino, cantidad):
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
