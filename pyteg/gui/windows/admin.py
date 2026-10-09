"""Módulo para la ventana de administración del juego."""

from __future__ import annotations

from typing import Any

from PySide6.QtCore import QSignalBlocker, Qt
from PySide6.QtGui import QIntValidator
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from pyteg.config import DEFAULT_MAP_THEME
from pyteg.core.partida.reglas import available_rule_modules, load_rules_for_map
from pyteg.core.situaciones.catalog import (
    available_situation_cards,
    available_situation_effects,
)
from pyteg.i18n import translate as _
from pyteg.toml_reader import TomlReader


class VentanaAdmin(QWidget):
    """Ventana de administración para configurar parámetros de la partida."""

    def __init__(self, main_window: Any) -> None:  # noqa: PLR0915
        """Inicializa la ventana de administración.

        Args:
            main_window: Ventana principal de la aplicación.

        """
        super().__init__(
            main_window if isinstance(main_window, QWidget) else None,
            Qt.WindowType.Window,
        )
        self.main_window = main_window
        self.setWindowTitle(_("Admin"))
        self.resize(720, 700)
        map_theme = getattr(main_window, "map_theme", DEFAULT_MAP_THEME)
        self.map_theme = map_theme
        self.is_admin_configuration = True
        self.start_pending = False
        initial_profile = (
            map_theme if map_theme in {"classic", "revancha"} else "classic"
        )
        rules = load_rules_for_map(map_theme, initial_profile)
        country_count = len(TomlReader.from_theme(map_theme).todos_los_paises())

        self._layout = QVBoxLayout()

        self.rules_profile_layout = QHBoxLayout()
        self.rules_profile_label = QLabel(_("Perfil de reglas:"))
        self.rules_profile_combo = QComboBox()
        self.rules_profile_combo.addItem(_("Clásico"), "classic")
        self.rules_profile_combo.addItem(_("Revancha"), "revancha")
        self.rules_profile_combo.setCurrentIndex(
            self.rules_profile_combo.findData(initial_profile)
        )
        self.rules_profile_layout.addWidget(self.rules_profile_label)
        self.rules_profile_layout.addWidget(self.rules_profile_combo)
        self._layout.addLayout(self.rules_profile_layout)

        self.rule_modules_label = QLabel(
            _("Mecánicas de Revancha (desmarcadas usan Clásico):")
        )
        self.rule_modules_label.setWordWrap(True)
        self._layout.addWidget(self.rule_modules_label)
        self.rule_module_checkboxes: dict[str, QCheckBox] = {}
        for module_id, label in available_rule_modules():
            checkbox = QCheckBox(_(label))
            checkbox.setChecked(initial_profile == "revancha")
            self._layout.addWidget(checkbox)
            self.rule_module_checkboxes[module_id] = checkbox

        # Fila para ingresar los segundos
        self.seconds_layout = QHBoxLayout()
        self.seconds_label = QLabel(_("Duración del turno (segundos):"))
        self.seconds_input = QLineEdit()
        self.seconds_input.setPlaceholderText(_("p. ej., 30, 60, 120"))
        self.seconds_input.setToolTip(_("Duración del turno en segundos"))
        self.seconds_input.setValidator(QIntValidator(0, 3600, self))
        self.seconds_input.setText(str(rules.turn_seconds))

        self.seconds_layout.addWidget(self.seconds_label)
        self.seconds_layout.addWidget(self.seconds_input)

        self._layout.addLayout(self.seconds_layout)

        # Checkbox para habilitar objetivo específico de países
        self.countries_checkbox = QCheckBox(_("Objetivo específico de países"))
        self.countries_checkbox.setChecked(True)
        self.countries_checkbox.setToolTip(
            _(
                "Activar para usar un objetivo específico de países "
                "en lugar de controlar todos"
            )
        )
        self._layout.addWidget(self.countries_checkbox)

        # Fila para ingresar países para ganar
        self.countries_layout = QHBoxLayout()
        self.countries_label = QLabel(_("Países para ganar:"))
        self.countries_input = QLineEdit()
        self.countries_input.setPlaceholderText(_("p. ej., 30, 50, 42"))
        self.countries_input.setToolTip(_("Cantidad de países necesarios para ganar"))
        self.countries_input.setValidator(QIntValidator(1, country_count, self))
        self.countries_input.setText(str(rules.victory_countries))

        self.countries_layout.addWidget(self.countries_label)
        self.countries_layout.addWidget(self.countries_input)

        self._layout.addLayout(self.countries_layout)

        # Checkbox para habilitar objetivos secretos
        self.objetivos_secretos_checkbox = QCheckBox(_("Objetivos secretos"))
        self.objetivos_secretos_checkbox.setChecked(rules.objectives_enabled)
        self.objetivos_secretos_checkbox.setToolTip(
            _("Activar los objetivos secretos elegidos de este mapa")
        )
        self._layout.addWidget(self.objetivos_secretos_checkbox)

        self.objective_checkboxes: dict[str, QCheckBox] = {}
        self.objectives_scroll = self._build_objective_list(map_theme)
        self._layout.addWidget(self.objectives_scroll)

        self.situations_checkbox = QCheckBox(_("Cartas de situación"))
        self.situations_checkbox.setChecked(rules.situation_ruleset != "none")
        self._layout.addWidget(self.situations_checkbox)

        self.situation_effects_label = QLabel(_("Tipos de situación:"))
        self._layout.addWidget(self.situation_effects_label)
        self.situation_checkboxes: dict[str, QCheckBox] = {}
        self.situation_card_checkboxes: dict[str, QCheckBox] = {}
        self.situation_card_effects: dict[str, str] = {}
        self._updating_situation_cards = False
        self.situations_scroll = self._build_situation_list()
        self._layout.addWidget(self.situations_scroll)

        self.situation_cards_label = QLabel(_("Cartas individuales:"))
        self._layout.addWidget(self.situation_cards_label)
        self.situation_cards_scroll = self._build_situation_card_list()
        self._layout.addWidget(self.situation_cards_scroll)
        for effect_id in self.situation_checkboxes:
            self._update_effect_checkbox(effect_id)

        # Checkbox para habilitar misiles
        self.misiles_checkbox = QCheckBox(_("Habilitar Misiles"))
        self.misiles_checkbox.setChecked(rules.missiles_enabled)
        self.misiles_checkbox.setToolTip(
            _("Activar para permitir canjear y lanzar misiles durante la partida")
        )
        self._layout.addWidget(self.misiles_checkbox)

        # Conectar checkbox para habilitar/deshabilitar el campo de países
        self.countries_checkbox.toggled.connect(self._toggle_countries_input)
        self.objetivos_secretos_checkbox.toggled.connect(self._toggle_objectives)
        self.situations_checkbox.toggled.connect(self._toggle_situations)
        self.rules_profile_combo.currentIndexChanged.connect(
            self._apply_profile_defaults
        )

        self.button = QPushButton(_("Empezar"))
        self.button.clicked.connect(self.empezar)
        # Permitir activar con Enter
        self.button.setDefault(True)
        self.button.setAutoDefault(True)
        self.seconds_input.returnPressed.connect(self.empezar)
        self.countries_input.returnPressed.connect(self.empezar)

        self.error_label = QLabel("")
        self.error_label.setStyleSheet("color: #b3261e;")
        self.error_label.hide()
        self._form_container = QWidget()
        self._form_container.setLayout(self._layout)
        self._form_scroll = QScrollArea()
        self._form_scroll.setWidgetResizable(True)
        self._form_scroll.setWidget(self._form_container)
        outer_layout = QVBoxLayout(self)
        outer_layout.addWidget(self._form_scroll)
        outer_layout.addWidget(self.error_label)
        outer_layout.addWidget(self.button)

        # Inicializar estado del campo de países
        self._toggle_countries_input(self.countries_checkbox.isChecked())
        self.objectives_scroll.setEnabled(self.objetivos_secretos_checkbox.isChecked())
        self.situations_scroll.setEnabled(self.situations_checkbox.isChecked())
        self.situation_cards_scroll.setEnabled(self.situations_checkbox.isChecked())
        self._restore_public_configuration()

    def _build_objective_list(self, map_theme: str) -> QScrollArea:
        """Muestra los objetivos que define el mapa, con selección individual.

        Returns:
            Contenedor desplazable con los objetivos del mapa.

        """
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setMinimumHeight(150)
        scroll.setMaximumHeight(180)
        content = QWidget()
        layout = QVBoxLayout(content)
        catalog = TomlReader.from_theme(map_theme).get_objetivos_secretos()
        for objective_id, data in catalog.items():
            if data.get("objetivo_comun", False):
                continue
            row = QHBoxLayout()
            checkbox = QCheckBox(objective_id)
            checkbox.setChecked(True)
            description = QLabel(str(data.get("descripcion", "")))
            description.setWordWrap(True)
            row.addWidget(checkbox, alignment=Qt.AlignmentFlag.AlignTop)
            row.addWidget(description, stretch=1)
            layout.addLayout(row)
            self.objective_checkboxes[objective_id] = checkbox
        layout.addStretch()
        scroll.setWidget(content)
        if not self.objective_checkboxes:
            self.objetivos_secretos_checkbox.setChecked(False)
            self.objetivos_secretos_checkbox.setEnabled(False)
        return scroll

    def _build_situation_list(self) -> QScrollArea:
        """Muestra controles que activan todas las copias de cada efecto.

        Returns:
            Contenedor desplazable con los tipos de situación.

        """
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setMinimumHeight(100)
        scroll.setMaximumHeight(140)
        content = QWidget()
        layout = QVBoxLayout(content)
        for effect_id, label in available_situation_effects():
            checkbox = QCheckBox(_(label))
            checkbox.setChecked(True)
            checkbox.setToolTip(effect_id)
            checkbox.toggled.connect(
                lambda enabled, selected_effect=effect_id: self._toggle_effect_cards(
                    selected_effect, enabled
                )
            )
            layout.addWidget(checkbox)
            self.situation_checkboxes[effect_id] = checkbox
        layout.addStretch()
        scroll.setWidget(content)
        return scroll

    def _build_situation_card_list(self) -> QScrollArea:
        """Muestra las 50 cartas físicas para elegir copias individuales.

        Returns:
            Contenedor desplazable con una casilla por carta.

        """
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setMinimumHeight(160)
        scroll.setMaximumHeight(240)
        content = QWidget()
        layout = QVBoxLayout(content)
        for card_id, label, effect_id in available_situation_cards():
            checkbox = QCheckBox(_(label))
            checkbox.setChecked(True)
            checkbox.toggled.connect(
                lambda _enabled, selected_effect=effect_id: (
                    self._update_effect_checkbox(selected_effect)
                )
            )
            checkbox.setToolTip(card_id)
            layout.addWidget(checkbox)
            self.situation_card_checkboxes[card_id] = checkbox
            self.situation_card_effects[card_id] = effect_id
        layout.addStretch()
        scroll.setWidget(content)
        return scroll

    def _toggle_effect_cards(self, effect_id: str, enabled: bool) -> None:  # noqa: FBT001
        """Marca o desmarca todas las copias físicas de un mismo efecto."""
        self._updating_situation_cards = True
        try:
            for card_id, checkbox in self.situation_card_checkboxes.items():
                if self.situation_card_effects[card_id] == effect_id:
                    checkbox.setChecked(enabled)
        finally:
            self._updating_situation_cards = False
        self._update_effect_checkbox(effect_id)

    def _update_effect_checkbox(self, effect_id: str) -> None:
        """Refleja en el control de tipo cuántas copias siguen elegidas."""
        if self._updating_situation_cards:
            return
        cards = [
            checkbox
            for card_id, checkbox in self.situation_card_checkboxes.items()
            if self.situation_card_effects[card_id] == effect_id
        ]
        selected = sum(checkbox.isChecked() for checkbox in cards)
        group_checkbox = self.situation_checkboxes[effect_id]
        with QSignalBlocker(group_checkbox):
            group_checkbox.setChecked(selected > 0)
        label = dict(available_situation_effects())[effect_id]
        group_checkbox.setText(_("{} ({}/{})").format(_(label), selected, len(cards)))

    def _apply_profile_defaults(self, _index: int) -> None:
        """Actualiza los valores sugeridos al cambiar el perfil de reglas."""
        profile = str(self.rules_profile_combo.currentData())
        rules = load_rules_for_map(self.map_theme, profile)
        for checkbox in self.rule_module_checkboxes.values():
            checkbox.setChecked(profile == "revancha")
        self.seconds_input.setText(str(rules.turn_seconds))
        self.countries_input.setText(str(rules.victory_countries))
        self.countries_checkbox.setChecked(rules.lobby_victory_countries > 0)
        self.objetivos_secretos_checkbox.setChecked(
            rules.objectives_enabled and bool(self.objective_checkboxes)
        )
        for checkbox in self.objective_checkboxes.values():
            checkbox.setChecked(True)
        self.misiles_checkbox.setChecked(rules.missiles_enabled)
        self.situations_checkbox.setChecked(rules.situation_ruleset != "none")
        for checkbox in self.situation_checkboxes.values():
            checkbox.setChecked(True)
        for checkbox in self.situation_card_checkboxes.values():
            checkbox.setChecked(True)

    def _restore_public_configuration(self) -> None:  # noqa: C901, PLR0912, PLR0914
        """Recupera los ajustes públicos al volver al lobby para una revancha."""
        model = getattr(self.main_window, "client_state_model", None)
        snapshot = getattr(model, "snapshot", None)
        config = snapshot.get("configuracion") if isinstance(snapshot, dict) else None
        if not isinstance(config, dict):
            return

        profile = config.get("rules_profile")
        if isinstance(profile, str):
            index = self.rules_profile_combo.findData(profile)
            if index >= 0:
                self.rules_profile_combo.setCurrentIndex(index)

        rule_modules = config.get("rule_modules")
        if isinstance(rule_modules, dict):
            for module_id, checkbox in self.rule_module_checkboxes.items():
                enabled = rule_modules.get(module_id)
                if isinstance(enabled, bool):
                    checkbox.setChecked(enabled)

        seconds = config.get("segundos_por_turno")
        if isinstance(seconds, int) and seconds > 0:
            self.seconds_input.setText(str(seconds))
        countries = config.get("paises_para_victoria")
        if isinstance(countries, int) and countries >= 0:
            self.countries_checkbox.setChecked(countries > 0)
            if countries > 0:
                self.countries_input.setText(str(countries))
        objectives_enabled = config.get("objetivos_secretos")
        if isinstance(objectives_enabled, bool):
            self.objetivos_secretos_checkbox.setChecked(objectives_enabled)
        missiles_enabled = config.get("misiles_habilitados")
        if isinstance(missiles_enabled, bool):
            self.misiles_checkbox.setChecked(missiles_enabled)
        situations_enabled = config.get("situations_enabled")
        if isinstance(situations_enabled, bool):
            self.situations_checkbox.setChecked(situations_enabled)

        objective_ids = config.get("objective_ids")
        if isinstance(objective_ids, list):
            selected_objectives = set(objective_ids)
            for objective_id, checkbox in self.objective_checkboxes.items():
                checkbox.setChecked(objective_id in selected_objectives)
        situation_effects = config.get("situation_effects")
        if isinstance(situation_effects, list):
            selected_effects = set(situation_effects)
            for effect_id, checkbox in self.situation_checkboxes.items():
                checkbox.setChecked(effect_id in selected_effects)
        situation_card_ids = config.get("situation_card_ids")
        if isinstance(situation_card_ids, list):
            selected_cards = set(situation_card_ids)
            for card_id, checkbox in self.situation_card_checkboxes.items():
                checkbox.setChecked(card_id in selected_cards)

    def update_language(self, _lang_code: str) -> None:
        """Re-aplica traducciones a etiquetas estáticas de la ventana admin."""
        self.setWindowTitle(_("Admin"))
        self.seconds_label.setText(_("Duración del turno (segundos):"))
        self.seconds_input.setPlaceholderText(_("p. ej., 30, 60, 120"))
        self.seconds_input.setToolTip(_("Duración del turno en segundos"))
        self.countries_checkbox.setText(_("Objetivo específico de países"))
        self.countries_checkbox.setToolTip(
            _(
                "Activar para usar un objetivo específico de países "
                "en lugar de controlar todos"
            )
        )
        self.countries_label.setText(_("Países para ganar:"))
        self.countries_input.setPlaceholderText(_("p. ej., 30, 50, 42"))
        self.countries_input.setToolTip(_("Cantidad de países necesarios para ganar"))
        self.objetivos_secretos_checkbox.setText(_("Objetivos secretos"))
        self.objetivos_secretos_checkbox.setToolTip(
            _("Activar los objetivos secretos elegidos de este mapa")
        )
        profile_label = getattr(self, "rules_profile_label", None)
        if profile_label is not None:
            profile_label.setText(_("Perfil de reglas:"))
            self.rules_profile_combo.setItemText(0, _("Clásico"))
            self.rules_profile_combo.setItemText(1, _("Revancha"))
            self.rule_modules_label.setText(
                _("Mecánicas de Revancha (desmarcadas usan Clásico):")
            )
            for module_id, label in available_rule_modules():
                self.rule_module_checkboxes[module_id].setText(_(label))
        situations_checkbox = getattr(self, "situations_checkbox", None)
        if situations_checkbox is not None:
            situations_checkbox.setText(_("Cartas de situación"))
            self.situation_effects_label.setText(_("Tipos de situación:"))
            self.situation_cards_label.setText(_("Cartas individuales:"))
            for card_id, label, _effect_id in available_situation_cards():
                self.situation_card_checkboxes[card_id].setText(_(label))
            for effect_id in self.situation_checkboxes:
                self._update_effect_checkbox(effect_id)
        self.misiles_checkbox.setText(_("Habilitar Misiles"))
        self.misiles_checkbox.setToolTip(
            _("Activar para permitir canjear y lanzar misiles durante la partida")
        )
        self.button.setText(_("Empezar"))

    def _toggle_countries_input(self, enabled: bool) -> None:  # noqa: FBT001
        """Habilita o deshabilita el campo de países según el checkbox."""
        self.countries_input.setEnabled(enabled)
        self.countries_label.setEnabled(enabled)

    def _toggle_objectives(self, enabled: bool) -> None:  # noqa: FBT001
        """Activa la selección y rellena todo si estaba vacía."""
        if enabled and not any(
            checkbox.isChecked() for checkbox in self.objective_checkboxes.values()
        ):
            for checkbox in self.objective_checkboxes.values():
                checkbox.setChecked(True)
        self.objectives_scroll.setEnabled(enabled)

    def _toggle_situations(self, enabled: bool) -> None:  # noqa: FBT001
        """Activa la selección y rellena todo si estaba vacía."""
        if enabled and not any(
            checkbox.isChecked() for checkbox in self.situation_card_checkboxes.values()
        ):
            for checkbox in self.situation_checkboxes.values():
                checkbox.setChecked(True)
        self.situations_scroll.setEnabled(enabled)
        self.situation_cards_scroll.setEnabled(enabled)

    def on_configuration_error(self, message: str) -> None:
        """Permite corregir una selección rechazada por el servidor."""
        self.start_pending = False
        self.button.setEnabled(True)
        self.error_label.setText(message)
        self.error_label.show()

    def empezar(self) -> None:
        """Inicia la partida con la configuración ingresada."""
        if getattr(self, "start_pending", False):
            return
        # Leer y validar los segundos ingresados
        segundos = None
        if self.seconds_input.text().strip():
            try:
                segundos = int(self.seconds_input.text())
            except ValueError:
                segundos = None

        # Leer y validar los países para ganar según el checkbox
        paises_para_victoria = None
        if self.countries_checkbox.isChecked():
            # Checkbox habilitado: usar valor específico del campo
            if self.countries_input.text().strip():
                try:
                    paises_para_victoria = int(self.countries_input.text())
                except ValueError:
                    paises_para_victoria = None
        else:
            # Checkbox deshabilitado: usar 0 para indicar "todos los países"
            paises_para_victoria = 0

        # Leer configuración de objetivos secretos
        objetivos_secretos = self.objetivos_secretos_checkbox.isChecked()

        # Leer configuración de misiles
        misiles_habilitados = self.misiles_checkbox.isChecked()

        profile_combo = getattr(self, "rules_profile_combo", None)
        if profile_combo is None:
            # Compatibilidad con adaptadores que sólo exponen controles antiguos.
            self.main_window.transmisor.empezar(
                segundos,
                paises_para_victoria,
                objetivos_secretos=objetivos_secretos,
                misiles_habilitados=misiles_habilitados,
            )
            self.close()
            return

        objective_ids = [
            objective_id
            for objective_id, checkbox in self.objective_checkboxes.items()
            if checkbox.isChecked()
        ]
        situation_card_ids = [
            card_id
            for card_id, checkbox in self.situation_card_checkboxes.items()
            if checkbox.isChecked()
        ]
        selected_effects = {
            self.situation_card_effects[card_id] for card_id in situation_card_ids
        }
        situation_effects = [
            effect_id
            for effect_id in self.situation_checkboxes
            if effect_id in selected_effects
        ]
        situations_enabled = self.situations_checkbox.isChecked()
        if objetivos_secretos and not objective_ids:
            self.error_label.setText(_("Seleccioná al menos un objetivo secreto."))
            self.error_label.show()
            return
        if situations_enabled and not situation_card_ids:
            self.error_label.setText(_("Seleccioná al menos una carta de situación."))
            self.error_label.show()
            return

        self.error_label.hide()
        self.start_pending = True
        self.button.setEnabled(False)
        self.main_window.transmisor.empezar(
            segundos,
            paises_para_victoria,
            objetivos_secretos=objetivos_secretos,
            misiles_habilitados=misiles_habilitados,
            rules_profile=str(profile_combo.currentData()),
            rule_modules={
                module_id: checkbox.isChecked()
                for module_id, checkbox in self.rule_module_checkboxes.items()
            },
            objective_ids=objective_ids,
            situations_enabled=situations_enabled,
            situation_effects=situation_effects,
            situation_card_ids=situation_card_ids,
        )

    def cargar_colores_asignados(self) -> None:
        """Método no-op para el admin.

        El cliente admin no visualiza la lista de colores como la ventana
        principal, pero algunos tasks del cliente invocan este método.
        Definirlo evita errores cuando el admin está abierto.
        """
