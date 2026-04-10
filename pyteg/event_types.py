"""Módulo para definir tipos de eventos del sistema.

Este módulo centraliza las constantes para los tipos de eventos que se pueden
publicar y suscribir en el MessageBus.
"""

# Eventos de juego
EVENT_MAPA_ACTUALIZADO = "mapa_actualizado"
EVENT_BATALLA_RESULTADO = "batalla_resultado"
EVENT_MISIL_LANZADO = "misil_lanzado"
EVENT_MISIL_AGREGADO = "misil_agregado"
EVENT_TURNO_CAMBIADO = "turno_cambiado"
EVENT_VICTORIA = "victoria"
EVENT_UNIDADES_DISPONIBLES = "unidades_disponibles"

# Eventos de chat
EVENT_CHAT = "chat"
EVENT_ERROR_CHAT = "error_chat"
EVENT_SISTEMA = "sistema"

# Eventos de configuración
EVENT_CONFIGURACION_PARTIDA = "configuracion_partida"
EVENT_ESTADO_CAMBIADO = "estado_cambiado"

# Eventos de jugadores
EVENT_JUGADOR_CONECTADO = "jugador_conectado"
EVENT_JUGADOR_DESCONECTADO = "jugador_desconectado"
EVENT_COLOR_ASIGNADO = "color_asignado"
EVENT_USERNAME_CAMBIADO = "username_cambiado"

# Eventos de tarjetas
EVENT_TARJETAS_ACTUALIZADAS = "tarjetas_actualizadas"
EVENT_TARJETA_RECLAMADA = "tarjeta_reclamada"
EVENT_CANJE_REALIZADO = "canje_realizado"

# Eventos de unidades
EVENT_UNIDAD_AGREGADA = "unidad_agregada"
EVENT_UNIDAD_MOVIDA = "unidad_movida"
EVENT_ATAQUE_INICIADO = "ataque_iniciado"
