import contextlib

from PySide6.QtCore import QSize, Qt, QTimer
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QSizePolicy,
    QStatusBar,
    QWidget,
)

from src.client_transmisor import ClientNullTransmisor
from src.cliente_colores import Colores
from src.debug_logger import debug_logger
from src.gui_admin import VentanaAdmin
from src.gui_attack_dialog import AttackDialog
from src.gui_conectar import VentanaConectar
from src.gui_configuracion_dialog import ConfiguracionDialog
from src.gui_esperar_jugadores import VentanaEsperarJugadores
from src.gui_language_selector import LanguageSelector
from src.gui_layout_manager import LayoutManager
from src.gui_theme_manager import ThemeManager
from src.i18n import translate as _


class Gui(QMainWindow):
    def __init__(self, client):  # noqa: PLR0915
        super().__init__()
        self._vivo = True
        self.client = client
        # Inicializar tema lo antes posible para uso en setup inicial
        self._theme = "light"
        self.client_by_id = {}
        self.transmisor = ClientNullTransmisor()
        self.conexion = None
        self.w = None
        self.ventana_conectar = None
        self.setWindowTitle(_("PyTeg"))
        # self.setFixedSize(QSize(800, 600))
        self.resize(QSize(1280, 800))

        # Inicializar gestores
        self.layout_manager = LayoutManager(self)
        self.theme_manager = ThemeManager(self)
        self.setMinimumSize(QSize(800, 600))
        self.setMouseTracking(True)

        # Initialize turn number and current player info
        self._turno_actual = 0
        self._jugador_actual_id = None
        self._jugador_actual_nombre = None
        self._jugador_actual_color = None

        # Initialize game configuration
        self._segundos_por_turno = 20
        self._paises_para_victoria = 50

        self.colores = Colores()

        # Configurar la vista gráfica usando el layout manager
        self.layout_manager.setup_graphics_view()

        # Create a status bar with permanent widgets for turn number and status
        self.status_bar = QStatusBar()
        self.status_bar.setFixedHeight(26)
        # Aplicar tema al status bar (ya existe self._theme)
        self.theme_manager._apply_statusbar_theme()  # noqa: SLF001

        # Add a widget for the current player with color indicator and nickname
        self.jugador_actual_widget = QWidget()
        self.jugador_actual_layout = QHBoxLayout(self.jugador_actual_widget)
        self.jugador_actual_layout.setContentsMargins(4, 0, 4, 0)
        self.jugador_actual_layout.setSpacing(6)

        # Color indicator (square)
        self.color_indicator = QLabel()
        self.color_indicator.setFixedSize(16, 16)
        self.color_indicator.setStyleSheet("""
            background-color: #cccccc;
            border: 1px solid #999999;
            border-radius: 2px;
        """)
        self.jugador_actual_layout.addWidget(self.color_indicator)

        # Turn and player info
        self.turno_label = QLabel("Turno: 0")
        self.turno_label.setStyleSheet("font-weight: 600;")
        self.jugador_actual_layout.addWidget(self.turno_label)

        self.status_bar.addPermanentWidget(self.jugador_actual_widget)

        # Separator
        sep1 = QFrame()
        sep1.setFrameShape(QFrame.VLine)
        sep1.setFrameShadow(QFrame.Sunken)
        self.status_bar.addPermanentWidget(sep1)

        # Add a widget for "My Player" info
        self.mi_jugador_widget = QWidget()
        self.mi_jugador_layout = QHBoxLayout(self.mi_jugador_widget)
        self.mi_jugador_layout.setContentsMargins(4, 0, 4, 0)
        self.mi_jugador_layout.setSpacing(6)

        # "Mi jugador:" label
        self.mi_jugador_text = QLabel(_("Mi jugador:"))
        self.mi_jugador_text.setStyleSheet("color: #555;")
        self.mi_jugador_layout.addWidget(self.mi_jugador_text)

        # My color indicator (square)
        self.mi_color_indicator = QLabel()
        self.mi_color_indicator.setFixedSize(16, 16)
        self.mi_color_indicator.setStyleSheet("""
            background-color: #cccccc;
            border: 1px solid #999999;
            border-radius: 2px;
        """)
        self.mi_jugador_layout.addWidget(self.mi_color_indicator)

        # My username
        self.mi_username_label = QLabel(_("[No conectado]"))
        self.mi_username_label.setStyleSheet("font-weight: 600;")
        self.mi_jugador_layout.addWidget(self.mi_username_label)

        self.status_bar.addPermanentWidget(self.mi_jugador_widget)

        # Separator
        sep2 = QFrame()
        sep2.setFrameShape(QFrame.VLine)
        sep2.setFrameShadow(QFrame.Sunken)
        self.status_bar.addPermanentWidget(sep2)

        # Add a label for the game state
        self.estado_label = QLabel(_("Estado: Desconectado"))
        self.estado_label.setObjectName("estadoLabel")
        self.estado_label.setProperty("class", "pill")
        self.status_bar.addPermanentWidget(self.estado_label)

        # Separator
        sep3 = QFrame()
        sep3.setFrameShape(QFrame.VLine)
        sep3.setFrameShadow(QFrame.Sunken)
        self.status_bar.addPermanentWidget(sep3)

        # Add a label for country selection
        self.seleccion_label = QLabel(_("Selección: Ninguna"))
        self.seleccion_label.setProperty("class", "pill")
        self.status_bar.addPermanentWidget(self.seleccion_label)

        # Separator
        sep4 = QFrame()
        sep4.setFrameShape(QFrame.VLine)
        sep4.setFrameShadow(QFrame.Sunken)
        self.status_bar.addPermanentWidget(sep4)

        # Add language selector
        self.language_selector = LanguageSelector()
        # Conectar la señal de cambio de idioma
        self.language_selector.language_changed.connect(self.on_language_changed)
        self.status_bar.addPermanentWidget(self.language_selector)

        # Add a stretch to push the status message to the right
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.status_bar.addPermanentWidget(spacer)

        self.setStatusBar(self.status_bar)

        self.show()  # IMPORTANT!!!!! Windows are hidden by default.

    def vivo(self):
        return self._vivo

    def update_player_list(self, players):
        """
        Updates the player list on the right column.
        Only shows players that are actually playing.
        :param players: List of tuples (name, color) where color is a QColor.
        """
        # Limpiar widgets existentes
        self._clear_player_widgets()

        # Crear widgets solo para jugadores activos
        for name, color in players:
            self._create_single_player_widget(name, color)

    def _clear_player_widgets(self):
        """Elimina todos los widgets de jugadores existentes"""
        if hasattr(self, "player_labels"):
            for _label, _turn_indicator, player_widget in self.player_labels:
                player_widget.setParent(None)
                player_widget.deleteLater()
        self.player_labels = []

    def _create_single_player_widget(self, name, color):
        """Crea un widget individual para un jugador"""
        # Crear un widget para el jugador (estilo tarjeta, neutro)
        player_widget = QFrame()
        player_widget.setObjectName("playerCard")

        player_layout = QHBoxLayout(player_widget)
        player_layout.setContentsMargins(8, 8, 8, 8)
        player_layout.setSpacing(8)

        # Indicador de color (círculo + glifo inicial)
        turn_indicator = self._make_circle_icon(color.name(), None)
        player_layout.addWidget(turn_indicator)

        # Etiqueta con el nombre del jugador
        label = QLabel(name)
        player_layout.addWidget(label)

        # Estilos unificados con sección UNIDADES
        label.setStyleSheet("color: #333; font-weight: 600; font-size: 13px;")

        # Guardar referencia
        self.player_labels.append((label, turn_indicator, player_widget))

        # Añadir al layout
        self.players_layout.addWidget(player_widget)

        # Aplicar estilo de tarjeta mediante tema
        self.theme_manager._apply_players_theme(player_widget)  # noqa: SLF001

    def abrir_ventana_conectar(self):
        # Cancelar selección al abrir ventana de conexión
        if hasattr(self.scene, "selection_manager"):
            self.scene.selection_manager.cancelar_seleccion()

        # Mantener referencia persistente para conexión al selector de idioma
        if not hasattr(self, "ventana_conectar") or self.ventana_conectar is None:
            self.ventana_conectar = VentanaConectar(self)

        self.ventana_conectar.show()

    def ventana_admin(self):
        self.w = None
        self.w = VentanaAdmin(self)
        self.w.show()

    def ventana_esperar_jugadores(self):
        print("=== Iniciando ventana_esperar_jugadores ===")
        print("Creando nueva ventana de espera...")
        self.w = VentanaEsperarJugadores(self)

        # Conectar la señal de cierre para limpiar la referencia
        def limpiar_ventana():
            print("Limpiando referencia a la ventana de espera")
            if hasattr(self, "w"):
                with contextlib.suppress(Exception):
                    # Desconectar todas las señales para evitar llamadas duplicadas
                    self.w.destroyed.disconnect()

                self.w = None

        self.w.destroyed.connect(limpiar_ventana)

        # Mostrar la ventana
        self.w.show()
        print("Ventana de espera mostrada")

    def update_turno(
        self,
        num_turno,
        num_ronda,
        jugador_actual_id=None,
        jugador_actual_nombre=None,
        jugador_actual_color=None,
    ):
        """Update the turn and round number display.

        Args:
            num_turno (int): The current turn number
            num_ronda (int): The current round number
            jugador_actual_id (int, optional): ID del jugador actual
            jugador_actual_nombre (str, optional): Nombre del jugador actual
            jugador_actual_color (str, optional): Color del jugador actual
        """
        self._turno_actual = num_turno
        self._jugador_actual_id = jugador_actual_id
        self._jugador_actual_nombre = jugador_actual_nombre
        self._jugador_actual_color = jugador_actual_color

        # Actualizar el texto del turno
        if jugador_actual_nombre:
            self.turno_label.setText(
                f"Ronda: {num_ronda} - Turno: {jugador_actual_nombre}"
            )
        else:
            self.turno_label.setText(f"Ronda: {num_ronda} - Turno: {num_turno + 1}")

        # Actualizar el indicador de color
        if jugador_actual_color:
            self.color_indicator.setStyleSheet(f"""
                background-color: {jugador_actual_color};
                border: 1px solid #999999;
                border-radius: 2px;
            """)
        else:
            self.color_indicator.setStyleSheet("""
                background-color: #cccccc;
                border: 1px solid #999999;
                border-radius: 2px;
            """)

    def update_status_bar(self, text, color=None):
        """Update the status bar with the given text.

        Args:
            text (str): The message to display in the status bar
            color (str, optional): Color for the text (e.g., 'green', 'red', '#ff0000')
        """
        # Apply color styling if provided
        if color:
            # Create a temporary label to apply color styling
            if not hasattr(self, "_status_temp_label"):
                self._status_temp_label = QLabel()
                self.status_bar.addWidget(self._status_temp_label)

            self._status_temp_label.setText(text)
            self._status_temp_label.setStyleSheet(f"color: {color}; font-weight: bold;")
            # Clear the default message to avoid duplication
            self.status_bar.clearMessage()
        else:
            # Use default status bar message
            if hasattr(self, "_status_temp_label"):
                self._status_temp_label.setText("")
            self.status_bar.showMessage(text)

    def clear_status_bar(self):
        """Clear the status bar message, but keep the turn number."""
        self.status_bar.clearMessage()
        # Also clear the temporary colored label if it exists
        if hasattr(self, "_status_temp_label"):
            self._status_temp_label.setText("")

    def update_game_state(self, estado):
        """Update the game state display in the status bar.

        Args:
            estado (str): The current game state
        """
        # Traducir estados técnicos a nombres más amigables
        estados_amigables = {
            "INICIAL": "Inicial",
            "EsperarJugadores": "Esperando Jugadores",
            "JUGANDO": "En Juego",
            "FINALIZADO": "Finalizado",
            "Conectado": "Conectado",
            "Desconectado": "Desconectado",
        }

        estado_mostrar = estados_amigables.get(estado, estado)
        self.estado_label.setText(f"Estado: {estado_mostrar}")

    def update_mi_jugador_info(self):
        """Actualiza la información del usuario actual (mi jugador).

        Actualiza la información en la barra de estado.
        """
        try:
            debug_logger.log("GUI: update_mi_jugador_info llamado")
            # Verificar que tenemos un cliente conectado
            if (
                not hasattr(self, "client")
                or not self.client
                or not self.client.userid()
            ):
                debug_logger.log("GUI: No hay cliente conectado")
                self.mi_username_label.setText("[No conectado]")
                self.mi_color_indicator.setStyleSheet("""
                    background-color: #cccccc;
                    border: 1px solid #999999;
                    border-radius: 2px;
                """)
                return

            # Obtener mi usuario ID
            mi_user_id = self.client.userid()
            debug_logger.log(f"GUI: Mi user_id: {mi_user_id}")

            # Obtener mi nombre de usuario
            mi_username = "[Sin nombre]"
            if hasattr(self.client, "username") and self.client.username():
                mi_username = self.client.username()
            debug_logger.log(f"GUI: Mi username: {mi_username}")

            # Obtener mi color asignado
            mi_color = None
            if hasattr(self, "colores") and self.colores:
                mi_color = self.colores.color_asignado(mi_user_id)
                debug_logger.log(f"GUI: Mi color: {mi_color}")

            # Actualizar el nombre de usuario
            self.mi_username_label.setText(mi_username)

            # Actualizar el color
            if mi_color and hasattr(mi_color, "name"):
                color_hex = mi_color.name()  # Obtener color en formato hexadecimal
                debug_logger.log(f"GUI: Color hex: {color_hex}")
                self.mi_color_indicator.setStyleSheet(f"""
                    background-color: {color_hex};
                    border: 1px solid #999999;
                    border-radius: 2px;
                """)
            else:
                debug_logger.log("GUI: No hay color asignado, usando color por defecto")
                # Color por defecto si no hay color asignado
                self.mi_color_indicator.setStyleSheet("""
                    background-color: #cccccc;
                    border: 1px solid #999999;
                    border-radius: 2px;
                """)
        except (AttributeError, KeyError, ValueError) as e:
            print(f"Error al actualizar información de mi jugador: {e}")
            self.mi_username_label.setText("[Error]")

    def update_unidades_disponibles(self, unidades):  # noqa: PLR0912
        """Actualiza el panel derecho con las unidades disponibles.

        Args:
            unidades (dict): Diccionario con el tipo de unidad y la cantidad disponible.
                Ejemplo: {"infanteria": 5, "misiles": 2, "Africa": 3}
        """
        # Mapeo de nombres de continentes del servidor a los de la GUI
        continent_mapping = {
            "Africa": "África",
            "Europa": "Europa",
            "Asia": "Asia",
            "América del Sur": "América del Sur",
            "América del Norte": "América del Norte",
            "Oceanía": "Oceanía",
        }

        # Actualizar unidades generales (infantería)
        if "infanteria" in unidades:
            cantidad = unidades["infanteria"]
            prev = self._last_units.get("Generales", None)
            # Estilo con color verde si hay unidades disponibles
            if cantidad > 0:
                style = (
                    "font-weight: bold; "
                    "color: #2E7D32; "
                    "background-color: #E8F5E8; "
                    "padding: 4px 8px; "
                    "border-radius: 4px; "
                    "border-left: 3px solid #4CAF50;"
                )
                text = f"Generales: {cantidad}"
            else:
                style = "font-weight: bold; color: #666666;"
                text = f"Generales: {cantidad}"

            self.value_labels["Generales"].setText(text)
            self.value_labels["Generales"].setStyleSheet(style)
            if prev is None or prev != cantidad:
                self._flash_row("Generales")
            self._last_units["Generales"] = cantidad

        # Actualizar unidades de continentes
        for server_name, gui_name in continent_mapping.items():
            if server_name in unidades and gui_name in self.value_labels:
                cantidad = unidades[server_name]
                prev = self._last_units.get(gui_name, None)
                if cantidad > 0:
                    # Estilo destacado para continentes con unidades disponibles
                    style = (
                        "font-weight: bold; "
                        "color: #1565C0; "
                        "background-color: #E3F2FD; "
                        "padding: 4px 8px; "
                        "border-radius: 4px; "
                        "border-left: 3px solid #2196F3;"
                    )
                    text = f"{gui_name}: {cantidad}"
                else:
                    # Estilo normal para continentes sin unidades
                    style = "font-weight: bold; color: #666666;"
                    text = f"{gui_name}: 0"

                self.value_labels[gui_name].setText(text)
                self.value_labels[gui_name].setStyleSheet(style)
                if prev is None or prev != cantidad:
                    self._flash_row(gui_name)
                self._last_units[gui_name] = cantidad
            elif gui_name in self.value_labels:
                # Resetear continentes que no tienen unidades disponibles
                self.value_labels[gui_name].setText(f"{gui_name}: 0")
                self.value_labels[gui_name].setStyleSheet(
                    "font-weight: bold; color: #666666;"
                )

        # Actualizar Misiles: usar fila existente y mostrar/ocultar
        if "misiles" in unidades and unidades["misiles"] > 0:
            text = f"Misiles: {unidades['misiles']}"
            style = (
                "font-weight: bold; "
                "color: #D32F2F; "
                "background-color: #FFEBEE; "
                "padding: 4px 8px; "
                "border-radius: 4px; "
                "border-left: 3px solid #F44336;"
            )
            self.value_labels["Misiles"].setText(text)
            self.value_labels["Misiles"].setStyleSheet(style)
            # Mostrar fila completa (parent del label)
            self._row_widgets["Misiles"].setVisible(True)
            prev = self._last_units.get("Misiles", None)
            if prev is None or prev != unidades["misiles"]:
                self._flash_row("Misiles")
            self._last_units["Misiles"] = unidades["misiles"]
        else:
            # Ocultar y resetear
            self.value_labels["Misiles"].setText("Misiles: 0")
            self.value_labels["Misiles"].setStyleSheet(
                "font-weight: bold; color: #666666;"
            )
            self._row_widgets["Misiles"].setVisible(False)
            self._last_units["Misiles"] = 0

    def _flash_row(self, key: str):
        """Aplica un highlight temporal a la fila cuando cambian valores."""
        row = self._row_widgets.get(key)
        if not row:
            return
        original = row.styleSheet()
        row.setStyleSheet(original + "\n#unitRow { background: #fff8e1; }")
        QTimer.singleShot(300, lambda: row.setStyleSheet(original))

    def keyPressEvent(self, event):  # noqa: N802
        if event.key() == Qt.Key_Enter or event.key() == Qt.Key_Return:
            self.chat.send_message()
        elif event.key() == Qt.Key_Escape and hasattr(self.scene, "selection_manager"):
            # Cancelar selección con tecla Escape usando selection_manager
            self.scene.selection_manager.cancelar_seleccion()

    def closeEvent(self, _):  # noqa: N802
        self._vivo = False

    def finalizar_turno(self):
        """Método llamado cuando se hace clic en el botón Finalizar Turno."""
        # Aquí puedes agregar la lógica para finalizar el turno actual
        # Por ejemplo, notificar al servidor que el turno ha terminado
        if hasattr(self, "transmisor") and hasattr(self.transmisor, "finalizar_turno"):
            self.transmisor.finalizar_turno()
            # Cancelar selección después de finalizar turno
            if hasattr(self.scene, "selection_manager"):
                self.scene.selection_manager.cancelar_seleccion()
        else:
            print("No se pudo finalizar el turno: transmisor no disponible")

    def atacar(self):
        """Método llamado cuando se hace clic en el botón Atacar de la toolbar."""
        # Verificar que tenemos un selection_manager
        if not hasattr(self.scene, "selection_manager"):
            self.update_status_bar(
                "Error: No hay sistema de selección disponible", "red"
            )
            return

        selection_manager = self.scene.selection_manager
        origen = selection_manager.get_pais_origen()
        destino = selection_manager.get_pais_destino()

        if not origen:
            self.update_status_bar("Selecciona un país de origen primero", "orange")
            return

        if not destino:
            self.update_status_bar(
                "Selecciona un país de destino después del origen", "orange"
            )
            return

        if hasattr(self, "transmisor") and hasattr(self.transmisor, "atacar"):
            # Obtener información del país atacante para determinar unidades disponibles
            max_unidades = self.get_max_attack_units(origen)

            if max_unidades < 1:
                self.update_status_bar(
                    f"No hay suficientes unidades en {origen} para atacar", "orange"
                )
                return

            # Mostrar diálogo para seleccionar cantidad de unidades
            dialog = AttackDialog(origen, destino, max_unidades, self)
            if dialog.exec() == QDialog.Accepted:
                cantidad_unidades = dialog.get_cantidad_unidades()
                self.transmisor.atacar(origen, destino, cantidad_unidades)
                self.update_status_bar(
                    f"Atacando de {origen} a {destino} con {cantidad_unidades} "
                    f"unidad{'es' if cantidad_unidades > 1 else ''}...",
                    "blue",
                )
                # Cancelar selección después de atacar
                selection_manager.cancelar_seleccion()
        else:
            self.update_status_bar("Error: No hay conexión disponible", "red")

    def get_max_attack_units(self, pais):
        """
        Obtiene el máximo número de unidades disponibles para atacar desde un país.

        Args:
            pais (str): Nombre del país atacante

        Returns:
            int: Máximo número de unidades disponibles (1-3)
        """
        # Buscar el país en la escena para obtener sus unidades
        if hasattr(self.scene, "paises") and pais in self.scene.paises:
            pais_widget = self.scene.paises[pais]
            unidades_totales = pais_widget.get_unidades()
            # Se necesita dejar al menos 1 unidad en el país
            unidades_disponibles = max(0, unidades_totales - 1)
            # Máximo 3 unidades para atacar
            return min(unidades_disponibles, 3)

        # Si no se encuentra el país, asumir 0 unidades disponibles
        return 0

    def set_configuracion_partida(self, segundos_por_turno, paises_para_victoria):
        """
        Establece la configuración de la partida.

        Args:
            segundos_por_turno (int): Duración de cada turno en segundos
            paises_para_victoria (int): Número de países necesarios para ganar
        """
        self._segundos_por_turno = segundos_por_turno
        self._paises_para_victoria = paises_para_victoria

    def mostrar_configuracion_partida(self):
        """
        Muestra la ventana de configuración de la partida.
        """
        dialog = ConfiguracionDialog(
            self, self._segundos_por_turno, self._paises_para_victoria
        )
        dialog.exec()

    def on_language_changed(self, lang_code):
        """
        Maneja el cambio de idioma actualizando todos los componentes de la GUI.

        Args:
            lang_code (str): Código del nuevo idioma (ej: 'es', 'en')
        """
        # Actualizar título de la ventana
        self.setWindowTitle(_("PyTeg"))

        # Actualizar etiquetas de la barra de estado
        self.mi_jugador_text.setText(_("Mi jugador:"))

        # Actualizar estados si están en valores por defecto
        if (
            self.mi_username_label.text() == "[No conectado]"
            or self.mi_username_label.text() == "[Not connected]"
        ):
            self.mi_username_label.setText(_("[No conectado]"))

        if self.estado_label.text().startswith(
            "Estado:"
        ) or self.estado_label.text().startswith("Status:"):
            self.estado_label.setText(_("Estado: Desconectado"))

        if self.seleccion_label.text().startswith(
            "Selección:"
        ) or self.seleccion_label.text().startswith("Selection:"):
            self.seleccion_label.setText(_("Selección: Ninguna"))

        # Actualizar la toolbar
        if hasattr(self, "toolbar"):
            self.toolbar.update_language(lang_code)

        # No necesitamos actualizar el selector de idioma porque ya maneja
        # su propio estado

        print(f"GUI actualizada al idioma: {lang_code}")
