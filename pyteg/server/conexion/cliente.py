"""Módulo para el cliente del servidor."""

from __future__ import annotations

import json
import secrets
import threading
from collections import OrderedDict
from copy import deepcopy
from typing import TYPE_CHECKING, Any

from pyteg.logger import get_logger
from pyteg.protocol_validation import MessageValidationError, validate_server_command
from pyteg.server.conexion.transmisor import ServerTransmisor

if TYPE_CHECKING:
    from pyteg.colores import IColor


class Client:
    """Representa un cliente conectado al servidor."""

    def __init__(  # noqa: PLR0913
        self,
        user_id: int,
        conn: Any,
        server: Any,
        username: str,
        *,
        soy_admin: bool,
        reconnect_token: str | None = None,
    ) -> None:
        """Inicializa un nuevo cliente.

        :param user_id: ID del usuario
        :param conn: Conexión del cliente
        :param server: Instancia del servidor
        :param username: Nombre de usuario
        :param soy_admin: Indica si el usuario es administrador
        """
        self._user_id = user_id
        self._conn = conn
        self.server: Any = server
        self._username = username
        self._soy_admin = soy_admin
        self._reconnect_token = reconnect_token or secrets.token_urlsafe(32)
        self._pending_reconnect = False
        self._handshake_status: bool | None = None
        self._color: IColor | None = None
        self.transmisor = ServerTransmisor(self._conn)
        self._logger = get_logger(f"server.client.{user_id}")
        self._cleanup_lock = threading.Lock()
        self._cleanup_completed = False
        self._command_results: OrderedDict[str, dict[str, Any]] = OrderedDict()
        self._command_payloads: OrderedDict[str, dict[str, Any]] = OrderedDict()

    def asignar_color(self, color: IColor | None) -> None:
        """Asigna un color al cliente.

        :param color: Color a asignar
        """
        self._color = color

    def es_admin(self) -> bool:
        """Verifica si el cliente es administrador.

        Returns:
            True si es administrador, False en caso contrario.

        """
        return self._soy_admin

    def asignar_admin(self, es_admin: bool) -> None:  # noqa: FBT001
        """Actualiza el administrador de la sala sin cambiar su identidad."""
        self._soy_admin = bool(es_admin)

    def reconnect_token(self) -> str:
        """Devuelve el token privado que permite recuperar la sesión.

        Returns:
            Token privado de la identidad.

        """
        return self._reconnect_token

    def set_reconnect_token(self, token: str) -> None:
        """Actualiza el token después de recuperar una identidad."""
        self._reconnect_token = token

    def marcar_reconexion_pendiente(self, *, pendiente: bool = True) -> None:
        """Marca la conexión como pendiente de autenticación de reconexión."""
        self._pending_reconnect = pendiente

    def es_reconexion_pendiente(self) -> bool:
        """Indica si la conexión todavía no recuperó una identidad.

        Returns:
            ``True`` mientras espera el comando de reconexión.

        """
        return self._pending_reconnect

    def handshake_status(self) -> bool | None:
        """Estado de la negociación del protocolo.

        Returns:
            ``True`` si el cliente fue aceptado, ``False`` si fue rechazado y
            ``None`` mientras todavía no envió un ``hello`` válido.

        """
        return self._handshake_status

    def marcar_handshake(self, accepted: bool) -> None:  # noqa: FBT001
        """Guarda el resultado de la negociación del protocolo."""
        self._handshake_status = bool(accepted)

    def command_result(self, command_id: str) -> dict[str, Any] | None:
        """Obtiene un resultado cacheado para un reintento.

        Returns:
            Resultado anterior o ``None`` si es un comando nuevo.

        """
        result = self._command_results.get(command_id)
        if result is not None:
            self._command_results.move_to_end(command_id)
            if command_id in self._command_payloads:
                self._command_payloads.move_to_end(command_id)
            return deepcopy(result)
        return None

    def command_payload(self, command_id: str) -> dict[str, Any] | None:
        """Obtiene el payload asociado a un resultado cacheado.

        Returns:
            Payload sin ``command_id`` o ``None`` si no hay registro.

        """
        payload = self._command_payloads.get(command_id)
        if payload is None:
            return None
        self._command_payloads.move_to_end(command_id)
        return deepcopy(payload)

    def remember_command_result(
        self,
        command_id: str,
        result: dict[str, Any],
        payload: dict[str, Any] | None = None,
        *,
        limit: int = 256,
    ) -> None:
        """Guarda resultados recientes con retención acotada."""
        self._command_results[command_id] = deepcopy(result)
        self._command_results.move_to_end(command_id)
        if payload is not None:
            payload_without_id = {
                key: value for key, value in payload.items() if key != "command_id"
            }
            self._command_payloads[command_id] = deepcopy(payload_without_id)
            self._command_payloads.move_to_end(command_id)
        while len(self._command_results) > limit:
            expired_id, _ = self._command_results.popitem(last=False)
            self._command_payloads.pop(expired_id, None)

    def export_command_results(self) -> dict[str, dict[str, Any]]:
        """Exporta la caché para transferirla durante una reconexión.

        Returns:
            Copia de los resultados recientes.

        """
        return {key: deepcopy(value) for key, value in self._command_results.items()}

    def import_command_results(self, values: dict[str, dict[str, Any]]) -> None:
        """Restaura resultados de la conexión histórica."""
        for key, value in values.items():
            self._command_results[key] = deepcopy(value)

    def export_command_cache(self) -> dict[str, dict[str, Any]]:
        """Exporta resultados y payloads para una reconexión idempotente.

        Returns:
            Copia de los registros recientes indexados por ``command_id``.

        """
        return {
            command_id: {
                "result": deepcopy(result),
                "payload": deepcopy(self._command_payloads.get(command_id, {})),
            }
            for command_id, result in self._command_results.items()
        }

    def import_command_cache(self, values: dict[str, dict[str, Any]]) -> None:
        """Restaura resultados y payloads cacheados de una sesión histórica."""
        for command_id, record in values.items():
            result = record.get("result")
            payload = record.get("payload")
            if not isinstance(result, dict):
                continue
            self._command_results[command_id] = deepcopy(result)
            if isinstance(payload, dict):
                self._command_payloads[command_id] = deepcopy(payload)

    def limpiar_cache_comandos(self) -> None:
        """Descarta resultados idempotentes al comenzar una nueva partida."""
        self._command_results.clear()
        self._command_payloads.clear()

    def reasignar_userid(self, user_id: int) -> None:
        """Reasigna el identificador tras validar una reconexión."""
        self._user_id = int(user_id)
        self._soy_admin = self._user_id == 1

    def cambiar_color(self, color: str) -> None:
        """Cambia el color del cliente.

        :param color: Nuevo color a asignar
        """
        self.server.color.asignar_color(self, color)

    def set_username(self, username: str) -> None:
        """Establece el nombre de usuario del cliente.

        :param username: Nuevo nombre de usuario
        """
        self._username = username

    def color_actual(self) -> IColor | None:
        """Obtiene el color actual del cliente.

        Returns:
            Color actual del cliente.

        """
        return self._color

    def userid(self) -> int:
        """Obtiene el ID de usuario del cliente.

        Returns:
            ID de usuario del cliente.

        """
        return self._user_id

    def username(self) -> str:
        """Obtiene el nombre de usuario del cliente.

        Returns:
            Nombre de usuario del cliente.

        """
        return self._username

    def enviar(self, data: bytes) -> None:
        """Envía datos al cliente.

        :param data: Datos a enviar
        """
        self._conn.send(data)

    def recibir(self) -> list[str] | None:
        """Recibe datos del cliente.

        Returns:
            Lista de tramas completas, ``[]`` cuando queda una trama parcial, o
            ``None`` si la conexión terminó.

        """
        result = self._conn.receiver()
        if result is None:
            return None
        return [str(item) for item in result]

    def cerrar(self, *, flush_outgoing: bool = False) -> None:
        """Libera una conexión y su registro de forma idempotente.

        El objeto conserva identidad, nombre y color para que una partida ya
        iniciada siga teniendo sus jugadores y territorios aunque el socket
        asociado se haya cerrado.

        Args:
            flush_outgoing: Entrega, dentro de un plazo, el error terminal ya
                encolado antes de cerrar el socket.

        """
        with self._cleanup_lock:
            if self._cleanup_completed:
                return
            self._cleanup_completed = True

        try:
            if flush_outgoing:
                self._conn.flush_outgoing()
            self._conn.close()
        finally:
            self.server.quitarme(self._user_id, self)

    def run(self) -> None:  # noqa: C901, PLR0912
        """Ejecuta el ciclo principal del cliente.

        Maneja la recepción de datos y el encolado de tareas validadas.
        """
        try:
            protocol_version = getattr(self.server, "protocol_version", "1")
            if not isinstance(protocol_version, str):
                protocol_version = "1"
            theme = getattr(self.server, "theme", "classic")
            if not isinstance(theme, str):
                theme = "classic"
            map_hash_getter = getattr(self.server, "map_hash", None)
            map_hash = map_hash_getter() if callable(map_hash_getter) else "legacy"
            if not isinstance(map_hash, str) or not map_hash:
                map_hash = "legacy"
            self.transmisor.enviar_hello(
                protocol_version,
                theme,
                map_hash,
                capabilities=["snapshots", "command_results", "reconnect"],
                rules=["validated_phases", "one_card_per_turn"],
            )
            if self.es_reconexion_pendiente():
                # Una conexión pendiente no debe anunciar su ID temporal ni
                # consumir colores antes de autenticarse.
                self.transmisor.enviar_userid(self.userid())
                self.transmisor.enviar_session_token(
                    self.userid(), self.reconnect_token()
                )
                self.transmisor.enviar_estado(self.server.estado.estado_actual())
            else:
                self.server.enviar_userid()
                self.transmisor.enviar_session_token(
                    self.userid(), self.reconnect_token()
                )
                self.server.enviar_username()

                if self.es_admin():
                    self.transmisor.sos_admin()

                self.transmisor.enviar_colores(self.server.color.colores())
                self.server.enviar_colores_asignados()
                self.transmisor.enviar_estado(self.server.estado.estado_actual())

            while True:
                datas = self.recibir()
                if datas is None:
                    break

                for data in datas:
                    if not data:
                        continue
                    try:
                        data_json = json.loads(data)
                        self.ejecutar_mensaje(data_json)
                    except json.JSONDecodeError:
                        self._logger.warning("Mensaje no JSON recibido: %r", data)
                        self._enviar_error_protocolo(
                            "invalid_json", "El mensaje no contiene JSON válido"
                        )
        except Exception:
            self._logger.exception(
                "Fallo no recuperable en el cliente %s", self._user_id
            )
        finally:
            self._logger.info(
                "Cliente %s (%s) se ha desconectado", self._user_id, self._username
            )
            self.cerrar()

    def _enviar_error_protocolo(self, code: str, message: str) -> None:
        """Envía un error de protocolo sin interrumpir el lector TCP."""
        self.transmisor.enviar_error(code, message)

    def ejecutar_mensaje(self, data: object) -> None:
        """Valida y encola una tarea basada en el mensaje recibido.

        Args:
            data: Valor JSON recibido desde la conexión TCP.

        """
        try:
            validated_data = validate_server_command(data)
        except MessageValidationError as error:
            self._logger.warning(
                "Comando inválido de cliente %s: %s", self._user_id, error
            )
            self._enviar_error_protocolo(error.code, str(error))
            return

        mensaje = validated_data["mensaje"]
        if mensaje == "hello":
            # El handshake actualiza la capacidad de la conexión que se usa
            # para validar los siguientes frames. Procesarlo aquí, antes de
            # encolar el resto del buffer TCP, evita que un ``reconectar`` o
            # un comando posterior vea todavía el estado ``UNNEGOTIATED``.
            validar = getattr(self.server, "validar_handshake", None)
            if callable(validar):
                validar(self, dict(validated_data))
            else:
                self.marcar_handshake(True)  # noqa: FBT003
            return

        if mensaje != "hello" and self.handshake_status() is not True:
            self._enviar_error_protocolo(
                "handshake_required",
                "Esta conexión debe completar el handshake antes de enviar comandos.",
            )
            return

        if self.es_reconexion_pendiente() and mensaje != "reconectar":
            self._enviar_error_protocolo(
                "reconnect_required",
                "Esta conexión debe autenticarse con reconectar antes de enviar "
                "acciones.",
            )
            return

        self.server.encolar_comando(self, validated_data)

        mensaje = validated_data["mensaje"]
        if mensaje:
            self._logger.debug(
                "Mensaje recibido del cliente %s: %s", self._user_id, mensaje
            )
