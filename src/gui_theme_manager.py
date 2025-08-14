"""
Gestor de temas para la interfaz gráfica principal de PyTeg.
Maneja la aplicación y gestión de temas claro/oscuro en toda la aplicación.
"""

from PySide6.QtWidgets import QApplication, QFrame, QWidget


class ThemeManager:
    """Gestor de temas para la ventana principal."""

    def __init__(self, main_window):
        """Inicializar el gestor de temas.

        Args:
            main_window: Instancia de la ventana principal (Gui)
        """
        self.main_window = main_window

    def set_theme(self, theme: str):
        """Cambia el tema de la interfaz ("light" o "dark")."""
        if theme not in {"light", "dark"}:
            return
        self.main_window._theme = theme  # noqa: SLF001
        # Aplicar tema global a toda la app (fondos, textos, menús, etc.)
        self._apply_global_theme()
        self._apply_statusbar_theme()
        # Reaplicar estilos en secciones
        self._apply_units_theme()
        # Reaplicar estilos tarjetas jugadores
        if hasattr(self.main_window, "players_manager"):
            players_manager = self.main_window.players_manager
            player_labels = getattr(players_manager, "player_labels", [])
            for _player_id, _player_name, w in player_labels:
                self._apply_players_theme(w)
        # Notificar a la toolbar para actualizar el botón de tema
        toolbar = self.main_window.toolbar
        has_toolbar = hasattr(self.main_window, "toolbar")
        has_theme_changed = hasattr(toolbar, "on_theme_changed")
        if has_toolbar and has_theme_changed:
            toolbar.on_theme_changed(self.main_window._theme)  # noqa: SLF001

    def toggle_theme(self):
        """Alterna entre tema claro y oscuro y aplica el cambio."""
        current = getattr(self.main_window, "_theme", "light")
        new_theme = "dark" if current != "dark" else "light"
        self.set_theme(new_theme)

    def _apply_statusbar_theme(self):
        """Aplica el tema a la barra de estado."""
        if self.main_window._theme == "dark":  # noqa: SLF001
            self.main_window.status_bar.setStyleSheet(
                """
                QStatusBar { background: #2b2f36; border-top: 1px solid #3a3f47; }
                QStatusBar QLabel { color: #e6e6e6; font-size: 12px; }
                QLabel[class="pill"] {
                    background: #3a3f47; border: 1px solid #4a5060;
                    border-radius: 10px; padding: 2px 8px; color: #e6e6e6;
                }
                QFrame { color: #e6e6e6; }
                """
            )
        else:
            self.main_window.status_bar.setStyleSheet(
                """
                QStatusBar { background: #f7f7f9; border-top: 1px solid #e1e3e8; }
                QStatusBar QLabel { color: #333; font-size: 12px; }
                QLabel[class="pill"] {
                    background: #eef1f7; border: 1px solid #d7dbe6;
                    border-radius: 10px; padding: 2px 8px;
                }
                QFrame { color: #333; }
                """
            )

    def _apply_global_theme(self):
        """Aplica un stylesheet global para tema claro/oscuro en toda la ventana."""
        app = QApplication.instance()
        if app is None:
            return
        if getattr(self.main_window, "_theme", "light") == "dark":
            app.setStyleSheet(
                "QWidget { background-color: #1e1f23; color: #e6e6e6; }\n"
                "QToolBar { background-color: #2b2f36; "
                "border-bottom: 1px solid #3a3f47; }\n"
                "QMenu { background-color: #2b2f36; color: #e6e6e6; "
                "border: 1px solid #3a3f47; }\n"
                "QMenu::item:selected { background-color: #3a3f47; }\n"
                "QSplitter::handle { background: #2b2f36; }\n"
                "QLineEdit, QTextEdit, QPlainTextEdit { background: #252a33; "
                "color: #e6e6e6; border: 1px solid #3a3f47; }\n"
                "QListWidget, QTreeWidget, QTableWidget, QScrollArea { "
                "background: #23262b; color: #e6e6e6; }\n"
                "QPushButton { background: #3a3f47; color: #e6e6e6; "
                "border: 1px solid #4a5060; border-radius: 4px; "
                "padding: 4px 8px; }\n"
                "QPushButton:hover { background: #444b5a; }\n"
                "QStatusBar { background: #2b2f36; }\n"
            )
        else:
            # Restaurar estilos por defecto (mantiene estilos locales específicos)
            app.setStyleSheet("")

    def _apply_units_theme(self, root: QWidget | None = None):
        """Aplica el tema a la sección de unidades."""
        root = root or getattr(self.main_window, "centralWidget", lambda: None)()
        theme = getattr(self.main_window, "_theme", "light")
        if theme == "dark":
            ss = (
                "#unitsSection { background: #21252b; border: 1px solid #3a3f47;"
                " border-radius: 8px; }\n"
                "#unitsTitle { color: #e6e6e6; font-size: 13px; font-weight: 700; }\n"
                "#unitRowLabel { font-weight: 600; color: #ddd; }\n"
            )
        else:
            ss = (
                "#unitsSection { background: #fafbfe; border: 1px solid #e6e9f2;"
                " border-radius: 8px; }\n"
                "#unitsTitle { color: #333333; font-size: 13px; font-weight: 700; }\n"
                "#unitRowLabel { font-weight: 600; color: #555; }\n"
            )
        # Aplicar al contenedor de la sección si existe
        if root is None:
            return
        # Buscar el QFrame con objectName unitsSection en la jerarquía inmediata
        # En este contexto, "root" es la sección creada arriba
        if isinstance(root, QFrame) and root.objectName() == "unitsSection":
            root.setStyleSheet(ss)

    def _apply_players_theme(self, player_widget: QFrame):
        """Aplica el tema a un widget de jugador específico."""
        if self.main_window._theme == "dark":  # noqa: SLF001
            player_widget.setStyleSheet(
                "#playerCard { background: #272b33; border-radius: 6px;"
                " border: 1px solid #3a3f47; }"
            )
        else:
            player_widget.setStyleSheet(
                "#playerCard { background: #ffffff; border-radius: 6px;"
                " border: 1px solid #e6e9f2; }"
            )
