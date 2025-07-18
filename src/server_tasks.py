from abc import ABC, abstractmethod

from src.exception import MensajeNoValidoError
from src.server_state_validator import ServerStateValidator
from src.turnos import PrimerTurno, SegundoTurno


class IServerTask(ABC):
    """Clase base para todas las tareas del servidor."""

    def __init__(self, data):
        self._data = data
        self._action_name = None  # Nombre de la acción para validación de estado
        self._validator = ServerStateValidator()

    @abstractmethod
    def _execute(self, client):
        """Método que implementa la lógica específica de cada tarea."""

    def run(self, client):
        """Ejecuta la tarea validando primero el estado del servidor."""
        # Validar estado usando TaskValidator
        self._validator.validar_accion(self._action_name, client.server)

        # Ejecutar la tarea si la validación pasa
        return self._execute(client)


class ServerTaskNull(IServerTask):
    def __init__(self, data):
        super().__init__(data)
        # No necesita validación de estado

    def _execute(self, _):
        msg = f"{self._data}"
        raise MensajeNoValidoError(msg)


class ServerTaskChat(IServerTask):
    def __init__(self, data):
        super().__init__(data)
        self._msg = data.get("msg")
        self._action_name = "chat"

    def _execute(self, client):
        client.server.enviar_chat(client.username(), self._msg)


class ServerTaskEmpezar(IServerTask):
    def __init__(self, data):
        super().__init__(data)
        self._action_name = "empezar"

    def _execute(self, client):
        if client.server.estado.esperar_jugadores():
            client.server.enviar_estado()
        else:
            print(
                f"No se pudo cambiar a estado EsperarJugadores desde "
                f"{client.server.estado.estado_actual()}"
            )


class ServerTaskSeleccionarColor(IServerTask):
    def __init__(self, data):
        super().__init__(data)
        self._color = data.get("color")
        self._action_name = "seleccionar_color"

    def _execute(self, client):
        client.cambiar_color(self._color)
        client.server.enviar_colores_asignados()


class ServerTaskEmpezarPartida(IServerTask):
    def __init__(self, data):
        super().__init__(data)
        self._action_name = "empezar_partida"

    def _execute(self, client):
        if client.server.estado.empezar_partida():
            client.server.enviar_estado()
            client.server.empezar_partida()
        else:
            print(
                f"No se pudo empezar la partida desde el estado "
                f"{client.server.estado.estado_actual()}"
            )


class ServerTaskSetUsername(IServerTask):
    def __init__(self, data):
        super().__init__(data)
        self._username = data.get("username")
        self._action_name = "set_username"

    def _execute(self, client):
        if self._username and isinstance(self._username, str):
            # Verificar si el username ya está en uso por otro cliente
            for other_client in client.server.dame_clientes():
                if (
                    other_client.userid() != client.userid()
                    and other_client.username() == self._username
                ):
                    # Username duplicado, enviar error al cliente
                    error_msg = (
                        f"El nombre de usuario '{self._username}' ya está en uso. "
                        "Por favor, elige otro nombre."
                    )
                    client.transmisor.enviar_error("duplicate_username", error_msg)
                    print(
                        f"Usuario {client.userid()} intentó usar username "
                        f"duplicado: {self._username}"
                    )
                    return

            # Username válido, actualizar el nombre de usuario del cliente
            client.set_username(self._username)
            # Notificar a todos los clientes sobre el cambio de nombre
            client.server.enviar_username()
            print(
                f"Usuario {client.userid()} ha cambiado su nombre a: {self._username}"
            )


class ServerTaskAgregarUnidad(IServerTask):
    def __init__(self, data):
        super().__init__(data)
        self._pais = data.get("pais")
        self._tipo_unidad = data.get("tipo_unidad")
        self._cantidad = data.get("cantidad", 1)  # Por defecto 1 si no se especifica
        self._action_name = "agregar_unidad"

    def _execute(self, client):
        # Verificar que el cliente sea el dueño del país
        if client.server.mapa.ocupado_por(self._pais) != client:
            print(f"El jugador {client.userid()} no es dueño de {self._pais}")
            return

        # Verificar que el tipo de unidad sea válido
        if self._tipo_unidad not in {"infanteria", "misil"}:
            print(f"Tipo de unidad no válido: {self._tipo_unidad}")
            return

        # Verificar que el jugador tenga suficientes unidades disponibles
        turno_actual = client.server.game.turno_actual()
        if (
            not hasattr(turno_actual, "cant_unidades")
            or turno_actual.cant_unidades() < self._cantidad
        ):
            msg = (
                f"No hay suficientes unidades disponibles para agregar "
                f"{self._cantidad} {self._tipo_unidad}"
            )
            print(msg)
            return

        # Agregar la unidad al país
        for _ in range(self._cantidad):
            client.server.mapa.agregar_una_unidad(self._pais)

            # Restar la unidad de las unidades generales disponibles
            if hasattr(turno_actual, "usar_unidad"):
                turno_actual.usar_unidad()

        msg = f"Se agregaron {self._cantidad} unidad(es) de tipo {self._tipo_unidad}"
        msg += f" en {self._pais}"
        print(msg)

        # Notificar a todos los clientes sobre el cambio en el mapa
        client.server.enviar_mapa()

        # Actualizar las unidades disponibles en la interfaz del jugador
        client.server.enviar_unidades_disponibles()


class ServerTaskMoverUnidad(IServerTask):
    def __init__(self, data):
        super().__init__(data)
        self._origen = data.get("origen")
        self._destino = data.get("destino")
        self._cantidad = data.get("cantidad", 1)  # Por defecto 1 si no se especifica
        self._action_name = "mover_unidad"

    def _execute(self, client):
        # Verificar que el cliente sea el dueño del país de origen
        if client.server.mapa.ocupado_por(self._origen) != client:
            print(f"El jugador {client.userid()} no es dueño de {self._origen}")
            return

        # Verificar que los países sean adyacentes
        paises_adyacentes = client.server.mapa.obtener_paises_adyacentes(self._origen)
        if self._destino not in paises_adyacentes:
            print(f"{self._destino} no es adyacente a {self._origen}")
            return

        # Verificar que haya suficientes unidades para mover
        unidades_origen = client.server.mapa.cantidad_unidades(self._origen)
        if unidades_origen <= self._cantidad:
            print(
                "No hay suficientes unidades en "
                f"{self._origen} para mover {self._cantidad}"
            )
            return

        # Mover las unidades
        client.server.mapa.mover(self._origen, self._destino, self._cantidad)
        print(
            f"Se movieron {self._cantidad} unidades de {self._origen} a {self._destino}"
        )

        # Notificar a todos los clientes sobre el cambio en el mapa
        client.server.enviar_mapa()


class ServerTaskAtacar(IServerTask):
    def __init__(self, data):
        super().__init__(data)
        self._origen = data.get("origen")
        self._destino = data.get("destino")
        self._cantidad_unidades = data.get("cantidad_unidades")
        self._action_name = "atacar"

    def _execute(self, client):
        # Verificar que no sea primer o segundo turno
        turno_actual = client.server.game.turno_actual()
        if isinstance(turno_actual, (PrimerTurno, SegundoTurno)):
            turno_nombre = type(turno_actual).__name__
            mensaje = (
                f"No se puede atacar en los primeros 2 turnos. "
                f"Turno actual: {turno_nombre}"
            )
            print(mensaje)
            return

        # Verificar que el cliente sea el dueño del país de origen
        if client.server.mapa.ocupado_por(self._origen) != client:
            print(f"El jugador {client.userid()} no es dueño de {self._origen}")
            return

        # Verificar que el país de destino sea de otro jugador
        if client.server.mapa.ocupado_por(self._destino) == client:
            print(f"No puedes atacar tu propio país: {self._destino}")
            return

        # Verificar que los países sean adyacentes
        paises_adyacentes = client.server.mapa.obtener_paises_adyacentes(self._origen)
        if self._destino not in paises_adyacentes:
            print(f"{self._destino} no es adyacente a {self._origen}")
            return

        # Verificar que haya al menos 2 unidades en el país de origen
        # (necesita 1 para atacar)
        unidades_origen = client.server.mapa.cantidad_unidades(self._origen)
        if unidades_origen < 2:
            print(f"Necesitas al menos 2 unidades en {self._origen} para atacar")
            return

        # Realizar el ataque
        client.server.game.atacar(self._origen, self._destino, self._cantidad_unidades)
        cantidad_texto = (
            f" con {self._cantidad_unidades} unidades"
            if self._cantidad_unidades is not None
            else ""
        )
        print(f"Ataque realizado de {self._origen} a {self._destino}{cantidad_texto}")

        # Notificar a todos los clientes sobre el cambio en el mapa
        client.server.enviar_mapa()

        # Dar una tarjeta al jugador si conquistó un país
        # (esto se podría implementar más adelante)


class ServerTaskFinalizarTurno(IServerTask):
    def __init__(self, data):
        super().__init__(data)
        self._action_name = "finalizar_turno"

    def _execute(self, client):
        # Verificar que sea el turno del cliente actual
        if not hasattr(client.server, "game") or client.server.game is None:
            print("El juego no ha comenzado")
            return

        turno_actual = client.server.game.turno_actual()
        if turno_actual.jugador_actual() != client:
            print(f"No es el turno de {client.userid()}")
            return

        # Finalizar el turno actual
        client.server.game.finalizar_turno()

        # Notificar a todos los clientes sobre el cambio de turno
        client.server.enviar_turno_actual()
        client.server.enviar_mapa()


dict_task = {
    "chat": ServerTaskChat,
    "empezar": ServerTaskEmpezar,
    "seleccionar_color": ServerTaskSeleccionarColor,
    "empezar_partida": ServerTaskEmpezarPartida,
    "set_username": ServerTaskSetUsername,
    "agregar_unidad": ServerTaskAgregarUnidad,
    "mover_unidad": ServerTaskMoverUnidad,
    "atacar": ServerTaskAtacar,
    "finalizar_turno": ServerTaskFinalizarTurno,
}
