"""Confirmación visual de la continuación que contiene un archivo de turno."""

from __future__ import annotations

from collections import Counter
from typing import TYPE_CHECKING

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QLabel,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from pyteg.i18n import translate as _

if TYPE_CHECKING:
    from pyteg.persistence.turn_preview import TurnPreview


class TurnPreviewDialog(QDialog):
    """Muestra un resumen sin exponer cartas, objetivos o tokens."""

    def __init__(self, preview: TurnPreview, parent: QWidget) -> None:
        """Presenta destinatario, estado del mapa y cambios desde la copia actual."""
        super().__init__(parent)
        self.setWindowTitle(_("Importar turno"))
        self.resize(620, 460)
        layout = QVBoxLayout(self)
        turn = preview.snapshot.get("turno") or {}
        self.summary = QLabel(
            _("Entrega {} · {} → {}\nMapa: {} · Ronda {}\nFecha: {}").format(
                preview.step + 1,
                preview.author,
                preview.recipient,
                _("Clásico")
                if preview.snapshot["theme"] == "classic"
                else _("Revancha"),
                turn.get("num_ronda", 1),
                preview.time,
            )
        )
        self.summary.setWordWrap(True)
        layout.addWidget(self.summary)
        counts = Counter(
            data["userid"] for data in preview.snapshot["countries"].values()
        )
        totals = QLabel(
            " · ".join(
                f"{player['username']}: {counts[player['userid']]}"
                for player in preview.snapshot["players"]
            )
        )
        totals.setWordWrap(True)
        layout.addWidget(QLabel(_("Países controlados:")))
        layout.addWidget(totals)
        self.changes = QTreeWidget()
        self.changes.setHeaderLabels([
            _("País"),
            _("Jugador"),
            _("Unidades"),
            _("Misiles"),
        ])
        names = {
            player["userid"]: player["username"]
            for player in preview.snapshot["players"]
        }
        for country, data in sorted(preview.changes.items()):
            self.changes.addTopLevelItem(
                QTreeWidgetItem([
                    country,
                    str(names.get(data["userid"], "—")),
                    str(data["unidades"]),
                    str(data.get("misiles", 0)),
                ])
            )
        layout.addWidget(
            QLabel(_("Cambios desde tu copia: {} países").format(len(preview.changes)))
        )
        layout.addWidget(self.changes)
        hint = QLabel(
            _(
                "Al importar se reemplaza la copia local por esta continuación. "
                "Conservá el archivo recibido para compartirlo o volver a consultarlo."
            )
        )
        hint.setWordWrap(True)
        layout.addWidget(hint)
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Open
            | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
