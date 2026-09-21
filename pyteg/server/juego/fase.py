"""Fases autoritativas de un turno.

El cliente puede usarlas para habilitar controles, pero el servidor conserva
la decisión final.  ``colocacion`` termina cuando el jugador consume todos
sus refuerzos; recién entonces se habilitan ataques, movimientos y el cierre
del turno.
"""

from __future__ import annotations

FASE_COLOCACION = "colocacion"
FASE_ACCIONES = "acciones"

FASES_VALIDAS = frozenset({FASE_COLOCACION, FASE_ACCIONES})
