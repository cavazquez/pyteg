"""Panel lateral UNIDADES (filas con íconos circulares y totales por tipo)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPixmap
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

if TYPE_CHECKING:
    from pyteg.gui.managers.protocols import MainWindowProtocol


def setup_continent_values(
    main_window: MainWindowProtocol, layout: QVBoxLayout
) -> None:
    """Crea la sección UNIDADES con filas ordenadas e íconos."""
    section = QFrame()
    section.setFrameShape(QFrame.Shape.StyledPanel)
    section.setObjectName("unitsSection")

    section_layout = QVBoxLayout(section)
    section_layout.setContentsMargins(10, 10, 10, 10)
    section_layout.setSpacing(6)

    title = QLabel("UNIDADES")
    title.setAlignment(Qt.AlignmentFlag.AlignLeft)
    title.setObjectName("unitsTitle")
    section_layout.addWidget(title)

    main_window.value_labels = {}
    main_window.row_widgets = {}
    main_window.last_units = {}

    _create_unit_row(
        main_window,
        section_layout,
        key="Generales",
        value=0,
        icon_color="#2E7D32",
        glyph="G",
        tooltip="Unidades generales disponibles para colocar",
    )

    _create_unit_row(
        main_window,
        section_layout,
        key="Misiles",
        value=0,
        icon_color="#D32F2F",
        glyph="M",
        tooltip="Misiles disponibles",
    )
    main_window.row_widgets["Misiles"].setVisible(False)

    for cont in [
        "América del Sur",
        "América del Norte",
        "Europa",
        "Asia",
        "África",
        "Oceanía",
    ]:
        _create_unit_row(
            main_window,
            section_layout,
            key=cont,
            value=0,
            icon_color="#1565C0",
            glyph="C",
            tooltip=f"Refuerzos por control de {cont}",
        )

    layout.addWidget(section)
    main_window.theme_manager._apply_units_theme(section)  # noqa: SLF001


def _create_unit_row(  # noqa: PLR0913, PLR0917
    main_window: MainWindowProtocol,
    parent_layout: QVBoxLayout,
    key: str,
    value: int,
    icon_color: str,
    glyph: str,
    tooltip: str,
) -> None:
    """Crea una fila (ícono dibujado + etiqueta) y la registra en value_labels."""
    row = QFrame()
    row.setObjectName("unitRow")
    row_layout = QHBoxLayout(row)
    row_layout.setContentsMargins(4, 4, 4, 4)
    row_layout.setSpacing(6)

    icon_label = _make_circle_icon(icon_color, glyph)
    row_layout.addWidget(icon_label)

    label = QLabel(f"{key}: {value}")
    label.setObjectName("unitRowLabel")
    row_layout.addWidget(label)

    spacer = QWidget()
    spacer.setSizePolicy(
        QSizePolicy.Policy.Expanding,
        QSizePolicy.Policy.Preferred,
    )
    row_layout.addWidget(spacer)

    parent_layout.addWidget(row)
    main_window.value_labels[key] = label
    main_window.row_widgets[key] = row
    row.setToolTip(tooltip)


def _make_circle_icon(color_hex: str, glyph: str | None) -> QLabel:
    """Crea un QLabel con un QPixmap de círculo y opcional glifo.

    Returns:
        QLabel con el icono de círculo creado.

    """
    size = 16
    pm = QPixmap(size, size)
    pm.fill(QColor(0, 0, 0, 0))
    painter = QPainter(pm)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setBrush(QColor(color_hex))
    painter.setPen(QColor(color_hex))
    painter.drawEllipse(0, 0, size - 1, size - 1)
    if glyph:
        painter.setPen(QColor("white"))
        font = QFont()
        font.setPointSize(8)
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(
            pm.rect(),
            Qt.AlignmentFlag.AlignCenter,
            glyph,
        )
    painter.end()
    label = QLabel()
    label.setPixmap(pm)
    return label
