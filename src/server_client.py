import json

from src.exception import MensajeNoValidoError
from src.server_tasks_manager import ServerTaskManager
from src.server_transmisor import ServerTransmisor


class Client:
    def __init__(self, user_id, conn, server, username, soy_admin):
        """
        Inicializa un nuevo cliente.

        :param user_id: ID del usuario
        :param conn: Conexión del cliente
        :param server: Instancia del servidor
        :param username: Nombre de usuario
        :param soy_admin: Indica si el usuario es administrador
        """
        self._user_id = user_id
        self._conn = conn
        self.server = server
        self._username = username
        self._soy_admin = soy_admin
        self._color = None
        self.transmisor = ServerTransmisor(self._conn)

    def asignar_color(self, color):
        """
        Asigna un color al cliente.

        :param color: Color a asignar
        """
        self._color = color

    def es_admin(self):
        """
        Verifica si el cliente es administrador.

        :return: True si es administrador, False en caso contrario
        """
        return self._soy_admin

    def cambiar_color(self, color):
        """
        Cambia el color del cliente.

        :param color: Nuevo color a asignar
        """
        self.server.color.asignar_color(self, color)

    def color_actual(self):
        """
        Obtiene el color actual del cliente.

        :return: Color actual del cliente
        """
        return self._color

    def userid(self):
        """
        Obtiene el ID de usuario del cliente.

        :return: ID de usuario del cliente
        """
        return self._user_id

    def username(self):
        """
        Obtiene el nombre de usuario del cliente.

        :return: Nombre de usuario del cliente
        """
        return self._username

    def enviar(self, data):
        """
        Envía datos al cliente.

        :param data: Datos a enviar
        """
        self._conn.send(data)

    def recibir(self):
        """
        Recibe datos del cliente.

        :return: Datos recibidos
        """
        return self._conn.receiver()

    def cerrar(self):
        """
        Cierra la conexión del cliente.
        """
        self._conn.close()

    def run(self):
        """
        Ejecuta el ciclo principal del cliente, manejando la recepción de datos
        y la ejecución de tareas.
        """
        vivo = True

        self.server.enviar_userid()
        self.server.enviar_username()

        if self.es_admin():
            self.transmisor.sos_admin()

        self.transmisor.enviar_colores(self.server.color.colores())
        self.transmisor.enviar_estado(self.server.estado.estado_actual())

        while vivo:
            data = self.recibir()

            if not data:
                vivo = False
                continue

            data_json = json.loads(data)
            self.ejecutar_mensaje(data_json)

    def ejecutar_mensaje(self, data):
        """
        Ejecuta una tarea basada en el mensaje recibido.

        :param data: Datos del mensaje en formato JSON
        """
        task = ServerTaskManager.msg_to_task(data)
        try:
            task.run(self)
        except MensajeNoValidoError as e:
            print(f"Error: {e}")

        mensaje = data.get("mensaje")
        if mensaje:
            print(mensaje)
