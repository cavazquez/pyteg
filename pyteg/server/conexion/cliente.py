"""Módulo para el cliente del servidor."""

from __future__ import annotations

import json
import threading
from typing import TYPE_CHECKING, Any

from pyteg.logger import get_logger
from pyteg.protocol_validation import MessageValidationError, validate_server_command
from pyteg.server.conexion.transmisor import ServerTransmisor

if TYPE_CHECKING:
    from pyteg.colores import IColor


class Client:
    """Representa un cliente conectado al servidor."""

    def __init__(
        self, user_id: int, conn: Any, server: Any, username: str, *, soy_admin: bool
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
        self._color: IColor | None = None
        self.transmisor = ServerTransmisor(self._conn)
        self._logger = get_logger(f"server.client.{user_id}")
        self._cleanup_lock = threading.Lock()
        self._cleanup_completed = False

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

    def run(self) -> None:
        """Ejecuta el ciclo principal del cliente.

        Maneja la recepción de datos y el encolado de tareas validadas.
        """
        try:
            self.server.enviar_userid()
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

        self.server.encolar_comando(self, validated_data)

        mensaje = validated_data["mensaje"]
        if mensaje:
            self._logger.debug(
                "Mensaje recibido del cliente %s: %s", self._user_id, mensaje
            )
