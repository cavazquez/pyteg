"""Módulo para manejar las tareas del servidor basadas en mensajes del cliente."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Any

from src.config import (
    MIN_UNITS_FOR_ATTACK,
    MIN_UNITS_TO_LEAVE,
    MISSILE_MAX_DISTANCE,
    MISSILE_UNIT_COST,
    SPECIAL_EXCHANGE_UNITS,
    VALID_UNIT_TYPES,
)
from src.exception import MensajeNoValidoError
from src.game_context import GameContext
from src.logger import get_logger
from src.server_state_validator import ServerStateValidator
from src.server_validators import (
    AdjacencyValidator,
    AttackRestrictionValidator,
    CountryOwnershipValidator,
    GameStateValidator,
    TurnValidator,
    UnitTypeValidator,
    UnitValidator,
    ValidationError,
)

LOGGER = get_logger("server.tasks")


class IServerTask(ABC):
    """Clase base para todas las tareas del servidor."""

    def __init__(self, data: dict[str, Any]) -> None:
        """Inicializa la tarea del servidor.

        Args:
            data: Datos del mensaje recibido del cliente.

        """
        self._data = data
        self._action_name: str | None = None  # Nombre de la acción para validación
        self._validator = ServerStateValidator()

    @abstractmethod
    def _execute(self, client: Any, context: GameContext) -> None:
        """Método que implementa la lógica específica de cada tarea.

        Args:
            client: Cliente que ejecuta la tarea.
            context: Contexto de acceso a recursos del juego.

        """

    def run(self, client: Any) -> None:
        """Ejecuta la tarea validando primero el estado del servidor."""
        # Validar estado usando TaskValidator cuando corresponda
        if self._action_name is not None:
            self._validator.validar_accion(self._action_name, client.server)

        # Crear contexto de acceso a recursos
        context = GameContext(
            client.server.mapa,
            client.server.game,
            client.server,
        )

        # Ejecutar la tarea si la validación pasa
        self._execute(client, context)


class ServerTaskNull(IServerTask):
    """Tarea nula para mensajes no reconocidos."""

    def __init__(self, data: dict[str, Any]) -> None:
        """Inicializa la tarea nula.

        Args:
            data: Datos del mensaje recibido.

        """
        super().__init__(data)
        # No necesita validación de estado

    def _execute(self, _: Any, context: GameContext) -> None:  # noqa: ARG002
        msg = f"{self._data}"
        raise MensajeNoValidoError(msg)


class ServerTaskChat(IServerTask):
    """Tarea para procesar mensajes de chat."""

    def __init__(self, data: dict[str, Any]) -> None:
        """Inicializa la tarea de chat.

        Args:
            data: Datos del mensaje de chat.

        """
        super().__init__(data)
        self._msg = data.get("msg")
        self._action_name = "chat"

    def _execute(self, client: Any, context: GameContext) -> None:  # noqa: ARG002
        client.server.enviar_chat(client.username(), self._msg)


class ServerTaskEmpezar(IServerTask):
    """Tarea para configurar e iniciar la partida."""

    def __init__(self, data: dict[str, Any]) -> None:
        """Inicializa la tarea de empezar partida.

        Args:
            data: Datos de configuración de la partida.

        """
        super().__init__(data)
        self._segundos = data.get("segundos")
        self._paises_para_victoria = data.get("paises_para_victoria")
        self._objetivos_secretos = data.get("objetivos_secretos", False)
        self._misiles_habilitados = data.get("misiles_habilitados", False)
        self._action_name = "empezar"

    def _execute(self, client: Any, context: GameContext) -> None:  # noqa: ARG002
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
    """Tarea para seleccionar el color de un jugador."""

    def __init__(self, data: dict[str, Any]) -> None:
        """Inicializa la tarea de seleccionar color.

        Args:
            data: Datos con el color seleccionado.

        """
        super().__init__(data)
        self._color = data.get("color")
        self._action_name = "seleccionar_color"

    def _execute(self, client: Any, context: GameContext) -> None:  # noqa: ARG002
        client.cambiar_color(self._color)
        client.server.enviar_colores_asignados()


class ServerTaskEmpezarPartida(IServerTask):
    """Tarea para iniciar la partida después de la configuración."""

    def __init__(self, data: dict[str, Any]) -> None:
        """Inicializa la tarea de empezar partida.

        Args:
            data: Datos del mensaje (vacío para esta tarea).

        """
        super().__init__(data)
        self._action_name = "empezar_partida"

    def _execute(self, client: Any, context: GameContext) -> None:  # noqa: ARG002
        if client.server.estado.empezar_partida():
            client.server.enviar_estado()
            client.server.empezar_partida()
        else:
            LOGGER.warning(
                "No se pudo empezar la partida desde el estado %s",
                client.server.estado.estado_actual(),
            )


class ServerTaskSetUsername(IServerTask):
    """Tarea para establecer el nombre de usuario de un cliente."""

    def __init__(self, data: dict[str, Any]) -> None:
        """Inicializa la tarea de establecer username.

        Args:
            data: Datos con el nombre de usuario.

        """
        super().__init__(data)
        self._username = data.get("username")
        self._action_name = "set_username"

    def _execute(self, client: Any, context: GameContext) -> None:
        if self._username and isinstance(self._username, str):
            # Verificar si el username ya está en uso por otro cliente
            for other_client in context.dame_clientes():
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
    """Tarea para agregar unidades a un país."""

    def _validate_field_not_none(self, field_value: Any, field_name: str) -> None:
        """Valida que un campo no sea None.

        Args:
            field_value: Valor del campo a validar.
            field_name: Nombre del campo para el mensaje de error.

        Raises:
            ValidationError: Si el campo es None.

        """
        if field_value is None:
            error_msg = f"{field_name} no especificado"
            raise ValidationError(error_msg)

    def __init__(self, data: dict[str, Any]) -> None:
        """Inicializa la tarea de agregar unidad.

        Args:
            data: Datos con país, tipo de unidad y cantidad.

        """
        super().__init__(data)
        self._pais: str | None = data.get("pais")
        self._tipo_unidad: str | None = data.get("tipo_unidad")
        self._cantidad = data.get("cantidad", 1)  # Por defecto 1 si no se especifica
        self._action_name = "agregar_unidad"

    def _validate_units_available(self, turno_actual: Any, cantidad: int) -> None:
        """Valida que haya suficientes unidades disponibles.

        Args:
            turno_actual: Turno actual del juego.
            cantidad: Cantidad de unidades requeridas.

        Raises:
            ValidationError: Si no hay suficientes unidades disponibles.

        """
        if (
            not hasattr(turno_actual, "cant_unidades")
            or turno_actual.cant_unidades() < cantidad
        ):
            msg = (
                f"No hay suficientes unidades disponibles para agregar "
                f"{cantidad} unidades"
            )
            raise ValidationError(msg)

    def _execute(self, client: Any, context: GameContext) -> None:
        try:
            # Validar que los datos requeridos estén presentes
            self._validate_field_not_none(self._pais, "País")
            self._validate_field_not_none(self._tipo_unidad, "Tipo de unidad")

            # Type narrowing: después de las validaciones, estos valores no son None
            if self._pais is None or self._tipo_unidad is None:
                return  # No debería llegar aquí, pero ayuda a MyPy

            # Validar turno y estado del juego
            TurnValidator.validate_turn(client, context.game)
            GameStateValidator.validate_game_started(context.game)

            # Validar propiedad del país
            CountryOwnershipValidator.validate_ownership(
                client, context.mapa, self._pais
            )

            # Validar tipo de unidad
            UnitTypeValidator.validate_unit_type(self._tipo_unidad, VALID_UNIT_TYPES)

            # Verificar que el jugador tenga suficientes unidades disponibles
            if context.game is None:
                return
            turno_actual = context.game.turno_actual()
            self._validate_units_available(turno_actual, self._cantidad)

        except ValidationError as e:
            client.transmisor.enviar_error_chat(e.mensaje)
            return

        # Obtener el turno actual para usar después
        if context.game is None:
            return
        turno_actual = context.game.turno_actual()

        # Agregar la unidad al país
        for _ in range(self._cantidad):
            context.mapa.agregar_una_unidad(self._pais)

            # Restar la unidad de las unidades generales disponibles
            if hasattr(turno_actual, "usar_unidad"):
                turno_actual.usar_unidad()

        msg = (
            f"Se agregaron {self._cantidad} unidad(es) de tipo {self._tipo_unidad}"
            f" en {self._pais}"
        )
        LOGGER.info(msg)

        # Notificar a todos los clientes sobre el cambio en el mapa
        context.enviar_mapa()

        # Actualizar las unidades disponibles en la interfaz del jugador
        context.enviar_unidades_disponibles()


class ServerTaskMoverUnidad(IServerTask):
    """Tarea para mover unidades entre países."""

    def __init__(self, data: dict[str, Any]) -> None:
        """Inicializa la tarea de mover unidad.

        Args:
            data: Datos con país de origen, destino y cantidad.

        """
        super().__init__(data)
        self._origen: str | None = data.get("origen")
        self._destino: str | None = data.get("destino")
        self._cantidad = data.get("cantidad", 1)  # Por defecto 1 si no se especifica
        self._action_name = "mover_unidad"

    def _validate_required_fields(self) -> None:
        """Valida que los campos requeridos estén presentes.

        Raises:
            ValidationError: Si algún campo requerido es None.

        """
        if self._origen is None:
            error_msg = "País de origen no especificado"
            raise ValidationError(error_msg)
        if self._destino is None:
            error_msg = "País de destino no especificado"
            raise ValidationError(error_msg)

    def _execute(self, client: Any, context: GameContext) -> None:
        try:
            # Validar que los datos requeridos estén presentes
            self._validate_required_fields()

            # Validar propiedad del país de origen
            # Type narrowing: después de las validaciones, estos valores no son None
            if self._origen is None or self._destino is None:
                return  # No debería llegar aquí, pero ayuda a MyPy

            CountryOwnershipValidator.validate_ownership(
                client, context.mapa, self._origen
            )

            # Validar adyacencia (antes de validar propiedad del destino)
            AdjacencyValidator.validate_adjacent(
                context.mapa, self._origen, self._destino
            )

            # Validar propiedad del país de destino
            CountryOwnershipValidator.validate_ownership(
                client, context.mapa, self._destino
            )

            # Validar suficientes unidades para mover
            UnitValidator.validate_sufficient_units_to_move(
                context.mapa, self._origen, self._cantidad
            )

        except ValidationError as e:
            client.transmisor.enviar_error_chat(e.mensaje)
            return

        # Mover las unidades
        context.mapa.mover(self._origen, self._destino, self._cantidad)
        LOGGER.info(
            "Se movieron %s unidades de %s a %s",
            self._cantidad,
            self._origen,
            self._destino,
        )

        # Notificar a todos los clientes sobre el cambio en el mapa
        context.enviar_mapa()


class ServerTaskAtacar(IServerTask):
    """Tarea para procesar ataques entre países."""

    def _validate_required_fields(self) -> None:
        """Valida que los campos requeridos estén presentes.

        Raises:
            ValidationError: Si algún campo requerido es None.

        """
        if self._origen is None:
            error_msg = "País de origen no especificado"
            raise ValidationError(error_msg)
        if self._destino is None:
            error_msg = "País de destino no especificado"
            raise ValidationError(error_msg)

    def __init__(self, data: dict[str, Any]) -> None:
        """Inicializa la tarea de atacar.

        Args:
            data: Datos con país de origen, destino y cantidad de unidades.

        """
        super().__init__(data)
        self._origen: str | None = data.get("origen")
        self._destino: str | None = data.get("destino")
        self._cantidad_unidades = data.get("cantidad_unidades")
        self._action_name = "atacar"

    def _execute(self, client: Any, context: GameContext) -> None:
        try:
            # Validar que los datos requeridos estén presentes
            self._validate_required_fields()

            # Type narrowing: después de las validaciones, estos valores no son None
            if self._origen is None or self._destino is None:
                return  # No debería llegar aquí, pero ayuda a MyPy

            # Validar estado del juego
            GameStateValidator.validate_game_started(context.game)

            # Validar restricciones de ataque (antes de validar turno)
            if context.game is None:
                return
            AttackRestrictionValidator.validate_not_first_turns(context.game)

            # Validar turno
            TurnValidator.validate_turn(client, context.game)

            # Validar propiedad del país de origen
            CountryOwnershipValidator.validate_ownership(
                client, context.mapa, self._origen
            )

            # Validar que el destino NO sea del mismo jugador
            CountryOwnershipValidator.validate_not_own_country(
                client, context.mapa, self._destino
            )

            # Validar adyacencia
            AdjacencyValidator.validate_adjacent(
                context.mapa, self._origen, self._destino
            )

            # Validar unidades mínimas para atacar
            UnitValidator.validate_min_units(
                context.mapa,
                self._origen,
                MIN_UNITS_FOR_ATTACK,
                f"Necesitas al menos {MIN_UNITS_FOR_ATTACK} unidades en "
                f"{self._origen} para atacar",
            )

        except ValidationError as e:
            client.transmisor.enviar_error_chat(e.mensaje)
            return

        # Logging del estado antes del ataque
        unidades_origen = context.mapa.cantidad_unidades(self._origen)
        unidades_destino = context.mapa.cantidad_unidades(self._destino)
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
        if context.game is None:
            return
        info_batalla = context.game.atacar(
            self._origen, self._destino, self._cantidad_unidades
        )

        # Logging del estado después del ataque
        unidades_origen_post = context.mapa.cantidad_unidades(self._origen)
        unidades_destino_post = context.mapa.cantidad_unidades(self._destino)
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

        # Enviar mapa actualizado a todos los clientes
        context.enviar_mapa()

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
        context.enviar_resultado_batalla(batalla_data)

        # Marcar que el jugador conquistó un país en este turno
        # (para poder reclamar tarjeta)
        if info_batalla["conquistado"]:
            LOGGER.info(
                "%s conquistó %s - puede reclamar tarjeta",
                client.username(),
                self._destino,
            )
            # Marcar al jugador como elegible para reclamar tarjeta
            if context.game is not None:
                context.game.marcar_jugador_puede_reclamar(client)
        # (esto se podría implementar más adelante)


class ServerTaskFinalizarTurno(IServerTask):
    """Tarea para finalizar el turno de un jugador."""

    def __init__(self, data: dict[str, Any]) -> None:
        """Inicializa la tarea de finalizar turno.

        Args:
            data: Datos del mensaje (vacío para esta tarea).

        """
        super().__init__(data)
        self._action_name = "finalizar_turno"

    def _execute(self, client: Any, context: GameContext) -> None:
        try:
            TurnValidator.validate_turn(client, context.game)
        except ValidationError as e:
            client.transmisor.enviar_error_chat(e.mensaje)
            return

        # Limpiar elegibilidad para reclamar tarjetas del turno anterior
        if context.game is not None:
            context.game.limpiar_elegibilidad_reclamar()

            # Finalizar el turno actual
            context.game.finalizar_turno()

        # Notificar a todos los clientes sobre el cambio de turno
        context.enviar_turno_actual()
        context.enviar_mapa()


class ServerTaskSolicitarTarjetas(IServerTask):
    """Tarea para solicitar las tarjetas del jugador."""

    def __init__(self, data: dict[str, Any]) -> None:
        """Inicializa la tarea de solicitar tarjetas.

        Args:
            data: Datos del mensaje (vacío para esta tarea).

        """
        super().__init__(data)
        # No necesita validación de estado específica

    def _execute(self, client: Any, context: GameContext) -> None:
        """Envía las tarjetas del jugador al cliente que las solicita."""
        context.enviar_tarjetas_jugador(client)


class ServerTaskReclamarTarjeta(IServerTask):
    """Tarea para reclamar una tarjeta después de conquistar un país."""

    def __init__(self, data: dict[str, Any]) -> None:
        """Inicializa la tarea de reclamar tarjeta.

        Args:
            data: Datos del mensaje (vacío para esta tarea).

        """
        super().__init__(data)
        self._action_name = "reclamar_tarjeta"

    def _execute(self, client: Any, context: GameContext) -> None:
        """Reclama una tarjeta si el jugador conquistó un país en este turno."""
        # Verificar que el juego haya comenzado
        if context.game is None:
            client.transmisor.enviar_error_chat("El juego no ha comenzado")
            return

        # Verificar que sea el turno del jugador
        turno_actual = context.game.turno_actual()
        if turno_actual.jugador_actual() != client:
            client.transmisor.enviar_error_chat("No es tu turno")
            return

        # Verificar que el jugador pueda reclamar tarjeta (conquistó país en este turno)
        if not context.game.puede_reclamar_tarjeta(client):
            client.transmisor.enviar_error_chat(
                "No has conquistado ningún país en este turno"
            )
            return

        # Asignar la tarjeta
        LOGGER.info("Asignando tarjeta a %s por reclamación manual", client.username())
        context.game.dame_una_tarjeta(client)

        # Remover al jugador de la lista de elegibles (solo una tarjeta por turno)
        context.game.reclamar_tarjeta_jugador(client)

        # Enviar tarjetas actualizadas al cliente
        context.enviar_tarjetas_jugador(client)

        # Notificar éxito
        client.transmisor.enviar_sistema("Tarjeta reclamada exitosamente")


class ServerTaskCanjeEspecial(IServerTask):
    """Tarea para realizar un canje especial (país + tarjeta por 2 unidades)."""

    def __init__(self, data: dict[str, Any]) -> None:
        """Inicializa la tarea de canje especial.

        Args:
            data: Datos con el país para el canje.

        """
        super().__init__(data)
        self._pais = data.get("pais")
        self._action_name = "canje_especial"

    def _execute(self, client: Any, context: GameContext) -> None:
        """Ejecuta el canje especial de país + tarjeta por 2 unidades."""
        if context.game is None:
            client.transmisor.enviar_error_chat("El juego no ha comenzado")
            return

        # Validar que el país esté especificado
        if self._pais is None:
            client.transmisor.enviar_error_chat("País no especificado")
            return

        mapa = context.game.mapa()
        mazo = context.game.mazo()

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

        # 2. Agregar unidades al país
        for _ in range(SPECIAL_EXCHANGE_UNITS):
            mapa.agregar_una_unidad(self._pais)

        # 3. Notificar a todos los clientes sobre el cambio en el mapa
        context.enviar_mapa()

        # 4. Enviar notificación específica del canje especial
        client.transmisor.enviar_canje_especial(self._pais, SPECIAL_EXCHANGE_UNITS)

        # 5. Actualizar tarjetas del jugador
        context.enviar_tarjetas_jugador(client)

        # 6. Notificar éxito
        client.transmisor.enviar_sistema(
            f"Canje especial realizado: +{SPECIAL_EXCHANGE_UNITS} "
            f"unidades en {self._pais}"
        )


class ServerTaskCanjearMisil(IServerTask):
    """Tarea para canjear unidades por un misil."""

    def _validate_field_not_none(self, field_value: Any, field_name: str) -> None:
        """Valida que un campo no sea None.

        Args:
            field_value: Valor del campo a validar.
            field_name: Nombre del campo para el mensaje de error.

        Raises:
            ValidationError: Si el campo es None.

        """
        if field_value is None:
            error_msg = f"{field_name} no especificado"
            raise ValidationError(error_msg)

    def __init__(self, data: dict[str, Any]) -> None:
        """Inicializa la tarea de canjear misil.

        Args:
            data: Datos con el país donde canjear el misil.

        """
        super().__init__(data)
        self._pais: str | None = data.get("pais")
        self._action_name = "canjear_misil"

    def _validate_missiles_enabled(self, server: Any) -> None:
        """Valida que los misiles estén habilitados.

        Args:
            server: Instancia del servidor.

        Raises:
            ValidationError: Si los misiles no están habilitados.

        """
        if not server.misiles_habilitados():
            msg = "Los misiles no están habilitados en esta partida"
            raise ValidationError(msg)

    def _execute(self, client: Any, context: GameContext) -> None:
        try:
            # 1. Verificar que los misiles estén habilitados
            self._validate_missiles_enabled(client.server)

            # 2. Validar que el país esté especificado
            self._validate_field_not_none(self._pais, "País")

            # Type narrowing: después de la validación, este valor no es None
            if self._pais is None:
                return  # No debería llegar aquí, pero ayuda a MyPy

            # 3. Validar turno y estado del juego
            TurnValidator.validate_turn(client, context.game)
            GameStateValidator.validate_game_started(context.game)

            # 4. Validar propiedad del país
            CountryOwnershipValidator.validate_ownership(
                client, context.mapa, self._pais
            )

            # 5. Validar unidades mínimas para canjear misil
            UnitValidator.validate_min_units(
                context.mapa,
                self._pais,
                MISSILE_UNIT_COST,
                (
                    f"Se requieren al menos {MISSILE_UNIT_COST} unidades "
                    f"para canjear un misil. {self._pais} tiene "
                    f"{context.mapa.cantidad_unidades(self._pais)} unidades."
                ),
            )

        except ValidationError as e:
            client.transmisor.enviar_error_chat(e.mensaje)
            return

        # 5. Restar las unidades del país
        for _ in range(MISSILE_UNIT_COST):
            context.mapa.restar_una_unidad(self._pais)

        # 7. Agregar misil al país
        context.mapa.agregar_misil(self._pais)
        cantidad_misiles = context.mapa.cantidad_misiles(self._pais)

        # 8. Notificar cambios a todos los clientes
        context.enviar_misil_agregado(self._pais, cantidad_misiles)
        # Actualizar el mapa completo para mostrar cambios en unidades
        context.enviar_mapa()

        # 10. Notificar éxito al jugador
        client.transmisor.enviar_sistema(
            f"Misil canjeado en {self._pais}: -{MISSILE_UNIT_COST} unidades, +1 misil. "
            f"Total: {cantidad_misiles} misiles"
        )


class ServerTaskLanzarMisil(IServerTask):
    """Tarea para lanzar un misil desde un país hacia otro."""

    def __init__(self, data: dict[str, Any]) -> None:
        """Inicializa la tarea de lanzar misil.

        Args:
            data: Datos con país de origen y destino del misil.

        """
        super().__init__(data)
        self._pais_origen = data.get("pais_origen")
        self._pais_destino = data.get("pais_destino")
        self._action_name = "lanzar_misil"

    def _execute(self, client: Any, context: GameContext) -> None:
        # Validar que los países estén especificados
        if self._pais_origen is None or self._pais_destino is None:
            client.transmisor.enviar_error_chat(
                "País de origen o destino no especificado"
            )
            return

        # Validar precondiciones y permisos
        error = self._validar_lanzamiento_misil(client, context)
        if error:
            client.transmisor.enviar_error_chat(error)
            return

        # Calcular distancia y daño
        distancia = context.mapa.calcular_distancia(
            self._pais_origen, self._pais_destino
        )
        dano = context.mapa.calcular_dano_misil(distancia)

        # Aplicar el daño y usar el misil
        for _ in range(dano):
            context.mapa.restar_una_unidad(self._pais_destino)
        context.mapa.usar_misil(self._pais_origen)

        # Notificar resultados
        self._notificar_resultado_misil(client, distancia, dano)

        # Notificar cambios en el mapa
        context.enviar_mapa()

    def _validar_lanzamiento_misil(
        self, client: Any, context: GameContext
    ) -> str | None:
        """Valida todas las condiciones para lanzar un misil.

        Args:
            client: Cliente que intenta lanzar el misil.
            context: Contexto de acceso a recursos del juego.

        Returns:
            str | None: Mensaje de error si hay alguna validación fallida,
            None si todo es válido.

        """
        # Validar configuración y estado del juego
        error = self._validar_estado_juego(client, context)
        if error:
            return error

        # Validar posesión y disponibilidad
        error = self._validar_posesion_misil(client, context)
        if error:
            return error

        # Validar distancia y daño
        return self._validar_distancia_dano(client, context)

    def _validar_estado_juego(self, client: Any, context: GameContext) -> str | None:
        """Valida que el juego esté en estado correcto.

        Args:
            client: Cliente que intenta lanzar el misil.
            context: Contexto de acceso a recursos del juego.

        Returns:
            Mensaje de error si la validación falla, None si es válido.

        """
        if not context.misiles_habilitados():
            return "Los misiles no están habilitados en esta partida"

        if context.game is None:
            return "El juego no ha comenzado"

        turno_actual = context.game.turno_actual()
        if turno_actual.jugador_actual() != client:
            return "No es tu turno"

        return None

    def _validar_posesion_misil(self, client: Any, context: GameContext) -> str | None:
        """Valida posesión de países y disponibilidad de misiles.

        Args:
            client: Cliente que intenta lanzar el misil.
            context: Contexto de acceso a recursos del juego.

        Returns:
            Mensaje de error si la validación falla, None si es válido.

        """
        if self._pais_origen is None or self._pais_destino is None:
            return "País de origen o destino no especificado"

        if context.mapa.ocupado_por(self._pais_origen) != client.userid():
            return f"No eres dueño de {self._pais_origen}"

        if context.mapa.cantidad_misiles(self._pais_origen) == 0:
            return f"{self._pais_origen} no tiene misiles disponibles"

        if context.mapa.ocupado_por(self._pais_destino) == client.userid():
            return "No puedes lanzar misiles a tus propios países"

        return None

    def _validar_distancia_dano(
        self,
        client: Any,  # noqa: ARG002
        context: GameContext,
    ) -> str | None:
        """Valida distancia y daño del misil.

        Args:
            client: Cliente que intenta lanzar el misil.
            context: Contexto de acceso a recursos del juego.

        Returns:
            Mensaje de error si la validación falla, None si es válido.

        """
        if self._pais_origen is None or self._pais_destino is None:
            return "País de origen o destino no especificado"

        distancia = context.mapa.calcular_distancia(
            self._pais_origen, self._pais_destino
        )

        if distancia == -1:
            return f"No hay camino entre {self._pais_origen} y {self._pais_destino}"

        if distancia > MISSILE_MAX_DISTANCE:
            return (
                f"El objetivo está demasiado lejos (distancia: {distancia}). "
                f"Máximo: {MISSILE_MAX_DISTANCE} saltos"
            )

        dano = context.mapa.calcular_dano_misil(distancia)
        unidades_destino = context.mapa.cantidad_unidades(self._pais_destino)
        if unidades_destino <= dano:
            return (
                f"El ataque dejaría a {self._pais_destino} sin unidades. "
                f"El país debe conservar al menos {MIN_UNITS_TO_LEAVE} "
                f"unidad. Unidades actuales: {unidades_destino}, Daño: {dano}"
            )

        return None

    def _notificar_resultado_misil(
        self, client: Any, distancia: int, dano: int
    ) -> None:
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
