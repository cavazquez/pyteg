"""Visor de repeticiones de sólo lectura, independiente de la partida activa."""

from __future__ import annotations

from bisect import bisect_left, bisect_right
from typing import TYPE_CHECKING

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QDialog,
    QGraphicsView,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QPushButton,
    QSlider,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from pyteg.gui.mapa.projection import render_countries
from pyteg.gui.mapa.scene import QCustomGraphicsScene
from pyteg.i18n import translate as _

if TYPE_CHECKING:
    from PySide6.QtWidgets import (
        QGraphicsSceneContextMenuEvent,
        QGraphicsSceneMouseEvent,
    )

    from pyteg.persistence.history import Replay

_ACTION_LABELS = {
    "atacar": "Ataque",
    "mover_unidad": "Movimiento",
    "agregar_unidad": "Refuerzos",
    "finalizar_turno": "Fin de turno",
    "empezar_partida": "Inicio de partida",
    "canjear_tarjetas": "Canje de tarjetas",
    "canje_especial": "Canje de país",
    "canjear_misil": "Misil obtenido",
    "lanzar_misil": "Misil lanzado",
    "reclamar_tarjeta": "Tarjeta obtenida",
    "_TurnExpired": "Tiempo agotado",
    "_ClientDisconnected": "Jugador desconectado",
}


class _ReadOnlyScene(QCustomGraphicsScene):
    """El mapa histórico no selecciona ni ofrece acciones de juego."""

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent) -> None:  # noqa: N802
        event.accept()

    def contextMenuEvent(self, event: QGraphicsSceneContextMenuEvent) -> None:  # noqa: N802
        event.accept()

    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent) -> None:  # noqa: N802
        event.accept()


class ReplayWindow(QDialog):
    """Navegación por acción o turno con reproducción automática del mapa."""

    def __init__(self, replay: Replay, parent: QWidget | None = None) -> None:
        """Construye una vista del mapa que nunca usa un transmisor."""
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        self.setWindowTitle(_("Historial y repetición"))
        self.resize(1080, 740)
        self.replay = replay
        self.scene = _ReadOnlyScene(self, theme=replay.snapshot(0)["theme"])
        self.view = QGraphicsView(self.scene)
        self.view.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.view.setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)
        self.records = QListWidget()
        self.records.addItem(_("Estado inicial"))
        for record in replay.records:
            action = _(_ACTION_LABELS.get(record["action"], "Estado de partida"))
            turn = record.get("turn") or {}
            self.records.addItem(
                f"{turn.get('num_turno', '—')} · {action} · "
                f"{record.get('userid') or '—'}"
            )
        self.records.currentRowChanged.connect(self.seek)
        splitter = QSplitter()
        splitter.addWidget(self.view)
        splitter.addWidget(self.records)
        splitter.setSizes([800, 280])
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setRange(0, replay.count - 1)
        self.slider.valueChanged.connect(self.seek)
        controls = QHBoxLayout()
        self.play_button = QPushButton(_("Reproducir"))
        self.play_button.clicked.connect(self.toggle_play)
        controls.addWidget(self.play_button)
        self._turn_buttons: dict[str, QPushButton] = {}
        for text, direction in (("Turno anterior", -1), ("Turno siguiente", 1)):
            button = QPushButton(_(text))
            self._turn_buttons[text] = button
            button.clicked.connect(
                lambda _checked=False, step=direction: self.jump_turn(step)
            )
            controls.addWidget(button)
        controls.addWidget(self.slider, 1)
        self.details = QLabel()
        self.details.setWordWrap(True)
        layout = QVBoxLayout(self)
        layout.addWidget(splitter, 1)
        layout.addLayout(controls)
        layout.addWidget(self.details)
        self._timer = QTimer(self)
        self._timer.setInterval(750)
        self._timer.timeout.connect(self._advance)
        self.finished.connect(self._timer.stop)
        self.seek(0)
        QTimer.singleShot(0, self._fit_map)

    def update_language(self, _lang_code: str | None = None) -> None:
        """Actualiza textos sin cambiar la posición de la repetición."""
        self.setWindowTitle(_("Historial y repetición"))
        self.play_button.setText(
            _("Pausar") if self._timer.isActive() else _("Reproducir")
        )
        for label, button in self._turn_buttons.items():
            button.setText(_(label))
        current = self.slider.value()
        self.records.blockSignals(True)  # noqa: FBT003 -- API Qt.
        self.records.clear()
        self.records.addItem(_("Estado inicial"))
        for record in self.replay.records:
            action = _(_ACTION_LABELS.get(record["action"], "Estado de partida"))
            turn = record.get("turn") or {}
            self.records.addItem(
                f"{turn.get('num_turno', '—')} · {action} · "
                f"{record.get('userid') or '—'}"
            )
        self.records.blockSignals(False)  # noqa: FBT003 -- API Qt.
        self.seek(current)

    def _fit_map(self) -> None:
        self.view.fitInView(
            self.scene.itemsBoundingRect(), Qt.AspectRatioMode.KeepAspectRatio
        )

    def seek(self, index: int) -> None:
        """Muestra una posición y sincroniza la lista y el deslizador."""
        if not 0 <= index < self.replay.count:
            return
        snapshot = self.replay.snapshot(index)
        render_countries(self.scene, snapshot)
        for control, setter in (
            (self.slider, self.slider.setValue),
            (self.records, self.records.setCurrentRow),
        ):
            control.blockSignals(True)  # noqa: FBT003 -- API Qt.
            setter(index)
            control.blockSignals(False)  # noqa: FBT003 -- API Qt.
        turn = snapshot.get("turno") or {}
        players = {
            player["userid"]: player["username"] for player in snapshot["players"]
        }
        who = players.get(turn.get("jugador_id"), "—")
        summary = (
            f"{index + 1}/{self.replay.count} · {_('Turno')} "
            f"{turn.get('num_turno', '—')} · {who}"
        )
        if index:
            record = self.replay.records[index - 1]
            payload = record.get("payload", {})
            countries = [
                str(payload[key])
                for key in ("pais", "origen", "destino", "pais_origen", "pais_destino")
                if key in payload
            ]
            summary += " · " + " → ".join(countries) if countries else ""
            for event in record.get("events", []):
                dice = [
                    str(event[key])
                    for key in ("dados_atacante", "dados_defensor")
                    if key in event
                ]
                if dice:
                    summary += f" · {_('Dados')}: {' / '.join(dice)}"
        self.details.setText(summary)

    def jump_turn(self, direction: int) -> None:
        """Salta al comienzo del turno anterior o siguiente."""
        starts = self.replay.turn_indices()
        current = self.slider.value()
        target = (
            bisect_right(starts, current)
            if direction > 0
            else bisect_left(starts, current) - 1
        )
        if 0 <= target < len(starts):
            self.seek(starts[target])

    def toggle_play(self) -> None:
        """Alterna reproducción automática y pausa."""
        if self._timer.isActive():
            self._timer.stop()
            self.play_button.setText(_("Reproducir"))
        else:
            if self.slider.value() == self.replay.count - 1:
                self.seek(0)
            self.play_button.setText(_("Pausar"))
            self._timer.start()

    def _advance(self) -> None:
        if self.slider.value() == self.replay.count - 1:
            self.toggle_play()
        else:
            self.seek(self.slider.value() + 1)
