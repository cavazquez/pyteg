"""Constantes del juego centralizadas.

Este módulo contiene todas las constantes utilizadas en el juego
para evitar valores hardcodeados y mejorar mantenibilidad.
"""

from __future__ import annotations

from typing import NamedTuple

# Tema de mapa por defecto (assets en themes/{nombre}/)
DEFAULT_MAP_THEME = "classic"
"""Nombre del tema de mapa usado por servidor y cliente."""

# Configuración de turnos
DEFAULT_TURN_SECONDS = 20
"""Segundos por defecto para cada turno."""

# Configuración de victoria
DEFAULT_VICTORY_COUNTRIES = 30
"""Cantidad de países necesarios para ganar por defecto."""

VICTORY_ALL_COUNTRIES = 0
"""Valor especial que indica que se necesita controlar todos los países."""

# Configuración de unidades
MIN_UNITS_FOR_ATTACK = 2
"""Mínimo de unidades necesarias en un país para poder atacar."""

MIN_UNITS_TO_LEAVE = 1
"""Mínimo de unidades que deben quedar en un país después de mover/atacar."""

# Configuración de misiles
MISSILE_UNIT_COST = 6
"""Cantidad de unidades necesarias para canjear un misil."""

MISSILE_MAX_DISTANCE = 3
"""Distancia máxima (en saltos) para lanzar un misil."""

# Configuración de canjes de tarjetas
EXCHANGE_UNITS: dict[int, int] = {
    0: 4,  # Primer canje: 4 unidades
    1: 7,  # Segundo canje: 7 unidades
}
"""Progresión de unidades por canje de tarjetas.

El primer canje (índice 0) da 4 unidades.
El segundo canje (índice 1) da 7 unidades.
A partir del tercer canje (índice >= 2): 5 * cant_canjes unidades.
"""

EXCHANGE_MULTIPLIER = 5
"""Multiplicador para canjes después del segundo (5 * cant_canjes)."""

# Configuración de canje especial
SPECIAL_EXCHANGE_UNITS = 2
"""Unidades obtenidas al canjear país + tarjeta."""

# Configuración de cálculo de unidades
MIN_GENERAL_UNITS = 3
"""Mínimo de unidades generales que recibe un jugador por turno."""

COUNTRIES_DIVISOR = 2
"""Divisor para calcular unidades generales (1 unidad por cada N países)."""

# Tipos de unidades válidos
VALID_UNIT_TYPES = {"infanteria"}
"""Tipos de unidades válidos en el juego."""

# Restricciones de turnos
FIRST_TURNS_NO_ATTACK = 2
"""Cantidad de turnos iniciales donde no se puede atacar."""

# Umbrales de tiempo para colores del timer
TIMER_COLOR_GREEN_THRESHOLD = 20
"""Segundos mínimos para mostrar el timer en verde."""

TIMER_COLOR_ORANGE_THRESHOLD = 10
"""Segundos mínimos para mostrar el timer en naranja."""

# Configuración de tarjetas
MAX_CARDS_BEFORE_FORCE_EXCHANGE = 5
"""Máximo de tarjetas que un jugador puede tener antes de forzar un canje."""

MIN_CARDS_SAME_SYMBOL_FOR_EXCHANGE = 3
"""Mínimo de tarjetas del mismo símbolo necesarias para canjear."""

# Configuración de colores
RGB_MAX_VALUE = 255
"""Valor máximo para componentes RGB (0-255)."""

HEX_COLOR_LENGTH = 6
"""Longitud esperada de un valor hexadecimal de color (sin #)."""

# Configuración de misiles - daño por distancia
MISSILE_DAMAGE_DISTANCE_1 = 3
"""Daño de misil a distancia 1."""

MISSILE_DAMAGE_DISTANCE_2 = 2
"""Daño de misil a distancia 2."""

MISSILE_DAMAGE_DISTANCE_3 = 1
"""Daño de misil a distancia 3."""


# Continentes: ID del mapa (TOML) como fuente única; derivados para GUI y turnos
class ContinentSpec(NamedTuple):
    """Metadatos de un continente del juego."""

    map_id: str
    """Identificador en TOML y mapa (ej. ``Sudamerica``)."""

    panel_label: str
    """Etiqueta del panel UNIDADES / msgid de traducción."""

    unit_suffix: str
    """Sufijo de métodos en ``SiguientesTurnos`` (ej. ``sudamerica``)."""

    bonus: int
    """Unidades de bonificación por control completo del continente."""


CONTINENTS: tuple[ContinentSpec, ...] = (
    ContinentSpec("Sudamerica", "América del Sur", "sudamerica", 3),
    ContinentSpec("Norteamerica", "América del Norte", "norteamerica", 5),
    ContinentSpec("Europa", "Europa", "europa", 5),
    ContinentSpec("Asia", "Asia", "asia", 7),
    ContinentSpec("Africa", "África", "africa", 3),
    ContinentSpec("Oceania", "Oceanía", "oceania", 2),
)
"""Registro canónico de continentes (orden = panel UNIDADES)."""

BONIFICACIONES_CONTINENTE: dict[str, int] = {
    spec.map_id: spec.bonus for spec in CONTINENTS
}
"""Bonificación por control completo; claves = ID del mapa."""

CONTINENT_PANEL_LABELS: tuple[str, ...] = tuple(spec.panel_label for spec in CONTINENTS)
"""Orden de filas de bonificación continental en el panel UNIDADES."""

MAP_CONTINENT_TO_PANEL_LABEL: dict[str, str] = {
    spec.map_id: spec.panel_label for spec in CONTINENTS
}
"""ID del mapa (TOML) → etiqueta del panel UNIDADES."""

CONTINENT_UNIT_SUFFIX: dict[str, str] = {
    spec.map_id: spec.unit_suffix for spec in CONTINENTS
}
"""ID del mapa → sufijo de métodos ``cant_unidades_*`` / ``usar_unidad_*``."""

# Configuración de UI
TITILATION_MAX_INTENSITY = 0.7
"""Intensidad máxima de titilación para efectos visuales."""

VOLUME_MEDIUM_THRESHOLD = 0.5
"""Umbral de volumen medio para iconos de sonido."""

# Configuración de tarjetas - umbrales para colores
CARD_SELECTION_ORANGE_THRESHOLD = 2
"""Umbral de tarjetas seleccionadas para mostrar color naranja."""

CARD_SELECTION_GREEN_THRESHOLD = 3
"""Umbral de tarjetas seleccionadas para mostrar color verde."""

CARDS_FOR_EXCHANGE = 3
"""Cantidad de tarjetas necesarias para realizar un canje."""
