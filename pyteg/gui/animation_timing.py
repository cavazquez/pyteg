"""Tiempos compartidos por las animaciones del mapa y los bots locales."""

BOT_ACTION_INTERVAL_MS = 1000
"""Pausa habitual entre dos acciones automáticas."""

BATTLE_HIGHLIGHT_DURATION_MS = 2500
"""Tiempo para señalar los países que participan en un ataque."""

UNIT_LOSS_DURATION_MS = 2000
"""Tiempo para leer las pérdidas de una batalla."""

UNIT_GAIN_DURATION_MS = 900
"""Tiempo para señalar las unidades que recibe un país."""

BOT_BATTLE_PAUSE_MS = BATTLE_HIGHLIGHT_DURATION_MS + UNIT_LOSS_DURATION_MS
"""El bot espera a que terminen los efectos antes de volver a actuar."""
