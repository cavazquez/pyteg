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
    def __init__(self, msg, msg_type="normal"):
        self._tipo = "chat"
        self._msg = msg
        self._msg_type = msg_type  # "normal", "error", "system"

    def to_json(self):
        data = {
            "mensaje": self._tipo,
            "msg": self._msg,
            "msg_type": self._msg_type,
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


class MsgTurno(IMsg):
    def __init__(
        self,
        num_turno,
        num_ronda,
        jugador_actual_id=None,
        jugador_actual_nombre=None,
        jugador_actual_color=None,
    ):
        self._tipo = "turno"
        self._num_turno = num_turno
        self._num_ronda = num_ronda
        self._jugador_actual_id = jugador_actual_id
        self._jugador_actual_nombre = jugador_actual_nombre
        self._jugador_actual_color = jugador_actual_color

    def to_json(self):
        data = {
            "mensaje": self._tipo,
            "num_turno": self._num_turno,
            "num_ronda": self._num_ronda,
        }

        # Agregar información del jugador actual si está disponible
        if self._jugador_actual_id is not None:
            data["jugador_actual_id"] = self._jugador_actual_id
        if self._jugador_actual_nombre is not None:
            data["jugador_actual_nombre"] = self._jugador_actual_nombre
        if self._jugador_actual_color is not None:
            data["jugador_actual_color"] = self._jugador_actual_color

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


class MsgActualizarListaJugadores(IMsg):
    def __init__(self, jugadores):
        """
        Inicializa un mensaje para actualizar la lista de jugadores en el cliente.

        Args:
            jugadores (list): Lista de tuplas (userid, color) donde color es un
                diccionario con las claves 'r', 'g', 'b'
        """
        self._tipo = "actualizar_lista_jugadores"
        self._jugadores = jugadores

    def to_json(self):
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


class MsgResultadoBatalla(IMsg):
    def __init__(self, batalla_data):
        """
        Inicializa un mensaje con el resultado de una batalla.

        Args:
            batalla_data (dict): Diccionario con todos los datos de la batalla:
                - origen (str): País atacante
                - destino (str): País defensor
                - atacante (str): Nombre del jugador atacante
                - defensor (str): Nombre del jugador defensor
                - dados_atacante (list): Lista de dados del atacante
                - dados_defensor (list): Lista de dados del defensor
                - resultado (dict): Resultado de la batalla con pérdidas
                - conquistado (bool): Si el país fue conquistado
        """
        self._tipo = "resultado_batalla"
        self._origen = batalla_data["origen"]
        self._destino = batalla_data["destino"]
        self._atacante = batalla_data["atacante"]
        self._defensor = batalla_data["defensor"]
        self._dados_atacante = batalla_data["dados_atacante"]
        self._dados_defensor = batalla_data["dados_defensor"]
        self._resultado = batalla_data["resultado"]
        self._conquistado = batalla_data.get("conquistado", False)

    def to_json(self):
        data = {
            "mensaje": self._tipo,
            "origen": self._origen,
            "destino": self._destino,
            "atacante": self._atacante,
            "defensor": self._defensor,
            "dados_atacante": self._dados_atacante,
            "dados_defensor": self._dados_defensor,
            "resultado": self._resultado,
            "conquistado": self._conquistado,
        }
        return json.dumps(data)


class MsgError(IMsg):
    def __init__(self, error_type, message):
        """
        Inicializa un mensaje de error del servidor.

        Args:
            error_type (str): Tipo de error (ej: "duplicate_username")
            message (str): Mensaje descriptivo del error
        """
        self._tipo = "error"
        self._error_type = error_type
        self._message = message

    def to_json(self):
        data = {
            "mensaje": self._tipo,
            "error_type": self._error_type,
            "message": self._message,
        }
        return json.dumps(data)


class MsgVictoria(IMsg):
    def __init__(self, ganador_id, ganador_nombre):
        """
        Inicializa un mensaje de victoria.

        Args:
            ganador_id (str): ID del jugador ganador
            ganador_nombre (str): Nombre del jugador ganador
        """
        self._tipo = "victoria"
        self._ganador_id = ganador_id
        self._ganador_nombre = ganador_nombre

    def to_json(self):
        data = {
            "mensaje": self._tipo,
            "ganador_id": self._ganador_id,
            "ganador_nombre": self._ganador_nombre,
        }
        return json.dumps(data)


class MsgConfiguracionPartida(IMsg):
    def __init__(self, segundos_por_turno, paises_para_victoria):
        """
        Inicializa un mensaje con la configuración de la partida.

        Args:
            segundos_por_turno (int): Duración de cada turno en segundos
            paises_para_victoria (int): Número de países necesarios para ganar
        """
        self._tipo = "configuracion_partida"
        self._segundos_por_turno = segundos_por_turno
        self._paises_para_victoria = paises_para_victoria

    def to_json(self):
        data = {
            "mensaje": self._tipo,
            "segundos_por_turno": self._segundos_por_turno,
            "paises_para_victoria": self._paises_para_victoria,
        }
        return json.dumps(data)


class MsgTarjetasJugador(IMsg):
    def __init__(self, tarjetas):
        """
        Inicializa un mensaje con las tarjetas del jugador.

        Args:
            tarjetas (list): Lista de tarjetas con formato
                [{"pais": str, "simbolo": str}, ...]
        """
        self._tipo = "tarjetas_jugador"
        self._tarjetas = tarjetas

    def to_json(self):
        data = {
            "mensaje": self._tipo,
            "tarjetas": self._tarjetas,
        }
        return json.dumps(data)


class MsgSolicitarTarjetas(IMsg):
    def __init__(self):
        """Mensaje para solicitar las tarjetas del jugador al servidor."""
        self._tipo = "solicitar_tarjetas"

    def to_json(self):
        data = {"mensaje": self._tipo}
        return json.dumps(data)


class MsgReclamarTarjeta(IMsg):
    def __init__(self):
        """Mensaje para reclamar una tarjeta después de conquistar un país."""
        self._tipo = "reclamar_tarjeta"

    def to_json(self):
        data = {"mensaje": self._tipo}
        return json.dumps(data)


class MsgCanjeEspecial(IMsg):
    def __init__(self, pais, unidades_agregadas):
        self._tipo = "canje_especial"
        self._pais = pais
        self._unidades_agregadas = unidades_agregadas

    def to_json(self):
        data = {
            "mensaje": self._tipo,
            "pais": self._pais,
            "unidades_agregadas": self._unidades_agregadas,
        }
        return json.dumps(data)
