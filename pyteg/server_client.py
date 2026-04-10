"""Módulo para el cliente del servidor."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

from pyteg.exception import EstadoInvalidoError, MensajeNoValidoError
from pyteg.logger import get_logger
from pyteg.server_tasks_manager import ServerTaskManager
from pyteg.server_transmisor import ServerTransmisor

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

    def recibir(self) -> list[str]:
        """Recibe datos del cliente.

        Returns:
            Lista de datos recibidos.

        """
        result = self._conn.receiver()
        if isinstance(result, list):
            return [str(item) for item in result]
        return []

    def cerrar(self) -> None:
        """Cierra la conexión del cliente."""
        self._conn.close()

    def run(self) -> None:
        """Ejecuta el ciclo principal del cliente.

        Maneja la recepción de datos y la ejecución de tareas.
        """
        vivo = True

        self.server.enviar_userid()
        self.server.enviar_username()

        if self.es_admin():
            self.transmisor.sos_admin()

        self.transmisor.enviar_colores(self.server.color.colores())
        self.server.enviar_colores_asignados()
        self.transmisor.enviar_estado(self.server.estado.estado_actual())

        while vivo:
            datas = self.recibir()

            if not datas or (len(datas) == 1 and not datas[0]):
                vivo = False
                continue

            for data in datas:
                try:
                    data_json = json.loads(data)
                    self.ejecutar_mensaje(data_json)
                except json.JSONDecodeError:
                    print(f"Mensaje no JSON recibido: {data}")

        # Cuando el cliente se desconecta, quitarlo del servidor
        self._logger.info(
            "Cliente %s (%s) se ha desconectado", self._user_id, self._username
        )
        self.server.quitarme(self._user_id)

    def ejecutar_mensaje(self, data: dict[str, Any]) -> None:
        """Ejecuta una tarea basada en el mensaje recibido.

        :param data: Datos del mensaje en formato JSON
        """
        task = ServerTaskManager.msg_to_task(data)
        try:
            task.run(self)
        except MensajeNoValidoError:
            self._logger.exception("Mensaje no válido del cliente %s", self._user_id)
        except EstadoInvalidoError as e:
            self._logger.warning("Error de estado del cliente %s: %s", self._user_id, e)
            # Opcionalmente, enviar el error al cliente
            if hasattr(self.server, "enviar_error"):
                self.server.enviar_error(str(e))

        mensaje = data.get("mensaje")
        if mensaje:
            self._logger.debug(
                "Mensaje recibido del cliente %s: %s", self._user_id, mensaje
            )
