from abc import ABC, abstractmethod

from PySide6.QtGui import QColor
from PySide6.QtWidgets import QMessageBox

from src.client import Client
from src.client_color import Color
from src.debug_logger import debug_logger


class IClientTask(ABC):
    @abstractmethod
    def run(self, main_window):
        pass


class ClientTaskNull(IClientTask):
    def __init__(self, data):
        self._msg = data.get("mensaje")

    def run(self, _):
        print(f"mensaje {self._msg} desconocido")


class ClientTaskChat(IClientTask):
    def __init__(self, data):
        self._msg = data.get("msg")

    def run(self, main_window):
        main_window.chat.append(self._msg)


class ClientTaskSerAdmin(IClientTask):
    def __init__(self, data):
        pass

    def run(self, main_window):
        main_window.client.ahora_es_admin()
        main_window.ventana_admin()


class ClientTaskEstado(IClientTask):
    def __init__(self, data):
        self._msg = data.get("estado")

    def run(self, main_window):
        print(f"Recibido cambio de estado: {self._msg}")

        # Actualizar el estado en la interfaz gráfica
        main_window.update_game_state(self._msg)

        if self._msg == "EsperarJugadores":
            print("Mostrando ventana de espera de jugadores")
            main_window.ventana_esperar_jugadores()
        elif self._msg == "JUGANDO":
            print("Cambiando a estado JUGANDO")
            # Cerrar la ventana de espera si está abierta
            if hasattr(main_window, "w") and main_window.w is not None:
                print("Cerrando ventana de espera...")
                try:
                    # Forzar el cierre de la ventana
                    main_window.w.close()
                    main_window.w.deleteLater()
                    main_window.w = None
                    print("Ventana de espera cerrada correctamente")
                except Exception as e:
                    print(f"Error al cerrar la ventana de espera: {e}")
            else:
                print("No hay ventana de espera abierta para cerrar")

            # Actualizar la lista de jugadores en la interfaz principal
            try:
                self.actualizar_lista_jugadores(main_window)
            except Exception as e:
                print(f"Error al actualizar lista de jugadores: {e}")

            # Forzar actualización de la interfaz
            if hasattr(main_window, "update"):
                main_window.update()

    def actualizar_lista_jugadores(self, main_window):
        """
        Actualiza la lista de jugadores en la interfaz de usuario.
        """
        # Obtener la lista de jugadores con sus colores
        jugadores = []
        for user_id, color in main_window.colores.colores_asignados().items():
            # Obtener el nombre de usuario del cliente
            client = main_window.client_by_id.get(user_id)
            if client:
                jugadores.append((client.username(), color))

        # Actualizar la lista de jugadores en la interfaz
        main_window.update_player_list(jugadores)


class ClientTaskColorAsignado(IClientTask):
    def __init__(self, data):
        self._msg = data

    def run(self, main_window):
        try:
            # Extraer el ID de usuario y el color del mensaje
            id_user = self._msg.get("id")
            if not id_user:
                print(
                    "Error: No se proporcionó ID de usuario"
                    "en el mensaje de color asignado"
                )
                return

            # Extraer los componentes de color
            r = self._msg.get("r", 0)
            g = self._msg.get("g", 0)
            b = self._msg.get("b", 0)

            print(f"Asignando color al jugador {id_user}: R={r}, G={g}, B={b}")

            # Crear el color y asignarlo al jugador
            color_data = {"r": r, "g": g, "b": b}
            main_window.colores.asignar(id_user, color_data)

            # Actualizar la lista de jugadores en la interfaz
            self.actualizar_lista_jugadores(main_window)

            # Actualizar la ventana de espera de jugadores si está abierta
            tiene_w = hasattr(main_window, "w") and main_window.w
            tiene_cargar_colores_asignados = hasattr(
                main_window.w, "cargar_colores_asignados"
            )
            if tiene_w and tiene_cargar_colores_asignados:
                main_window.w.cargar_colores_asignados()

            # Actualizar información del usuario actual si es su color
            if hasattr(main_window, "client") and main_window.client:
                mi_user_id = main_window.client.userid()
                debug_logger.log(
                    f"ClientTaskColorAsignado: Mi user_id: {mi_user_id}, "
                    f"Color asignado a: {id_user}"
                )
                if mi_user_id == id_user:
                    debug_logger.log(
                        "ClientTaskColorAsignado: ES MI COLOR, actualizando mi info"
                    )
                    if hasattr(main_window, "update_mi_jugador_info"):
                        main_window.update_mi_jugador_info()
                else:
                    debug_logger.log(
                        "ClientTaskColorAsignado: NO es mi color, no actualizo"
                    )

        except Exception as e:
            print(f"Error en ClientTaskColorAsignado: {e}")

    def actualizar_lista_jugadores(self, main_window):
        """
        Actualiza la lista de jugadores en la interfaz de usuario.
        """
        try:
            # Obtener la lista de jugadores con sus colores
            jugadores = []
            for user_id, color in main_window.colores.colores_asignados().items():
                # Obtener el nombre de usuario del cliente
                client = main_window.client_by_id.get(user_id)
                if client and hasattr(client, "username"):
                    jugadores.append((client.username(), color))
                    print(f"Jugador {client.username()} tiene color {color.getRgb()}")

            # Actualizar la lista de jugadores en la interfaz si el método existe
            if hasattr(main_window, "update_player_list"):
                main_window.update_player_list(jugadores)
        except Exception as e:
            print(f"Error al actualizar lista de jugadores: {e}")


class ClientTaskColor(IClientTask):
    def __init__(self, data):
        self._msg = data

    def run(self, main_window):
        self._msg.pop("mensaje")
        main_window.colores.agregar_color(Color(**self._msg))


class ClientTaskUserId(IClientTask):
    def __init__(self, data):
        self._msg = data

    def run(self, main_window):
        userid = int(self._msg.get("user_id"))
        debug_logger.log(f"ClientTaskUserId: Recibido user_id {userid}")

        # Solo establecer el ID del cliente actual si aún no tiene uno
        if not main_window.client.userid():
            debug_logger.log(
                f"ClientTaskUserId: Estableciendo {userid} como MI user_id"
            )
            main_window.client.set_userid(userid)
            # Actualizar información del usuario actual
            if hasattr(main_window, "update_mi_jugador_info"):
                main_window.update_mi_jugador_info()
        else:
            debug_logger.log(
                f"ClientTaskUserId: Ya tengo user_id {main_window.client.userid()}, "
                f"agregando {userid} a la lista"
            )

        # Siempre mantener información de todos los jugadores
        main_window.client_by_id[userid] = Client()
        main_window.client_by_id[userid].set_userid(userid)


class ClientTaskTurno(IClientTask):
    def __init__(self, data):
        self._msg = data

    def run(self, main_window):
        num_turno = int(self._msg.get("num_turno", 0))
        num_ronda = int(
            self._msg.get("num_ronda", 1)
        )  # Por defecto 1 si no se especifica

        # Obtener información del jugador actual
        jugador_actual_id = self._msg.get("jugador_actual_id")
        jugador_actual_nombre = self._msg.get("jugador_actual_nombre")
        jugador_actual_color = self._msg.get("jugador_actual_color")

        main_window.update_turno(
            num_turno,
            num_ronda,
            jugador_actual_id,
            jugador_actual_nombre,
            jugador_actual_color,
        )

        # Mostrar mensaje de inicio de turno en el chat
        main_window.chat.append(f"Turno {num_turno + 1} iniciado")

        # Solicitar actualización de unidades disponibles al servidor
        # Esto debería ser manejado por el servidor enviando un mensaje
        # de unidades_disponibles


class ClientTaskTiempo(IClientTask):
    def __init__(self, data):
        self._msg = data

    def run(self, main_window):
        tiempo = int(self._msg.get("tiempo", 0))
        # Solo mostrar el tiempo restante, la información del jugador
        # ya se muestra en la barra de estado con el cuadrado de color
        if tiempo > 0:
            # Determinar color basado en tiempo restante
            if tiempo > 20:  # Mucho tiempo - Verde
                color = "green"
            elif tiempo > 10:  # Poco tiempo - Amarillo/Naranja
                color = "orange"
            else:  # Muy poco tiempo - Rojo
                color = "red"

            main_window.update_status_bar(f"Tiempo restante: {tiempo}s", color=color)
        else:
            main_window.clear_status_bar()


class ClientTaskUsername(IClientTask):
    def __init__(self, data):
        self._msg = data

    def run(self, main_window):
        username = self._msg.get("username")
        userid = self._msg.get("user_id")

        # Actualizar el nombre de usuario
        # en el cliente principal si es el propio cliente
        if main_window.client.userid() == userid:
            main_window.client.set_username(username)

        # Actualizar el nombre de usuario en el diccionario de clientes
        if userid in main_window.client_by_id:
            main_window.client_by_id[userid].set_username(username)

        # Actualizar la lista de jugadores en la interfaz
        self.actualizar_lista_jugadores(main_window)

        # Actualizar información del usuario actual si es mi usuario
        if main_window.client.userid() == userid and hasattr(
            main_window, "update_mi_jugador_info"
        ):
            main_window.update_mi_jugador_info()

    def actualizar_lista_jugadores(self, main_window):
        """
        Actualiza la lista de jugadores en la interfaz de usuario.
        """
        # Obtener la lista de jugadores con sus colores
        jugadores = []
        for user_id, color in main_window.colores.colores_asignados().items():
            # Obtener el nombre de usuario del cliente
            client = main_window.client_by_id.get(user_id)
            if client and client.username():
                jugadores.append((client.username(), color))

        # Actualizar la lista de jugadores en la interfaz
        main_window.update_player_list(jugadores)


class ClientTaskAsignarPais(IClientTask):
    def __init__(self, data):
        self._msg = data

    def run(self, main_window):
        try:
            nombre_pais = self._msg.get("pais")
            userid = self._msg.get("userid")
            unidades = self._msg.get("unidades", 1)  # Valor por defecto de 1 unidad

            # Obtener el objeto país de la escena
            pais = main_window.scene.paises.get(nombre_pais)
            if not pais:
                print(f"País no encontrado: {nombre_pais}")
                return

            # Establecer las unidades del país
            pais.set_unidades(unidades)

            # Obtener el color asignado al jugador
            color = main_window.colores.color_asignado(userid)
            if not color:
                print(f"No se encontró color para el jugador {userid}")
                return

            # Establecer el color del país
            pais.set_color(color)

            print(
                f"País {nombre_pais} asignado al jugador {userid}"
                f"con {unidades} unidades y color {color.getRgb()}"
            )

        except Exception as e:
            print(f"Error al asignar país: {e}")


class ClientTaskUnidadesDisponibles(IClientTask):
    def __init__(self, data):
        self._unidades = data.get("unidades", {})

    def run(self, main_window):
        print(f"Recibidas unidades disponibles: {self._unidades}")
        if hasattr(main_window, "update_unidades_disponibles"):
            main_window.update_unidades_disponibles(self._unidades)


class ClientTaskActualizarListaJugadores(IClientTask):
    def __init__(self, data):
        self._jugadores = data.get("jugadores", [])

    def run(self, main_window):
        """
        Actualiza la lista de jugadores en la interfaz de usuario con el
        orden actualizado.

        Args:
            main_window: La ventana principal de la aplicación
        """
        try:
            # Crear una lista de tuplas (nombre, color) para actualizar la interfaz
            jugadores_actualizados = []

            for jugador in self._jugadores:
                userid = jugador.get("userid")
                color_data = jugador.get("color", {})

                # Obtener el nombre de usuario del cliente
                # Valor por defecto si no se encuentra el cliente
                nombre = f"Jugador {userid}"
                if (
                    hasattr(main_window, "client_by_id")
                    and userid in main_window.client_by_id
                ):
                    cliente = main_window.client_by_id[userid]
                    if hasattr(cliente, "username") and cliente.username():
                        nombre = cliente.username()

                # Crear un objeto QColor a partir de los componentes RGB

                color = QColor(
                    color_data.get("r", 200),
                    color_data.get("g", 200),
                    color_data.get("b", 200),
                )

                jugadores_actualizados.append((nombre, color))

            # Actualizar la lista de jugadores en la interfaz
            if hasattr(main_window, "update_player_list"):
                main_window.update_player_list(jugadores_actualizados)

        except Exception as e:
            print(f"Error al actualizar la lista de jugadores: {e}")


class ClientTaskError(IClientTask):
    def __init__(self, data):
        self._error_type = data.get("error_type")
        self._message = data.get("message")

    def run(self, main_window):
        """
        Maneja errores enviados por el servidor mostrando un diálogo
        de error al usuario.
        """
        if self._error_type == "duplicate_username":
            # Mostrar diálogo específico para nombres de usuario duplicados
            msg_box = QMessageBox(main_window)
            msg_box.setIcon(QMessageBox.Warning)
            msg_box.setWindowTitle("Nombre de usuario duplicado")
            msg_box.setText("El nombre de usuario que elegiste ya está en uso.")
            msg_box.setInformativeText(
                "Por favor, elige un nombre de usuario diferente."
            )
            msg_box.setStandardButtons(QMessageBox.Ok)
            msg_box.exec()

            # Cerrar ventana de esperar jugadores si está abierta
            if hasattr(main_window, "w") and main_window.w:
                main_window.w.close()

            # Desconectar del servidor y abrir ventana de conexión
            if hasattr(main_window, "conexion") and main_window.conexion:
                main_window.conexion.desconectar()

            # Abrir la ventana de conexión para que el usuario pueda
            # intentar con un nombre diferente
            main_window.abrir_ventana_conectar()
        else:
            # Mostrar diálogo genérico para otros tipos de error
            msg_box = QMessageBox(main_window)
            msg_box.setIcon(QMessageBox.Critical)
            msg_box.setWindowTitle("Error")
            msg_box.setText(self._message or "Ha ocurrido un error.")
            msg_box.setStandardButtons(QMessageBox.Ok)
            msg_box.exec()


dict_task = {
    "chat": ClientTaskChat,
    "sosadmin": ClientTaskSerAdmin,
    "estado": ClientTaskEstado,
    "color_asignado": ClientTaskColorAsignado,
    "color": ClientTaskColor,
    "user_id": ClientTaskUserId,
    "username": ClientTaskUsername,
    "turno": ClientTaskTurno,
    "tiempo": ClientTaskTiempo,
    "pais": ClientTaskAsignarPais,
    "unidades_disponibles": ClientTaskUnidadesDisponibles,
    "actualizar_lista_jugadores": ClientTaskActualizarListaJugadores,
    "error": ClientTaskError,
}
