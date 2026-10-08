"""Carta de situación vigente, visible sin interrumpir la partida."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Any

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QLabel, QSizePolicy, QVBoxLayout, QWidget

from pyteg.i18n import translate as _


def _effect_descriptions() -> dict[str, str]:
    """Traduce las explicaciones al idioma vigente.

    Returns:
        Descripciones de las ocho estrategias del mazo.

    """
    return {
        "classic_combat": _("Se mantienen las reglas de combate de esta partida."),
        "snow": _("El defensor suma un dado, hasta un máximo de cuatro."),
        "tailwind": _("El atacante suma un dado, hasta un máximo de cuatro."),
        "crisis": _(
            "Los jugadores con la menor tirada no pueden reclamar tarjeta "
            "de país durante esta ronda. Los empates también quedan afectados."
        ),
        "extra_reinforcements": _(
            "Cada jugador recibe refuerzos extra equivalentes a la mitad de "
            "sus países, redondeada hacia abajo."
        ),
        "open_borders": _("Solo se puede atacar entre continentes diferentes."),
        "closed_borders": _("Solo se puede atacar dentro del mismo continente."),
        "rest": _(
            "Los jugadores indicados no pueden atacar ni mover unidades "
            "durante esta ronda. Pueden colocar refuerzos."
        ),
    }


def _effect_names() -> dict[str, str]:
    """Traduce los nombres de las cartas.

    Returns:
        Nombres visibles por ID de estrategia.

    """
    return {
        "classic_combat": _("Combate clásico"),
        "snow": _("Nieve"),
        "tailwind": _("Viento a favor"),
        "crisis": _("Crisis"),
        "extra_reinforcements": _("Refuerzos extras"),
        "open_borders": _("Fronteras abiertas"),
        "closed_borders": _("Fronteras cerradas"),
        "rest": _("Descanso"),
    }


@dataclass(frozen=True, slots=True)
class SituationView:
    """Contenido traducido de la franja, sin referencias a widgets."""

    title: str
    description: str
    affected: str = ""
    rolls: str = ""
    restricted: bool = False


def _player_names(state: dict[str, Any], local_userid: int | None) -> dict[int, str]:
    names: dict[int, str] = {}
    for player in state.get("players") or []:
        if not isinstance(player, dict) or not isinstance(player.get("userid"), int):
            continue
        userid = player["userid"]
        name = str(player.get("username") or _("Jugador %(id)s") % {"id": userid})
        if userid == local_userid:
            name = _("%(name)s (vos)") % {"name": name}
        names[userid] = name
    return names


def _affected_text(affected: list[int], names: dict[int, str]) -> str:
    if not affected:
        return _("Sin jugadores afectados.")
    return _("Afecta a: %(players)s.") % {
        "players": ", ".join(names.get(userid, str(userid)) for userid in affected)
    }


def situation_view(
    state: dict[str, Any], local_userid: int | None = None
) -> SituationView | None:
    """Construye la carta que debe mostrar el cliente desde el snapshot.

    Returns:
        Contenido visible o ``None`` fuera de partida y con el mazo apagado.

    """
    if state.get("estado") != "JUGANDO":
        return None
    card = state.get("situacion")
    config = state.get("configuracion") or {}
    if not isinstance(card, dict):
        return None
    effect = card.get("efecto", "none")
    if effect == "none":
        if (
            not isinstance(config, dict)
            or config.get("situation_ruleset", "none") == "none"
        ):
            return None
        return SituationView(
            _("Sin carta de situación"),
            _("Se revela una carta al comenzar cada ronda desde la segunda.")
            if card.get("ronda", 1) == 1
            else _(
                "No hay una carta aplicable en esta ronda. "
                "Se mantienen las reglas de la partida."
            ),
        )
    name = _effect_names().get(effect, str(card.get("nombre") or _("Situación")))
    names = _player_names(state, local_userid)
    affected = card.get("jugadores_afectados")
    affected_ids = (
        [userid for userid in affected if isinstance(userid, int)]
        if isinstance(affected, list)
        else []
    )
    rolls = card.get("tiradas_crisis")
    rolls_text = ""
    if isinstance(rolls, dict) and rolls:
        results = [
            f"{names.get(int(userid), userid)}: {value}"
            for userid, value in rolls.items()
            if isinstance(userid, str) and userid.isdecimal() and isinstance(value, int)
        ]
        rolls_text = _("Dados: %(rolls)s.") % {"rolls": "; ".join(results)}
    return SituationView(
        _("%(card)s · Ronda %(round)s")
        % {"card": name, "round": card.get("ronda", "—")},
        _effect_descriptions().get(
            effect, _("Esta carta modifica las reglas durante la ronda actual.")
        ),
        _affected_text(affected_ids, names) if isinstance(affected, list) else "",
        rolls_text,
        restricted=effect in {"crisis", "rest"} and local_userid in affected_ids,
    )


class SituationBanner(QFrame):
    """Franja compacta con carta, efecto y resultados públicos de la ronda."""

    def __init__(self, parent: QWidget | None = None) -> None:
        """Crea las etiquetas y conserva el estado para cambios de idioma."""
        super().__init__(parent)
        self.setObjectName("situationBanner")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self._state: dict[str, Any] = {}
        self._local_userid: int | None = None
        self._theme = "light"
        self._restricted = False
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 7, 12, 7)
        layout.setSpacing(3)
        self.title_label = QLabel()
        self.effect_label = QLabel()
        self.details_label = QLabel()
        for label in (self.title_label, self.effect_label, self.details_label):
            label.setTextFormat(Qt.TextFormat.PlainText)
            label.setWordWrap(True)
            label.setMinimumWidth(0)
            layout.addWidget(label)
        self.title_label.setObjectName("situationTitle")
        self.details_label.setObjectName("situationDetails")
        self.apply_theme(self._theme)
        self.hide()

    def update_snapshot(self, state: dict[str, Any], local_userid: int | None) -> None:
        """Actualiza la franja también al resincronizar o reconectar."""
        self._state = {
            key: deepcopy(state.get(key))
            for key in ("situacion", "configuracion", "players", "estado")
        }
        self._local_userid = local_userid
        self.update_language("")

    def clear(self) -> None:
        """Retira la carta al desconectar o volver al lobby."""
        self._state.clear()
        self.hide()

    def update_language(self, _lang_code: str) -> None:
        """Reconstruye todos los textos usando el idioma vigente."""
        view = situation_view(self._state, self._local_userid)
        if view is None:
            self.hide()
            return
        self.title_label.setText(view.title)
        self.effect_label.setText(view.description)
        self.details_label.setText("\n".join(filter(None, (view.affected, view.rolls))))
        self.details_label.setVisible(bool(view.affected or view.rolls))
        self._restricted = view.restricted
        self.apply_theme(self._theme)
        self.show()

    def apply_theme(self, theme: str) -> None:
        """Mantiene el contraste de la carta en temas claro y oscuro."""
        self._theme = theme
        dark = theme == "dark"
        background = "#282d38" if dark else "#eef3ff"
        foreground = "#edf2ff" if dark else "#243453"
        detail = "#c9d3e8" if dark else "#465b7f"
        border = "#d8a44c" if self._restricted else "#6483d5"
        self.setStyleSheet(
            f"#situationBanner {{ background: {background}; color: {foreground}; "
            f"border: 1px solid {border}; border-left: 4px solid {border}; "
            "border-radius: 6px; } "
            f"#situationBanner QLabel {{ color: {foreground}; background: transparent; "
            "border: none; } "
            "#situationTitle { font-weight: 700; } "
            f"#situationDetails {{ color: {detail}; }}"
        )
