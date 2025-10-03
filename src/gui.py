import contextlib

from PySide6.QtCore import QSize, Qt
from PySide6.QtWidgets import (
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
from src.gui_admin import VentanaAdmin
from src.gui_conectar import VentanaConectar
from src.gui_configuracion_dialog import ConfiguracionDialog
from src.gui_esperar_jugadores import VentanaEsperarJugadores
from src.gui_game_actions import GameActionsManager
from src.gui_language_selector import LanguageSelector
from src.gui_layout_manager import LayoutManager
from src.gui_players_manager import PlayersManager
from src.gui_sound_control import SoundControlWidget
from src.gui_status_manager import StatusManager
from src.gui_tarjetas_dialog import TarjetasDialog
from src.gui_theme_manager import ThemeManager
from src.gui_units_manager import UnitsManager
from src.i18n import translate as _
from src.sound_manager import SoundManager


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
        self.players_manager = PlayersManager(self)
        self.status_manager = StatusManager(self)
        self.units_manager = UnitsManager(self)
        self.game_actions_manager = GameActionsManager(self)
        self.sound_manager = SoundManager()
        self.setMinimumSize(QSize(800, 600))
        self.setMouseTracking(True)

        # Initialize turn number and current player info
        self._turno_actual = 0
        self._jugador_actual_id = None
        self._jugador_actual_nombre = None
        self._jugador_actual_color = None

        # Initialize game configuration
        self._segundos_por_turno = 20
        self._paises_para_victoria = 30
        self._objetivos_secretos = False
        self.misiles_habilitados = False

        # Initialize secret objective variables
        self._objetivo_secreto_id = None
        self._objetivo_secreto_descripcion = None

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

        # Separator
        sep5 = QFrame()
        sep5.setFrameShape(QFrame.VLine)
        sep5.setFrameShadow(QFrame.Sunken)
        self.status_bar.addPermanentWidget(sep5)

        # Add sound control widget
        self.sound_control = SoundControlWidget(self.sound_manager)
        self.status_bar.addPermanentWidget(self.sound_control)

        # Separator
        sep6 = QFrame()
        sep6.setFrameShape(QFrame.VLine)
        sep6.setFrameShadow(QFrame.Sunken)
        self.status_bar.addPermanentWidget(sep6)

        # Add timer widget for countdown
        self.timer_label = QLabel("")
        self.timer_label.setStyleSheet("font-weight: bold; padding: 2px 8px;")
        self.timer_label.setMinimumWidth(120)
        self.status_bar.addPermanentWidget(self.timer_label)

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
        Only shows players that are actually playing.
        :param players: List of tuples (name, color) where color is a QColor.
        """
        self.players_manager.update_player_list(players)

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
        self.turno_label.setText(f"Ronda: {num_ronda} - Turno: {num_turno + 1}")

        # Actualizar sombreado del jugador en su turno
        if jugador_actual_nombre:
            self.players_manager.set_current_player(jugador_actual_nombre)

    def update_status_bar(self, text, color=None):
        """Update the status bar with the given text.

        Args:
            text (str): The message to display in the status bar
            color (str, optional): Color for the text (e.g., 'green', 'red', '#ff0000')
        """
        self.status_manager.update_status_bar(text, color)

    def update_timer_display(self, text, color=None):
        """Update the timer display in the status bar.

        Args:
            text (str): The timer text to display
            color (str, optional): Color for the text
        """
        if color:
            self.timer_label.setStyleSheet(
                f"font-weight: bold; padding: 2px 8px; color: {color};"
            )
        else:
            self.timer_label.setStyleSheet("font-weight: bold; padding: 2px 8px;")
        self.timer_label.setText(text)

    def clear_status_bar(self):
        """Clear the status bar message, but keep the turn number."""
        self.status_manager.clear_status_bar()

    def update_game_state(self, estado):
        """Update the game state display in the status bar.

        Args:
            estado (str): The current game state
        """
        self.status_manager.update_game_state(estado)

    def update_mi_jugador_info(self):
        """Actualiza la información del usuario actual (mi jugador).

        Actualiza la información en la barra de estado.
        """
        self.status_manager.update_mi_jugador_info()

    def update_unidades_disponibles(self, unidades):
        """Actualiza el panel derecho con las unidades disponibles.

        Args:
            unidades (dict): Diccionario con el tipo de unidad y la cantidad disponible.
                Ejemplo: {"infanteria": 5, "misiles": 2, "Africa": 3}
        """
        self.units_manager.update_unidades_disponibles(unidades)

    def keyPressEvent(self, event):  # noqa: N802
        if event.key() == Qt.Key_Enter or event.key() == Qt.Key_Return:
            self.chat.send_message()
        elif event.key() == Qt.Key_Escape and hasattr(self.scene, "selection_manager"):
            # Cancelar selección con tecla Escape usando selection_manager
            self.scene.selection_manager.cancelar_seleccion()

    def closeEvent(self, _):  # noqa: N802
        self._vivo = False
        # Limpiar recursos del gestor de sonidos
        self.sound_manager.cleanup()

    def finalizar_turno(self):
        """Método llamado cuando se hace clic en el botón Finalizar Turno."""
        self.game_actions_manager.finalizar_turno()

    def atacar(self):
        """Método llamado cuando se hace clic en el botón Atacar de la toolbar."""
        self.game_actions_manager.atacar()

    def get_max_attack_units(self, pais):
        """
        Obtiene el máximo número de unidades disponibles para atacar desde un país.

        Args:
            pais (str): Nombre del país atacante

        Returns:
            int: Máximo número de unidades disponibles (1-3)
        """
        return self.game_actions_manager.get_max_attack_units(pais)

    def canjear_misil(self, pais):
        """Canjea 6 unidades por 1 misil en el país especificado.

        Args:
            pais (str): Nombre del país donde canjear el misil
        """
        if self.transmisor:
            self.transmisor.canjear_misil(pais)
            self.status_bar.showMessage(f"Canjeando misil en {pais}...", 3000)

    def lanzar_misil(self, pais_origen, pais_destino):
        """Lanza un misil desde un país hacia otro.

        Args:
            pais_origen (str): País desde donde se lanza el misil
            pais_destino (str): País objetivo del misil
        """
        if self.transmisor:
            self.transmisor.lanzar_misil(pais_origen, pais_destino)
            self.status_bar.showMessage(
                f"Lanzando misil desde {pais_origen} hacia {pais_destino}...",
                3000,
            )

    def set_configuracion_partida(
        self,
        segundos_por_turno,
        paises_para_victoria,
        *,
        objetivos_secretos=False,
        misiles_habilitados=False,
    ):
        """
        Establece la configuración de la partida.

        Args:
            segundos_por_turno (int): Duración de cada turno en segundos
            paises_para_victoria (int): Número de países necesarios para ganar
            objetivos_secretos (bool): Si los objetivos secretos están activados
            misiles_habilitados (bool): Si el sistema de misiles está habilitado
        """
        self._segundos_por_turno = segundos_por_turno
        self._paises_para_victoria = paises_para_victoria
        self._objetivos_secretos = objetivos_secretos
        self.misiles_habilitados = misiles_habilitados

        # Inicializar variables para objetivo secreto
        self._objetivo_secreto_id = None
        self._objetivo_secreto_descripcion = None

    def mostrar_configuracion_partida(self):
        """
        Muestra la ventana de configuración de la partida.
        """
        dialog = ConfiguracionDialog(
            self,
            self._segundos_por_turno,
            self._paises_para_victoria,
            objetivos_secretos=self._objetivos_secretos,
            misiles_habilitados=self.misiles_habilitados,
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
            self.estado_text.text() == "Esperando jugadores"
            or self.estado_text.text() == "Waiting for players"
        ):
            self.estado_text.setText(_("Esperando jugadores"))

        if (
            self.turno_text.text() == "Esperando turno"
            or self.turno_text.text() == "Waiting for turn"
        ):
            self.turno_text.setText(_("Esperando turno"))

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

    def set_objetivo_secreto(self, objetivo_id, descripcion):
        """
        Establece el objetivo secreto del jugador.

        Args:
            objetivo_id (str): ID del objetivo secreto
            descripcion (str): Descripción del objetivo secreto
        """
        self._objetivo_secreto_id = objetivo_id
        self._objetivo_secreto_descripcion = descripcion

        # Si hay un diálogo de tarjetas abierto, actualizarlo
        from src.gui_tarjetas_dialog import TarjetasDialog  # noqa: PLC0415

        for widget in self.findChildren(TarjetasDialog):
            if widget.isVisible():
                widget.set_objetivo_secreto(objetivo_id, descripcion)

    def mostrar_tarjetas(self):
        """Muestra la ventana de tarjetas del jugador."""
        # Solicitar tarjetas actualizadas al servidor
        self.transmisor.solicitar_tarjetas()

        dialog = TarjetasDialog(self)

        # Si tenemos tarjetas del servidor, usarlas inmediatamente
        if hasattr(self, "tarjetas_jugador") and self.tarjetas_jugador:
            dialog.actualizar_tarjetas(self.tarjetas_jugador)
        else:
            # Si no hay tarjetas, usar lista vacía para mostrar slots vacíos
            dialog.actualizar_tarjetas([])

        # Si tenemos un objetivo secreto, mostrarlo en el diálogo
        if self._objetivo_secreto_id and self._objetivo_secreto_descripcion:
            dialog.set_objetivo_secreto(
                self._objetivo_secreto_id, self._objetivo_secreto_descripcion
            )

        dialog.exec()
