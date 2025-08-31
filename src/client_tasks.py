from abc import ABC, abstractmethod

from PySide6.QtCore import QTimer
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QMessageBox

from src.client import Client
from src.client_color import Color
from src.gui_dice_animation import BattleResultDialog
from src.gui_tarjetas_dialog import TarjetasDialog
from src.logger import get_logger


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
        self._msg_type = data.get("msg_type", "normal")

    def run(self, main_window):
        main_window.chat.append(self._msg, self._msg_type)


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
                except (AttributeError, RuntimeError) as e:
                    print(f"Error al cerrar la ventana de espera: {e}")
            else:
                print("No hay ventana de espera abierta para cerrar")

            # Actualizar la lista de jugadores en la interfaz principal
            try:
                self.actualizar_lista_jugadores(main_window)
            except (AttributeError, KeyError, TypeError) as e:
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
                debug_logger = get_logger("client.tasks")
                debug_logger.debug(
                    "ClientTaskColorAsignado: Mi user_id: %s, Color asignado a: %s",
                    mi_user_id,
                    id_user,
                )
                if mi_user_id == id_user:
                    debug_logger.debug(
                        "ClientTaskColorAsignado: ES MI COLOR, actualizando mi info"
                    )
                    if hasattr(main_window, "update_mi_jugador_info"):
                        main_window.update_mi_jugador_info()
                else:
                    debug_logger.debug(
                        "ClientTaskColorAsignado: NO es mi color, no actualizo"
                    )

        except (AttributeError, KeyError, ValueError) as e:
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
        except (AttributeError, KeyError, TypeError) as e:
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
        debug_logger = get_logger("client.tasks")
        debug_logger.debug("ClientTaskUserId: Recibido user_id %s", userid)

        # Solo establecer el ID del cliente actual si aún no tiene uno
        if not main_window.client.userid():
            debug_logger.debug(
                "ClientTaskUserId: Estableciendo %s como MI user_id", userid
            )
            main_window.client.set_userid(userid)
            # Actualizar información del usuario actual
            if hasattr(main_window, "update_mi_jugador_info"):
                main_window.update_mi_jugador_info()
        else:
            debug_logger.debug(
                "ClientTaskUserId: Ya tengo user_id %s, agregando %s a la lista",
                main_window.client.userid(),
                userid,
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
        main_window.chat.append(f"Turno {num_turno + 1} iniciado", "system")

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

        # Actualizar la ventana de espera de jugadores si está abierta
        if hasattr(main_window, "w") and main_window.w is not None:
            main_window.w.cargar_colores_asignados()

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

        except (AttributeError, KeyError, ValueError) as e:
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

        except (AttributeError, KeyError, TypeError) as e:
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


class ClientTaskResultadoBatalla(IClientTask):
    def __init__(self, data):
        self._origen = data.get("origen")
        self._destino = data.get("destino")
        self._atacante = data.get("atacante")
        self._defensor = data.get("defensor")
        self._dados_atacante = data.get("dados_atacante", [])
        self._dados_defensor = data.get("dados_defensor", [])
        self._resultado = data.get("resultado", {})
        self._conquistado = data.get("conquistado", False)

    def run(self, main_window):
        """
        Muestra el resultado de una batalla con comportamiento diferenciado:
        - Atacante: Ve animación completa de dados
        - Espectadores: Ven efectos visuales (titilación + pérdidas flotantes)
        """
        try:
            # Obtener nombre del jugador actual
            mi_nombre = None
            if hasattr(main_window, "client") and hasattr(
                main_window.client, "username"
            ):
                mi_nombre = main_window.client.username()

            # Verificar si soy el atacante
            soy_atacante = mi_nombre == self._atacante

            if soy_atacante:
                # SOY EL ATACANTE: Mostrar animación completa
                self._mostrar_animacion_completa(main_window)
            else:
                # SOY ESPECTADOR: Mostrar efectos visuales
                self._mostrar_efectos_batalla(main_window)

            # Debug info
            print(f"Batalla: {self._origen} -> {self._destino}")
            print(f"Atacante: {self._atacante}, Defensor: {self._defensor}")
            print(f"Mi nombre: {mi_nombre}, Soy atacante: {soy_atacante}")
            print(f"Conquistado: {self._conquistado}")

        except (AttributeError, KeyError, ValueError) as e:
            print(f"Error al mostrar resultado de batalla: {e}")
            # Fallback: mostrar mensaje simple en barra de estado
            if hasattr(main_window, "update_status_bar"):
                main_window.update_status_bar(
                    f"Error mostrando batalla: {self._atacante} vs {self._defensor}",
                    "red",
                )

    def _mostrar_animacion_completa(self, main_window):
        """Muestra la animación completa de dados para el atacante."""

        # Preparar datos de la batalla para el diálogo
        batalla_data = {
            "origen": self._origen,
            "destino": self._destino,
            "atacante": self._atacante,
            "defensor": self._defensor,
            "dados_atacante": self._dados_atacante,
            "dados_defensor": self._dados_defensor,
            "resultado": self._resultado,
            "conquistado": self._conquistado,
        }

        # Mostrar diálogo de animación de dados
        dialog = BattleResultDialog(batalla_data, main_window)

        # Conectar señal para actualizar barra de estado cuando termine
        def on_animation_finished():
            if self._conquistado:
                mensaje = f"¡Has conquistado {self._destino}!"
                color = "green"
            else:
                mensaje = f"Tu ataque a {self._destino} fue repelido"
                color = "orange"

            if hasattr(main_window, "update_status_bar"):
                main_window.update_status_bar(mensaje, color)

        dialog.animation_finished.connect(on_animation_finished)
        dialog.exec()  # Mostrar diálogo modal

    def _mostrar_efectos_batalla(self, main_window):
        """Muestra efectos visuales para espectadores (titilación + pérdidas)."""
        try:
            # 1. Iniciar titilación en países origen y destino
            self._iniciar_titilacion_paises(main_window)

            # 2. Mostrar mensaje en barra de estado
            mensaje = f"Batalla: {self._atacante} ataca {self._destino}"
            if hasattr(main_window, "update_status_bar"):
                main_window.update_status_bar(mensaje, "blue")

            # 3. Programar mostrar pérdidas flotantes después de 2.5 segundos
            QTimer.singleShot(
                2500, lambda: self._mostrar_perdidas_flotantes(main_window)
            )

        except (AttributeError, RuntimeError) as e:
            print(f"Error mostrando efectos de batalla: {e}")

    def _iniciar_titilacion_paises(self, main_window):
        """Inicia la titilación en los países origen y destino."""
        try:
            if hasattr(main_window, "scene") and hasattr(main_window.scene, "paises"):
                # Obtener países origen y destino
                pais_origen = main_window.scene.paises.get(self._origen)
                pais_destino = main_window.scene.paises.get(self._destino)

                # Iniciar titilación si los países existen
                if pais_origen and hasattr(pais_origen, "iniciar_titilacion_batalla"):
                    pais_origen.iniciar_titilacion_batalla()

                if pais_destino and hasattr(pais_destino, "iniciar_titilacion_batalla"):
                    pais_destino.iniciar_titilacion_batalla()

        except (AttributeError, RuntimeError) as e:
            print(f"Error iniciando titilación: {e}")

    def _mostrar_perdidas_flotantes(self, main_window):
        """Muestra las pérdidas flotantes y detiene la titilación."""
        try:
            # Detener titilación
            self._detener_titilacion_paises(main_window)

            # Calcular pérdidas
            perdedores = self._resultado.get("restar", [])
            perdidas_atacante = perdedores.count(self._atacante)
            perdidas_defensor = perdedores.count(self._defensor)

            # Mostrar pérdidas flotantes
            if perdidas_atacante > 0:
                self._mostrar_perdida_flotante(
                    main_window, self._origen, perdidas_atacante
                )

            if perdidas_defensor > 0:
                self._mostrar_perdida_flotante(
                    main_window, self._destino, perdidas_defensor
                )

            # Actualizar barra de estado con resultado final
            if self._conquistado:
                mensaje = f"¡{self._atacante} conquistó {self._destino}!"
                color = "green"
            else:
                mensaje = f"{self._defensor} defendió {self._destino}"
                color = "orange"

            if hasattr(main_window, "update_status_bar"):
                main_window.update_status_bar(mensaje, color)

        except (AttributeError, RuntimeError) as e:
            print(f"Error mostrando pérdidas flotantes: {e}")

    def _detener_titilacion_paises(self, main_window):
        """Detiene la titilación en los países origen y destino."""
        try:
            if hasattr(main_window, "scene") and hasattr(main_window.scene, "paises"):
                pais_origen = main_window.scene.paises.get(self._origen)
                pais_destino = main_window.scene.paises.get(self._destino)

                if pais_origen and hasattr(pais_origen, "detener_titilacion_batalla"):
                    pais_origen.detener_titilacion_batalla()

                if pais_destino and hasattr(pais_destino, "detener_titilacion_batalla"):
                    pais_destino.detener_titilacion_batalla()

        except (AttributeError, RuntimeError) as e:
            print(f"Error deteniendo titilación: {e}")

    def _mostrar_perdida_flotante(self, main_window, nombre_pais, perdidas):
        """Muestra una pérdida flotante sobre un país específico."""
        try:
            if hasattr(main_window, "scene") and hasattr(main_window.scene, "paises"):
                pais = main_window.scene.paises.get(nombre_pais)
                if pais and hasattr(pais, "mostrar_perdida_flotante"):
                    pais.mostrar_perdida_flotante(perdidas)

        except (AttributeError, RuntimeError) as e:
            print(f"Error mostrando pérdida flotante: {e}")


class ClientTaskVictoria(IClientTask):
    def __init__(self, data):
        self._ganador_id = data.get("ganador_id")
        self._ganador_nombre = data.get("ganador_nombre")

    def run(self, main_window):
        """
        Muestra un mensaje de victoria cuando alguien gana la partida.
        """
        try:
            # Mostrar mensaje en la barra de estado
            if hasattr(main_window, "update_status_bar"):
                main_window.update_status_bar(
                    f"🏆 ¡{self._ganador_nombre} ha ganado la partida!",
                    "green",
                )

            # Mostrar diálogo de victoria
            msg_box = QMessageBox(main_window)
            msg_box.setWindowTitle("¡Partida Terminada!")
            msg_box.setIcon(QMessageBox.Information)
            msg_box.setText("🏆 ¡Felicitaciones!")
            msg_box.setInformativeText(
                f"{self._ganador_nombre} ha ganado la partida "
                f"controlando el número objetivo de países."
            )
            msg_box.setStandardButtons(QMessageBox.Ok)
            msg_box.exec()

            # También mostrar en el chat
            if hasattr(main_window, "chat"):
                main_window.chat.append(
                    f"🏆 ¡{self._ganador_nombre} ha ganado la partida!", "system"
                )

        except (AttributeError, RuntimeError) as e:
            print(f"Error al mostrar mensaje de victoria: {e}")


class ClientTaskConfiguracionPartida(IClientTask):
    def __init__(self, data):
        self._segundos_por_turno = data.get("segundos_por_turno", 20)
        self._paises_para_victoria = data.get("paises_para_victoria", 50)

    def run(self, main_window):
        """
        Procesa la configuración de la partida y la almacena en la ventana principal.
        """
        try:
            # Almacenar la configuración en la ventana principal
            if hasattr(main_window, "set_configuracion_partida"):
                main_window.set_configuracion_partida(
                    self._segundos_por_turno, self._paises_para_victoria
                )

            # Mostrar mensaje en la barra de estado
            if hasattr(main_window, "update_status_bar"):
                if self._paises_para_victoria == 0:
                    objetivo_texto = "todos los países"
                else:
                    objetivo_texto = f"{self._paises_para_victoria} países"
                main_window.update_status_bar(
                    f"Objetivo: {objetivo_texto} | Turno: {self._segundos_por_turno}s",
                    "blue",
                )

        except (AttributeError, RuntimeError) as e:
            print(f"Error al procesar configuración de partida: {e}")


class ClientTaskTarjetasJugador(IClientTask):
    def __init__(self, data):
        self._tarjetas = data.get("tarjetas", [])

    def run(self, main_window):
        """
        Actualiza las tarjetas del jugador en la GUI.

        Args:
            main_window: Ventana principal de la GUI
        """
        try:
            # Almacenar las tarjetas en la GUI para uso posterior
            if hasattr(main_window, "tarjetas_jugador"):
                main_window.tarjetas_jugador = self._tarjetas
            else:
                # Si no existe el atributo, crearlo
                main_window.tarjetas_jugador = self._tarjetas

            debug_logger = get_logger("client.tasks")
            debug_logger.info(
                "Tarjetas del jugador actualizadas: %s tarjetas", len(self._tarjetas)
            )
            print(
                f"ClientTaskTarjetasJugador: Recibidas {len(self._tarjetas)} tarjetas: "
                f"{self._tarjetas}"
            )

            # Si hay un diálogo de tarjetas abierto, actualizarlo
            for widget in main_window.findChildren(TarjetasDialog):
                if widget.isVisible():
                    widget.actualizar_tarjetas(self._tarjetas)
                    debug_logger.info("Diálogo de tarjetas actualizado automáticamente")

        except (AttributeError, RuntimeError) as e:
            print(f"Error al procesar tarjetas del jugador: {e}")


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
    "resultado_batalla": ClientTaskResultadoBatalla,
    "victoria": ClientTaskVictoria,
    "configuracion_partida": ClientTaskConfiguracionPartida,
    "tarjetas_jugador": ClientTaskTarjetasJugador,
}
