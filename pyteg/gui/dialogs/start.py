"""Punto de entrada común para partidas locales, LAN y por archivos."""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
)

from pyteg.client.bot_strategies import (
    BOT_DIFFICULTIES,
    DEFAULT_BOT_DIFFICULTY,
    difficulty_labels,
)
from pyteg.i18n import translate as _

if TYPE_CHECKING:
    from pyteg.gui.main_window import Gui


class StartDialog(QDialog):
    """Elige modo, mapa y reglas y permite retomar archivos recientes."""

    def __init__(self, window: Gui) -> None:  # noqa: PLR0915 -- formulario Qt.
        """Reúne los caminos de entrada sin crear una partida hasta confirmar."""
        super().__init__(window)
        self.main_window = window
        self.setWindowTitle(_("Jugar Pyteg"))
        self.resize(600, 620)
        layout = QVBoxLayout(self)
        self.heading = QLabel(_("Nueva partida"))
        self.heading.setStyleSheet("font-size: 22px; font-weight: bold;")
        layout.addWidget(self.heading)
        form = QFormLayout()
        self.mode = QComboBox()
        self.mode.addItem(_("Local · humano contra bots"), "local")
        self.mode.addItem(_("LAN · crear o unirse"), "lan")
        self.mode.addItem(_("Por archivos · turnos asíncronos"), "async")
        self.theme_selector = QComboBox()
        self.rules_selector = QComboBox()
        for selector in (self.theme_selector, self.rules_selector):
            selector.addItem(_("Clásico"), "classic")
            selector.addItem(_("Revancha"), "revancha")
            selector.setCurrentIndex(selector.findData(window.map_theme))
        self.name = QLineEdit(window.client.username() or _("Jugador 1"))
        self.name.setMaxLength(80)
        self.bots = QSpinBox()
        self.bots.setRange(0, 7)
        self.bots.setValue(3)
        self.difficulty = QComboBox()
        for difficulty, label in difficulty_labels().items():
            self.difficulty.addItem(label, difficulty)
        self.difficulty.setCurrentIndex(
            self.difficulty.findData(DEFAULT_BOT_DIFFICULTY)
        )
        self.names = QLineEdit(
            ", ".join(_("Jugador {}").format(index) for index in range(1, 5))
        )
        self._form = form
        self._rows = [
            ("Modo:", self.mode),
            ("Mapa:", self.theme_selector),
            ("Perfil de reglas:", self.rules_selector),
            ("Tu nombre:", self.name),
            ("Bots:", self.bots),
            ("Dificultad:", self.difficulty),
            ("Jugadores:", self.names),
        ]
        for text, field in self._rows:
            form.addRow(_(text), field)
        layout.addLayout(form)
        self.hint = QLabel()
        self.hint.setWordWrap(True)
        layout.addWidget(self.hint)
        self.error_label = QLabel()
        self.error_label.setStyleSheet("color: #b3261e;")
        self.error_label.setWordWrap(True)
        layout.addWidget(self.error_label)
        buttons = QHBoxLayout()
        self.start_button = QPushButton(_("Continuar"))
        self.start_button.setDefault(True)
        self.start_button.clicked.connect(self._start)
        self.open_button = QPushButton(_("Abrir archivo…"))
        self.open_button.clicked.connect(self._open)
        buttons.addWidget(self.start_button)
        buttons.addWidget(self.open_button)
        layout.addLayout(buttons)
        self.recent_label = QLabel(_("Partidas y archivos recientes"))
        layout.addWidget(self.recent_label)
        self.recent_list = QListWidget()
        self.recent_list.itemActivated.connect(self._open_recent)
        layout.addWidget(self.recent_list, stretch=1)
        self.mode.currentIndexChanged.connect(self._update_mode)
        self.bots.valueChanged.connect(self._update_mode)
        self.difficulty.currentIndexChanged.connect(self._update_mode)
        self._update_mode()
        self.refresh_recent()

    def _update_mode(self) -> None:
        mode = self.mode.currentData()
        self._form.setRowVisible(self.name, mode != "async")
        self._form.setRowVisible(self.bots, mode == "local")
        self._form.setRowVisible(
            self.difficulty, mode == "local" and self.bots.value() > 0
        )
        self._form.setRowVisible(self.names, mode == "async")
        self.hint.setText(
            {
                "local": _(
                    "Un humano y hasta siete bots. Podés jugar solo con cero "
                    "bots. Después elegís objetivos, situaciones "
                    "y el resto de las reglas."
                ),
                "lan": _(
                    "Continuá para crear una sala o buscar una partida en tu red. "
                    "Quien la crea puede personalizar todas las reglas."
                ),
                "async": _(
                    "Ingresá de 1 a 8 nombres separados por comas. Cada jugador recibe "
                    "y entrega su turno como un archivo, sin límite de tiempo."
                ),
            }[str(mode)]
        )
        if mode == "local" and self.bots.value() > 0:
            detail = {
                "easy": _("Fácil: jugadas simples y elección variada de ataques."),
                "normal": _(
                    "Normal: refuerza fronteras y cuida la defensa al avanzar."
                ),
                "hard": _(
                    "Difícil: prioriza su objetivo y evalúa riesgos "
                    "y ataques siguientes."
                ),
            }[str(self.difficulty.currentData())]
            self.hint.setText(self.hint.text() + "\n\n" + detail)
        self.error_label.clear()

    def refresh_recent(self) -> None:
        """Actualiza la lista cada vez que se vuelve a la pantalla de inicio."""
        self.recent_list.clear()
        for path in self.main_window.files_manager.recent.paths():
            item = QListWidgetItem(self.main_window.files_manager.describe_recent(path))
            item.setData(Qt.ItemDataRole.UserRole, str(path))
            item.setToolTip(str(path))
            self.recent_list.addItem(item)

    def _start(self) -> None:
        files = self.main_window.files_manager
        try:
            theme, profile = (
                str(self.theme_selector.currentData()),
                str(self.rules_selector.currentData()),
            )
            mode = self.mode.currentData()
            if mode == "local":
                files.start_offline(
                    theme,
                    profile,
                    self.name.text(),
                    self.bots.value(),
                    difficulty=str(self.difficulty.currentData()),
                )
            elif mode == "async":
                files.start_offline(theme, profile, self.names.text().split(","))
            else:
                self.main_window.window_manager.abrir_ventana_conectar()
                dialog = self.main_window.ventana_conectar
                if dialog is not None:
                    dialog.theme_selector.setCurrentIndex(
                        dialog.theme_selector.findData(theme)
                    )
                    dialog.rules_selector.setCurrentIndex(
                        dialog.rules_selector.findData(profile)
                    )
                    dialog.username.setText(self.name.text())
            self.accept()
        except (OSError, ValueError) as error:
            self.error_label.setText(str(error))

    def _open(self) -> None:
        if self.main_window.files_manager.open_game():
            self.accept()

    def _open_recent(self, item: QListWidgetItem) -> None:
        try:
            if self.main_window.files_manager.open_path(
                str(item.data(Qt.ItemDataRole.UserRole)), preview=True
            ):
                self.accept()
        except (OSError, ValueError, KeyError, TypeError) as error:
            self.error_label.setText(str(error))

    def update_language(self, _language: str) -> None:
        """Actualiza los textos sin perder selecciones del formulario."""
        self.setWindowTitle(_("Jugar Pyteg"))
        self.heading.setText(_("Nueva partida"))
        self.mode.setItemText(0, _("Local · humano contra bots"))
        self.mode.setItemText(1, _("LAN · crear o unirse"))
        self.mode.setItemText(2, _("Por archivos · turnos asíncronos"))
        for selector in (self.theme_selector, self.rules_selector):
            selector.setItemText(0, _("Clásico"))
            selector.setItemText(1, _("Revancha"))
        labels = difficulty_labels()
        for difficulty in BOT_DIFFICULTIES:
            self.difficulty.setItemText(
                self.difficulty.findData(difficulty), labels[difficulty]
            )
        for text, field in self._rows:
            label = self._form.labelForField(field)
            if isinstance(label, QLabel):
                label.setText(_(text))
        self.start_button.setText(_("Continuar"))
        self.open_button.setText(_("Abrir archivo…"))
        self.recent_label.setText(_("Partidas y archivos recientes"))
        self._update_mode()
