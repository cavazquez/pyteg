"""Fases autoritativas de un turno y su matriz de comandos.

El cliente puede usarlas para habilitar controles, pero el servidor conserva
la decisión final. ``colocacion`` termina cuando el jugador consume todos sus
refuerzos; recién entonces se habilitan ataques, movimientos y el cierre del
turno.

Los comandos mutantes aparecen exactamente en una fase. Las consultas sin
efectos laterales, como ``solicitar_tarjetas``, no necesitan una fase y se
validan únicamente contra el estado global de la partida.
"""

from __future__ import annotations

FASE_COLOCACION = "colocacion"
FASE_ACCIONES = "acciones"

FASES_VALIDAS = frozenset({FASE_COLOCACION, FASE_ACCIONES})

# Política autoritativa del protocolo. Mantenerla aquí evita que cada tarea
# vuelva a definir qué puede hacer durante un turno y permite revisar la
# superficie completa de comandos en un único lugar.
COMANDOS_POR_FASE: dict[str, frozenset[str]] = {
    FASE_COLOCACION: frozenset({
        "agregar_unidad",
        "canjear_tarjetas",
        "canje_especial",
    }),
    FASE_ACCIONES: frozenset({
        "atacar",
        "mover_unidad",
        "reclamar_tarjeta",
        "canjear_misil",
        "lanzar_misil",
        "proponer_pacto",
        "aceptar_pacto",
        "romper_pacto",
        "finalizar_turno",
    }),
}

FASE_POR_COMANDO: dict[str, str] = {
    comando: fase
    for fase, comandos in COMANDOS_POR_FASE.items()
    for comando in comandos
}

COMANDOS_SIN_FASE = frozenset({"solicitar_tarjetas"})
