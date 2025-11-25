from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Any

from src.exception import MensajeNoValidoError
from src.logger import get_logger
from src.server_state_validator import ServerStateValidator
from src.turnos import PrimerTurno, SegundoTurno

LOGGER = get_logger("server.tasks")


class IServerTask(ABC):
    """Clase base para todas las tareas del servidor."""

    def __init__(self, data):
        self._data = data
        self._action_name: str | None = None  # Nombre de la acción para validación
        self._validator = ServerStateValidator()

    @abstractmethod
    def _execute(self, client):
        """Método que implementa la lógica específica de cada tarea."""

    def run(self, client):
        """Ejecuta la tarea validando primero el estado del servidor."""
        # Validar estado usando TaskValidator cuando corresponda
        if self._action_name is not None:
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
        self._segundos = data.get("segundos")
        self._paises_para_victoria = data.get("paises_para_victoria")
        self._objetivos_secretos = data.get("objetivos_secretos", False)
        self._misiles_habilitados = data.get("misiles_habilitados", False)
        self._action_name = "empezar"

    def _execute(self, client):
        # Configurar segundos por turno si se envió desde el cliente
        if self._segundos is not None:
            try:
                segundos_int = int(self._segundos)
                if segundos_int > 0:
                    client.server.set_segundos_por_turno(segundos_int)
            except (TypeError, ValueError):
                pass

        # Configurar países para victoria si se envió desde el cliente
        if self._paises_para_victoria is not None:
            try:
                paises_int = int(self._paises_para_victoria)
                if paises_int >= 0:  # Permitir 0 para desactivar objetivo específico
                    client.server.set_paises_para_victoria(paises_int)
            except (TypeError, ValueError):
                pass

        # Configurar objetivos secretos si se envió desde el cliente
        client.server.set_objetivos_secretos(activados=self._objetivos_secretos)
        LOGGER.debug("Objetivos secretos configurados: %s", self._objetivos_secretos)

        # Configurar misiles si se envió desde el cliente
        client.server.set_misiles_habilitados(activados=self._misiles_habilitados)
        LOGGER.debug("Misiles habilitados: %s", self._misiles_habilitados)

        if client.server.estado.esperar_jugadores():
            client.server.enviar_estado()
        else:
            LOGGER.warning(
                "No se pudo cambiar a estado EsperarJugadores desde %s",
                client.server.estado.estado_actual(),
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
            LOGGER.warning(
                "No se pudo empezar la partida desde el estado %s",
                client.server.estado.estado_actual(),
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
                    LOGGER.warning(
                        "Usuario %s intentó usar username duplicado: %s",
                        client.userid(),
                        self._username,
                    )
                    return

            # Username válido, actualizar el nombre de usuario del cliente
            client.set_username(self._username)
            # Notificar a todos los clientes sobre el cambio de nombre
            client.server.enviar_username()
            LOGGER.info(
                "Usuario %s ha cambiado su nombre a: %s",
                client.userid(),
                self._username,
            )


class ServerTaskAgregarUnidad(IServerTask):
    def __init__(self, data):
        super().__init__(data)
        self._pais = data.get("pais")
        self._tipo_unidad = data.get("tipo_unidad")
        self._cantidad = data.get("cantidad", 1)  # Por defecto 1 si no se especifica
        self._action_name = "agregar_unidad"

    def _execute(self, client):
        # Verificar que sea el turno del cliente actual
        if not hasattr(client.server, "game") or client.server.game is None:
            client.transmisor.enviar_error_chat("El juego no ha comenzado")
            return

        turno_actual = client.server.game.turno_actual()
        if turno_actual.jugador_actual() != client:
            client.transmisor.enviar_error_chat("No es tu turno")
            return

        # Verificar que el cliente sea el dueño del país
        if client.server.mapa.ocupado_por(self._pais) != client:
            client.transmisor.enviar_error_chat(f"No eres dueño de {self._pais}")
            return

        # Verificar que el tipo de unidad sea válido
        if self._tipo_unidad not in {"infanteria", "misil"}:
            client.transmisor.enviar_error_chat(
                "Tipo de unidad no válido. Debe ser 'infanteria' o 'misil'."
            )
            return

        # Verificar que el jugador tenga suficientes unidades disponibles
        if (
            not hasattr(turno_actual, "cant_unidades")
            or turno_actual.cant_unidades() < self._cantidad
        ):
            client.transmisor.enviar_error_chat(
                f"No hay suficientes unidades disponibles para agregar "
                f"{self._cantidad} unidades"
            )
            return

        # Agregar la unidad al país
        for _ in range(self._cantidad):
            client.server.mapa.agregar_una_unidad(self._pais)

            # Restar la unidad de las unidades generales disponibles
            if hasattr(turno_actual, "usar_unidad"):
                turno_actual.usar_unidad()

        msg = (
            f"Se agregaron {self._cantidad} unidad(es) de tipo {self._tipo_unidad}"
            f" en {self._pais}"
        )
        LOGGER.info(msg)

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
            client.transmisor.enviar_error_chat(f"No eres dueño de {self._origen}")
            return

        # Verificar que el país de destino sea del mismo jugador
        if client.server.mapa.ocupado_por(self._destino) != client:
            client.transmisor.enviar_error_chat(f"No eres dueño de {self._destino}")
            return

        # Verificar que los países sean adyacentes
        paises_adyacentes = client.server.mapa.obtener_paises_adyacentes(self._origen)
        if self._destino not in paises_adyacentes:
            client.transmisor.enviar_error_chat(
                f"{self._destino} no es adyacente a {self._origen}"
            )
            return

        # Verificar que haya suficientes unidades para mover
        unidades_origen = client.server.mapa.cantidad_unidades(self._origen)
        if unidades_origen <= self._cantidad:
            client.transmisor.enviar_error_chat(
                f"No hay suficientes unidades en {self._origen} "
                f"para mover {self._cantidad}"
            )
            return

        # Mover las unidades
        client.server.mapa.mover(self._origen, self._destino, self._cantidad)
        LOGGER.info(
            "Se movieron %s unidades de %s a %s",
            self._cantidad,
            self._origen,
            self._destino,
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
        if isinstance(turno_actual, PrimerTurno | SegundoTurno):
            client.transmisor.enviar_error_chat(
                "No se puede atacar en los primeros 2 turnos. "
                "Debe esperar al tercer turno."
            )
            return

        # Verificar que el cliente sea el dueño del país de origen
        if client.server.mapa.ocupado_por(self._origen) != client:
            client.transmisor.enviar_error_chat(f"No eres dueño de {self._origen}")
            return

        # Verificar que el país de destino sea de otro jugador
        if client.server.mapa.ocupado_por(self._destino) == client:
            client.transmisor.enviar_error_chat(
                f"No puedes atacar tu propio país: {self._destino}"
            )
            return

        # Verificar que los países sean adyacentes
        paises_adyacentes = client.server.mapa.obtener_paises_adyacentes(self._origen)
        if self._destino not in paises_adyacentes:
            client.transmisor.enviar_error_chat(
                f"{self._destino} no es adyacente a {self._origen}"
            )
            return

        # Verificar que haya al menos 2 unidades en el país de origen
        # (necesita 1 para atacar)
        unidades_origen = client.server.mapa.cantidad_unidades(self._origen)
        if unidades_origen < 2:
            client.transmisor.enviar_error_chat(
                f"Necesitas al menos 2 unidades en {self._origen} para atacar"
            )
            return

        # Logging del estado antes del ataque
        unidades_destino = client.server.mapa.cantidad_unidades(self._destino)
        LOGGER.info("=== INICIO ATAQUE ===")
        LOGGER.info(
            "Origen: %s (%s unidades)",
            self._origen,
            unidades_origen,
        )
        LOGGER.info(
            "Destino: %s (%s unidades)",
            self._destino,
            unidades_destino,
        )
        LOGGER.info("Cantidad unidades atacando: %s", self._cantidad_unidades)

        # Realizar el ataque
        info_batalla = client.server.game.atacar(
            self._origen, self._destino, self._cantidad_unidades
        )

        # Logging del estado después del ataque
        unidades_origen_post = client.server.mapa.cantidad_unidades(self._origen)
        unidades_destino_post = client.server.mapa.cantidad_unidades(self._destino)
        LOGGER.info("=== RESULTADO ATAQUE ===")
        LOGGER.info(
            "Origen: %s (%s -> %s unidades)",
            self._origen,
            unidades_origen,
            unidades_origen_post,
        )
        LOGGER.info(
            "Destino: %s (%s -> %s unidades)",
            self._destino,
            unidades_destino,
            unidades_destino_post,
        )
        LOGGER.info("Conquistado: %s", info_batalla["conquistado"])
        cantidad_texto = (
            f" con {self._cantidad_unidades} unidades"
            if self._cantidad_unidades is not None
            else ""
        )
        LOGGER.info(
            "Ataque realizado de %s a %s%s",
            self._origen,
            self._destino,
            cantidad_texto,
        )

        # Enviar resultado de la batalla a todos los clientes
        batalla_data = {
            "origen": self._origen,
            "destino": self._destino,
            "atacante": info_batalla["atacante"],
            "defensor": info_batalla["defensor"],
            "dados_atacante": info_batalla["dados_atacante"],
            "dados_defensor": info_batalla["dados_defensor"],
            "resultado": info_batalla["resultado"],
            "conquistado": info_batalla["conquistado"],
        }
        for cliente in client.server.dame_clientes():
            cliente.transmisor.enviar_resultado_batalla(batalla_data)

        # Marcar que el jugador conquistó un país en este turno
        # (para poder reclamar tarjeta)
        if info_batalla["conquistado"]:
            LOGGER.info(
                "%s conquistó %s - puede reclamar tarjeta",
                client.username(),
                self._destino,
            )
            # Marcar al jugador como elegible para reclamar tarjeta
            client.server.game.marcar_jugador_puede_reclamar(client)

        # Notificar a todos los clientes sobre el cambio en el mapa
        client.server.enviar_mapa()
        # (esto se podría implementar más adelante)


class ServerTaskFinalizarTurno(IServerTask):
    def __init__(self, data):
        super().__init__(data)
        self._action_name = "finalizar_turno"

    def _execute(self, client):
        # Verificar que sea el turno del cliente actual
        if not hasattr(client.server, "game") or client.server.game is None:
            client.transmisor.enviar_error_chat("El juego no ha comenzado")
            return

        turno_actual = client.server.game.turno_actual()
        if turno_actual.jugador_actual() != client:
            client.transmisor.enviar_error_chat("No es tu turno")
            return

        # Limpiar elegibilidad para reclamar tarjetas del turno anterior
        client.server.game.limpiar_elegibilidad_reclamar()

        # Finalizar el turno actual
        client.server.game.finalizar_turno()

        # Notificar a todos los clientes sobre el cambio de turno
        client.server.enviar_turno_actual()
        client.server.enviar_mapa()


class ServerTaskSolicitarTarjetas(IServerTask):
    def __init__(self, data):
        super().__init__(data)
        # No necesita validación de estado específica

    def _execute(self, client):
        """Envía las tarjetas del jugador al cliente que las solicita."""
        client.server.enviar_tarjetas_jugador(client)


class ServerTaskReclamarTarjeta(IServerTask):
    def __init__(self, data):
        super().__init__(data)
        self._action_name = "reclamar_tarjeta"

    def _execute(self, client):
        """Reclama una tarjeta si el jugador conquistó un país en este turno."""
        # Verificar que el juego haya comenzado
        if not hasattr(client.server, "game") or client.server.game is None:
            client.transmisor.enviar_error_chat("El juego no ha comenzado")
            return

        # Verificar que sea el turno del jugador
        turno_actual = client.server.game.turno_actual()
        if turno_actual.jugador_actual() != client:
            client.transmisor.enviar_error_chat("No es tu turno")
            return

        # Verificar que el jugador pueda reclamar tarjeta (conquistó país en este turno)
        if not client.server.game.puede_reclamar_tarjeta(client):
            client.transmisor.enviar_error_chat(
                "No has conquistado ningún país en este turno"
            )
            return

        # Asignar la tarjeta
        LOGGER.info("Asignando tarjeta a %s por reclamación manual", client.username())
        client.server.game.dame_una_tarjeta(client)

        # Remover al jugador de la lista de elegibles (solo una tarjeta por turno)
        client.server.game.reclamar_tarjeta_jugador(client)

        # Enviar tarjetas actualizadas al cliente
        client.server.enviar_tarjetas_jugador(client)

        # Notificar éxito
        client.transmisor.enviar_sistema("Tarjeta reclamada exitosamente")


class ServerTaskCanjeEspecial(IServerTask):
    def __init__(self, data):
        super().__init__(data)
        self._pais = data.get("pais")
        self._action_name = "canje_especial"

    def _execute(self, client):
        """Ejecuta el canje especial de país + tarjeta por 2 unidades."""
        mapa = client.server.game.mapa()
        mazo = client.server.game.mazo()

        # Validar que el jugador posee el país
        if not mapa.jugador_posee_pais(client, self._pais):
            client.transmisor.enviar_error_chat(f"No posees el país {self._pais}")
            return

        # Buscar y remover la tarjeta correspondiente al país
        tarjeta_encontrada = None
        tarjetas_jugador = mazo.tarjetas_asignadas(client)

        if len(tarjetas_jugador) == 0:
            client.transmisor.enviar_error_chat(
                "No tienes tarjetas. Conquista países para obtener tarjetas."
            )
            return

        for tarjeta in tarjetas_jugador:
            if tarjeta.pais == self._pais:
                tarjeta_encontrada = tarjeta
                break

        if not tarjeta_encontrada:
            client.transmisor.enviar_error_chat(
                f"No posees la tarjeta del país {self._pais}"
            )
            return

        # Realizar el canje especial
        # 1. Remover la tarjeta del jugador
        tarjeta_encontrada.desasignar()
        tarjeta_encontrada.desusar()

        # 2. Agregar 2 unidades al país
        mapa.agregar_una_unidad(self._pais)
        mapa.agregar_una_unidad(self._pais)

        # 3. Notificar a todos los clientes sobre el cambio en el mapa
        client.server.enviar_mapa()

        # 4. Enviar notificación específica del canje especial
        client.transmisor.enviar_canje_especial(self._pais, 2)

        # 5. Actualizar tarjetas del jugador
        client.server.enviar_tarjetas_jugador(client)

        # 6. Notificar éxito
        client.transmisor.enviar_sistema(
            f"Canje especial realizado: +2 unidades en {self._pais}"
        )


class ServerTaskCanjearMisil(IServerTask):
    def __init__(self, data):
        super().__init__(data)
        self._pais = data.get("pais")
        self._action_name = "canjear_misil"

    def _execute(self, client):
        # 1. Verificar que los misiles estén habilitados
        if not client.server.misiles_habilitados():
            client.transmisor.enviar_error_chat(
                "Los misiles no están habilitados en esta partida"
            )
            return

        # 2. Verificar que el juego haya comenzado
        if not hasattr(client.server, "game") or client.server.game is None:
            client.transmisor.enviar_error_chat("El juego no ha comenzado")
            return

        # 3. Verificar que sea el turno del cliente
        turno_actual = client.server.game.turno_actual()
        if turno_actual.jugador_actual() != client:
            client.transmisor.enviar_error_chat("No es tu turno")
            return

        # 4. Verificar que el cliente sea dueño del país
        if client.server.mapa.ocupado_por(self._pais) != client:
            client.transmisor.enviar_error_chat(f"No eres dueño de {self._pais}")
            return

        # 5. Verificar que el país tenga al menos 6 unidades
        unidades = client.server.mapa.cantidad_unidades(self._pais)
        if unidades < 6:
            client.transmisor.enviar_error_chat(
                f"Se requieren al menos 6 unidades para canjear un misil. "
                f"{self._pais} tiene {unidades} unidades."
            )
            return

        # 6. Restar las 6 unidades del país
        for _ in range(6):
            client.server.mapa.restar_una_unidad(self._pais)

        # 7. Agregar misil al país
        client.server.mapa.agregar_misil(self._pais)
        cantidad_misiles = client.server.mapa.cantidad_misiles(self._pais)

        # 8. Notificar cambios a todos los clientes
        client.server.enviar_misil_agregado(self._pais, cantidad_misiles)
        # Actualizar el mapa completo para mostrar cambios en unidades
        client.server.enviar_mapa()

        # 10. Notificar éxito al jugador
        client.transmisor.enviar_sistema(
            f"Misil canjeado en {self._pais}: -6 unidades, +1 misil. "
            f"Total: {cantidad_misiles} misiles"
        )


class ServerTaskLanzarMisil(IServerTask):
    def __init__(self, data):
        super().__init__(data)
        self._pais_origen = data.get("pais_origen")
        self._pais_destino = data.get("pais_destino")
        self._action_name = "lanzar_misil"

    def _execute(self, client):
        # Validar precondiciones y permisos
        error = self._validar_lanzamiento_misil(client)
        if error:
            client.transmisor.enviar_error_chat(error)
            return

        # Calcular distancia y daño
        distancia = client.server.mapa.calcular_distancia(
            self._pais_origen, self._pais_destino
        )
        dano = client.server.mapa.calcular_dano_misil(distancia)

        # Aplicar el daño y usar el misil
        for _ in range(dano):
            client.server.mapa.restar_una_unidad(self._pais_destino)
        client.server.mapa.usar_misil(self._pais_origen)

        # Notificar resultados
        self._notificar_resultado_misil(client, distancia, dano)

    def _validar_lanzamiento_misil(self, client) -> str | None:
        """Valida todas las condiciones para lanzar un misil.

        Returns:
            str | None: Mensaje de error si hay alguna validación fallida,
            None si todo es válido.
        """
        # Validar configuración y estado del juego
        error = self._validar_estado_juego(client)
        if error:
            return error

        # Validar posesión y disponibilidad
        error = self._validar_posesion_misil(client)
        if error:
            return error

        # Validar distancia y daño
        return self._validar_distancia_dano(client)

    def _validar_estado_juego(self, client) -> str | None:
        """Valida que el juego esté en estado correcto."""
        if not client.server.misiles_habilitados():
            return "Los misiles no están habilitados en esta partida"

        if not hasattr(client.server, "game") or client.server.game is None:
            return "El juego no ha comenzado"

        turno_actual = client.server.game.turno_actual()
        if turno_actual.jugador_actual() != client:
            return "No es tu turno"

        return None

    def _validar_posesion_misil(self, client) -> str | None:
        """Valida posesión de países y disponibilidad de misiles."""
        if client.server.mapa.ocupado_por(self._pais_origen) != client:
            return f"No eres dueño de {self._pais_origen}"

        if client.server.mapa.cantidad_misiles(self._pais_origen) == 0:
            return f"{self._pais_origen} no tiene misiles disponibles"

        if client.server.mapa.ocupado_por(self._pais_destino) == client:
            return "No puedes lanzar misiles a tus propios países"

        return None

    def _validar_distancia_dano(self, client) -> str | None:
        """Valida distancia y daño del misil."""
        distancia = client.server.mapa.calcular_distancia(
            self._pais_origen, self._pais_destino
        )

        if distancia == -1:
            return f"No hay camino entre {self._pais_origen} y {self._pais_destino}"

        if distancia > 3:
            return (
                f"El objetivo está demasiado lejos (distancia: {distancia}). "
                "Máximo: 3 saltos"
            )

        dano = client.server.mapa.calcular_dano_misil(distancia)
        unidades_destino = client.server.mapa.cantidad_unidades(self._pais_destino)
        if unidades_destino <= dano:
            return (
                f"El ataque dejaría a {self._pais_destino} sin unidades. "
                f"El país debe conservar al menos 1 unidad. "
                f"Unidades actuales: {unidades_destino}, Daño: {dano}"
            )

        return None

    def _notificar_resultado_misil(self, client, distancia, dano):
        """Notifica el resultado del lanzamiento del misil a todos."""
        unidades_restantes = client.server.mapa.cantidad_unidades(self._pais_destino)

        resultado_data = {
            "jugador": client.username(),
            "pais_origen": self._pais_origen,
            "pais_destino": self._pais_destino,
            "distancia": distancia,
            "dano": dano,
            "unidades_restantes": unidades_restantes,
        }

        client.server.enviar_resultado_misil(resultado_data)
        # Actualizar el mapa completo y misiles
        client.server.enviar_mapa()
        cantidad_misiles_origen = client.server.mapa.cantidad_misiles(self._pais_origen)
        client.server.enviar_misil_agregado(self._pais_origen, cantidad_misiles_origen)


TaskFactory = Callable[[dict[str, Any]], IServerTask]


dict_task: dict[str, TaskFactory] = {
    "chat": ServerTaskChat,
    "empezar": ServerTaskEmpezar,
    "empezar_partida": ServerTaskEmpezarPartida,
    "set_username": ServerTaskSetUsername,
    "agregar_unidad": ServerTaskAgregarUnidad,
    "mover_unidad": ServerTaskMoverUnidad,
    "atacar": ServerTaskAtacar,
    "finalizar_turno": ServerTaskFinalizarTurno,
    "solicitar_tarjetas": ServerTaskSolicitarTarjetas,
    "reclamar_tarjeta": ServerTaskReclamarTarjeta,
    "canje_especial": ServerTaskCanjeEspecial,
    "canjear_misil": ServerTaskCanjearMisil,
    "lanzar_misil": ServerTaskLanzarMisil,
}
