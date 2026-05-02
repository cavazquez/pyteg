"""Hojas de estilo (QSS) usadas por la barra de estado.

Se mantienen como constantes para facilitar su reutilización y testeo.
"""

from __future__ import annotations

LABEL_BOLD_STYLE = "font-weight: 600;"
"""Negrita ligera para etiquetas de turno y nombre del jugador."""

LABEL_MUTED_STYLE = "color: #555;"
"""Tono apagado para textos secundarios (`Mi jugador:` etc.)."""

MI_COLOR_INDICATOR_DEFAULT_STYLE = """
    background-color: #cccccc;
    border: 1px solid #999999;
    border-radius: 2px;
"""
"""Estado por defecto del cuadradito coloreado del jugador local."""

TIMER_LABEL_STYLE = "font-weight: bold; padding: 2px 8px;"
"""Estilo del temporizador alojado en la barra de estado."""
