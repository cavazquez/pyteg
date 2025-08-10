import pathlib
from functools import partial

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import (
    QAction,
    QIcon,
)
from PySide6.QtWidgets import (
    QApplication,
    QMenu,
    QSizePolicy,
    QToolBar,
    QToolButton,
    QWidget,
)

from src.exception import ImagenNoEncontradaError


class ToolBar(QToolBar):
    def __init__(self, texto, main_window):
        super().__init__(texto)
        self.setMovable(False)
        self.setFloatable(False)
        self.setAllowedAreas(Qt.TopToolBarArea)
        # Mostrar texto al lado del ícono para mejor legibilidad
        self.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.setIconSize(QSize(24, 24))
        self.main_window = main_window

        # Referencias a los botones que se activan/desactivan
        self.button_conectar = None
        self.button_desconectar = None
        self.button_atacar = None
        self.button_mover = None
        self.button_finalizar_turno = None
        self.button_fullscreen = None
        self.button_admin = None

        # Configurar la barra de herramientas
        self._setup_action_buttons()
        self._setup_size_menu()

        # Establecer estado inicial (desconectado)
        self._habilitar_solo_conectar()

    def _validar_icono(self, ruta_icono, contexto=""):
        """Valida que un archivo de icono existe y se puede cargar.

        Raises:
            ImagenNoEncontradaError: Si el archivo de icono no existe.
        """
        if not pathlib.Path(ruta_icono).exists():
            contexto_msg = f" ({contexto})" if contexto else ""
            raise ImagenNoEncontradaError(
                ruta_icono, f"icono de la barra de herramientas{contexto_msg}"
            )
        return QIcon(ruta_icono)

    def _setup_spacers_right(self):
        """Añade un expansor a la derecha para empujar elementos finales"""
        right_spacer = QWidget(self)
        right_spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.addWidget(right_spacer)

    def _setup_action_buttons(self):
        """Configura los botones de acción en la barra de herramientas"""
        # Grupo: Conexión
        icono_conectar = self._validar_icono("icons/conectar.png", "conectar")
        self.button_conectar = QAction(icono_conectar, "Conectar", self)
        self.button_conectar.triggered.connect(self.main_window.abrir_ventana_conectar)
        self.button_conectar.setToolTip("Conectar al servidor")
        self.button_conectar.setStatusTip("Abrir ventana de conexión")
        self.addAction(self.button_conectar)

        self.addSeparator()

        # Grupo: Acciones de juego
        icono_atacar = self._validar_icono("icons/atacar.png", "atacar")
        self.button_atacar = QAction(icono_atacar, "Atacar", self)
        self.button_atacar.triggered.connect(self.main_window.atacar)
        self.button_atacar.setToolTip("Atacar país seleccionado")
        self.button_atacar.setStatusTip("Ejecutar ataque entre países seleccionados")
        self.addAction(self.button_atacar)

        # Botón mover
        icono_mover = self._validar_icono("icons/mover.png", "mover")
        self.button_mover = QAction(icono_mover, "Mover", self)
        self.button_mover.setEnabled(False)  # Inicialmente deshabilitado
        self.button_mover.triggered.connect(self._mover_paises_seleccionados)
        self.button_mover.setToolTip("Mover unidades entre países")
        self.button_mover.setStatusTip("Mover 1 unidad entre los países seleccionados")
        self.addAction(self.button_mover)
        self.addSeparator()

        # Botón para finalizar el turno
        icono_finalizar = self._validar_icono("icons/finish.png", "finalizar turno")
        self.button_finalizar_turno = QAction(icono_finalizar, "Finalizar Turno", self)
        self.button_finalizar_turno.setEnabled(True)  # Siempre habilitado
        self.button_finalizar_turno.triggered.connect(self.main_window.finalizar_turno)
        self.button_finalizar_turno.setToolTip("Finalizar tu turno actual")
        self.button_finalizar_turno.setStatusTip("Pasar el turno al siguiente jugador")
        self.addAction(self.button_finalizar_turno)

        self.addSeparator()

        # Botón para mostrar configuración de la partida
        icono_config = self._validar_icono("icons/resize.png", "configuración")
        self.button_configuracion = QAction(icono_config, "Configuración", self)
        self.button_configuracion.setEnabled(True)  # Siempre habilitado
        self.button_configuracion.triggered.connect(
            self.main_window.mostrar_configuracion_partida
        )
        self.button_configuracion.setToolTip("Ver configuración de la partida")
        self.button_configuracion.setStatusTip(
            "Mostrar duración de turno y objetivo de países"
        )
        self.addAction(self.button_configuracion)

        # Grupo: Administración (removido)

    def _setup_size_menu(self):
        """Configura el menú de tamaño y su botón"""
        # Crear y configurar el menú
        self.size_menu = self._create_size_menu()

        # Crear botón de menú con ícono
        size_button = self._create_size_button()

        # Botón Pantalla Completa (toggle)
        self.button_fullscreen = QAction(self)
        icono_full = self._validar_icono(
            "icons/fullscreen.png", "pantalla completa (toggle)"
        )
        self.button_fullscreen.setIcon(icono_full)
        self.button_fullscreen.setCheckable(True)
        self.button_fullscreen.setText("Pantalla Completa")
        self.button_fullscreen.setToolTip("Alternar pantalla completa")
        self.button_fullscreen.setStatusTip("Entrar/salir de pantalla completa")
        self.button_fullscreen.triggered.connect(self._toggle_fullscreen)
        self.addAction(self.button_fullscreen)

        # Espaciador para empujar controles de tamaño a la derecha
        self._setup_spacers_right()
        # Agregar el botón al extremo derecho
        self.addWidget(size_button)

    def _create_size_menu(self):
        """Crea el menú de tamaño con todas sus opciones"""
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                padding: 5px;
            }
            QMenu::item {
                padding: 6px 25px 6px 30px;
                border-radius: 3px;
                margin: 2px;
            }
            QMenu::item:selected {
                background-color: #4361ee;
                color: white;
            }
            QMenu::icon {
                padding-left: 10px;
            }
            QMenu::separator {
                height: 1px;
                background: #dee2e6;
                margin: 5px 10px;
            }
        """)

        # Sección de tamaños predefinidos
        menu.addSection("Tamaños predefinidos")

        # Acciones para los tamaños predefinidos con íconos
        size_actions = [
            ("Pequeño (800x600)", 800, 600, "icons/size_small.png"),
            ("Mediano (1024x768)", 1024, 768, "icons/size_medium.png"),
            ("Grande (1280x800)", 1280, 800, "icons/size_large.png"),
        ]

        for text, width, height, icon_path in size_actions:
            action = QAction(text, self)
            icono = self._validar_icono(icon_path, f"tamaño {text}")
            action.setIcon(icono)
            action.triggered.connect(partial(self.resize_window, width, height))
            menu.addAction(action)

        # Separador
        menu.addSeparator()

        # Opciones de pantalla completa
        fullscreen_action = QAction("Pantalla Completa", self)
        icono_fullscreen = self._validar_icono(
            "icons/fullscreen.png", "pantalla completa"
        )
        fullscreen_action.setIcon(icono_fullscreen)
        fullscreen_action.triggered.connect(lambda: self.resize_window(0, 0))
        menu.addAction(fullscreen_action)

        # Opción para ajustar al tamaño de la pantalla
        fit_screen_action = QAction("Ajustar a la pantalla", self)
        icono_fit = self._validar_icono("icons/fit_screen.png", "ajustar pantalla")
        fit_screen_action.setIcon(icono_fit)
        fit_screen_action.triggered.connect(self.fit_to_screen)
        menu.addAction(fit_screen_action)

        # Separador
        menu.addSeparator()

        # Opción para restaurar tamaño por defecto
        default_action = QAction("Tamaño por defecto", self)
        icono_default = self._validar_icono(
            "icons/default_size.png", "tamaño por defecto"
        )
        default_action.setIcon(icono_default)
        default_action.triggered.connect(lambda: self.resize_window(1280, 800))
        menu.addAction(default_action)

        return menu

    def _create_size_button(self):
        """Crea el botón de tamaño con su estilo"""
        size_button = QToolButton(self)
        icono_resize = self._validar_icono("icons/resize.png", "botón de redimensionar")
        size_button.setIcon(icono_resize)
        size_button.setToolTip("Cambiar tamaño de la ventana")
        size_button.setPopupMode(QToolButton.InstantPopup)
        size_button.setMenu(self.size_menu)
        size_button.setIconSize(QSize(24, 24))

        # Estilo para el botón
        size_button.setStyleSheet("""
            QToolButton {
                border: none;
                padding: 4px;
                border-radius: 4px;
            }
            QToolButton:hover {
                background-color: rgba(67, 97, 238, 0.1);
            }
            QToolButton:pressed {
                background-color: rgba(67, 97, 238, 0.2);
            }
            QToolButton::menu-indicator {
                image: none;
            }
        """)

        return size_button

    def resize_window(self, width, height):
        """Cambia el tamaño de la ventana principal"""
        if width == 0 or height == 0:  # Pantalla completa
            self.main_window.showFullScreen()
            if self.button_fullscreen:
                self.button_fullscreen.setChecked(True)
        else:
            # Asegurarse de salir del modo pantalla completa
            self.main_window.showNormal()
            self.main_window.resize(width, height)
            # Centrar la ventana en la pantalla
            self.center_window()
            if self.button_fullscreen:
                self.button_fullscreen.setChecked(False)

    def fit_to_screen(self):
        """Ajusta la ventana al tamaño de la pantalla con un margen"""
        # Obtener el tamaño disponible de la pantalla
        screen = QApplication.primaryScreen().availableGeometry()
        # Calcular un tamaño que sea el 90% del tamaño disponible
        width = int(screen.width() * 0.9)
        height = int(screen.height() * 0.9)
        # Redimensionar y centrar
        self.main_window.showNormal()
        self.main_window.resize(width, height)
        self.center_window()

    def center_window(self):
        """Centra la ventana en la pantalla"""
        frame_geometry = self.main_window.frameGeometry()
        screen_center = QApplication.primaryScreen().availableGeometry().center()
        frame_geometry.moveCenter(screen_center)
        self.main_window.move(frame_geometry.topLeft())

    def actualizar_botones_seleccion(self, hay_dos_paises_seleccionados):
        """Actualiza el estado de los botones de atacar y mover según la selección"""
        # Solo actualizar si está conectado
        if self._esta_conectado():
            if self.button_atacar:
                self.button_atacar.setEnabled(hay_dos_paises_seleccionados)
            if self.button_mover:
                self.button_mover.setEnabled(hay_dos_paises_seleccionados)

    def actualizar_estado_conexion(self, conectado):
        """Actualiza el estado de todos los botones según el estado de conexión"""
        if conectado:
            self._habilitar_botones_conectado()
        else:
            self._habilitar_solo_conectar()

    def _esta_conectado(self):
        """Verifica si el cliente está conectado al servidor"""
        if not hasattr(self.main_window, "transmisor"):
            return False
        if self.main_window.transmisor is None:
            return False
        # Verificar si tiene conexión usando método público si existe
        if hasattr(self.main_window.transmisor, "esta_conectado"):
            return self.main_window.transmisor.esta_conectado()
        # Fallback: verificar si no es ClientNullTransmisor
        return not type(self.main_window.transmisor).__name__.endswith("NullTransmisor")

    def _habilitar_solo_conectar(self):
        """Deshabilita todos los botones excepto el de conectar"""
        if self.button_conectar:
            self.button_conectar.setEnabled(True)
        if self.button_atacar:
            self.button_atacar.setEnabled(False)
        if self.button_mover:
            self.button_mover.setEnabled(False)
        # El botón finalizar turno permanece siempre habilitado
        # Botón admin removido

    def _habilitar_botones_conectado(self):
        """Habilita los botones apropiados cuando está conectado"""
        # Deshabilitar botón conectar
        if self.button_conectar:
            self.button_conectar.setEnabled(False)
        # Botón desconectar removido

        # Los botones atacar y mover permanecen deshabilitados
        # hasta que se seleccionen países
        if self.button_atacar:
            self.button_atacar.setEnabled(False)
        if self.button_mover:
            self.button_mover.setEnabled(False)

        # El botón finalizar turno permanece siempre habilitado

    def _atacar_paises_seleccionados(self):
        """Ejecuta ataque entre los países seleccionados"""
        if hasattr(self.main_window, "scene") and self.main_window.scene:
            selection_manager = self.main_window.scene.selection_manager
            origen = selection_manager.get_pais_origen()
            destino = selection_manager.get_pais_destino()

            if origen and destino and hasattr(self.main_window, "transmisor"):
                # Por ahora usamos la misma función que mover (como está en gui_menu.py)
                self.main_window.transmisor.mover_unidad(
                    origen=origen, destino=destino, cantidad=1
                )
                self.main_window.status_bar.showMessage(
                    f"Atacando desde {origen} hacia {destino}", 3000
                )
                selection_manager.cancelar_seleccion()

    def _mover_paises_seleccionados(self):
        """Ejecuta movimiento entre los países seleccionados"""
        if hasattr(self.main_window, "scene") and self.main_window.scene:
            selection_manager = self.main_window.scene.selection_manager
            origen = selection_manager.get_pais_origen()
            destino = selection_manager.get_pais_destino()

            if origen and destino and hasattr(self.main_window, "transmisor"):
                self.main_window.transmisor.mover_unidad(
                    origen=origen, destino=destino, cantidad=1
                )
                self.main_window.status_bar.showMessage(
                    f"Moviendo 1 unidad de {origen} a {destino}", 3000
                )
                selection_manager.cancelar_seleccion()

    # Métodos para botones removidos (_desconectar, _abrir_admin) eliminados

    def _toggle_fullscreen(self):
        """Alterna entre pantalla completa y modo normal."""
        if self.main_window.isFullScreen():
            self.main_window.showNormal()
            if self.button_fullscreen:
                self.button_fullscreen.setChecked(False)
        else:
            self.main_window.showFullScreen()
            if self.button_fullscreen:
                self.button_fullscreen.setChecked(True)
