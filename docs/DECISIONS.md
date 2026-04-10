# DECISIONS (ADR) – Pyteg

Este documento registra decisiones de arquitectura y sus motivaciones.

## ADR-001: Cliente-Servidor con mensajes tipificados
- Contexto: Necesidad de multijugador y UI reactiva.
- Decisión: Arquitectura TCP cliente-servidor. Mensajes tipificados en `server_msg.py` y transmisores `server_transmisor.py`/`client_transmisor.py`.
- Consecuencias: Facilita validaciones centralizadas y broadcast selectivo. Exige mantener compatibilidad de protocolo.

## ADR-002: Validación estricta de turnos en el servidor
- Contexto: Se detectó que los jugadores podían agregar unidades fuera de su turno.
- Decisión: Validar en `ServerTaskAgregarUnidad` (y análogos) que sea el turno del cliente actual, y que el juego haya comenzado.
- Consecuencias: Previene acciones indebidas. Se reflejan errores vía chat.
- Referencia: Commit 947060a – “Fix: Prevenir agregar unidades fuera del turno del jugador”.

## ADR-003: Sistema de chat tipificado para errores y sistema
- Contexto: Se necesitaba feedback claro de acciones no permitidas.
- Decisión: `MsgChat` con tipos: normal, error, system. Métodos `enviar_error_chat` y `enviar_sistema` en `ServerTransmisor`.
- Consecuencias: UX clara; centraliza manejo de errores.
- Referencia: Commit 2e82a38 – “Implementar sistema completo de mensajes de error en chat”.

## ADR-004: Publicar resultado de batalla a todos los clientes
- Contexto: Falta de feedback de batallas; solo se actualizaba el mapa.
- Decisión: `MsgResultadoBatalla` con dados, pérdidas y conquista; `ServerTaskAtacar` difunde resultado y luego mapa.
- Consecuencias: Transparencia de combate y trazabilidad (logging extenso).
- Referencia: Commit e1d1709 – “Implementar sistema completo de resultados de batalla”.

## ADR-005: Estado de toolbar dependiente de conexión y selección
- Contexto: Necesidad de UX consistente.
- Decisión: Toolbar habilita/inhabilita botones según conexión y selección de países; “Finalizar Turno” siempre habilitado.
- Consecuencias: Reduce errores de usuario; comunica estado de la app.

## ADR-006: mypy estricto en el proyecto
- Contexto: Aumentar confianza en refactor y contratos entre módulos.
- Decisión: Configuración `[tool.mypy] strict = true` en `pyproject.toml` sobre `pyteg/`, `tests/` y `scripts/`; ejecución local (`uv run mypy`) y en CI.
- Consecuencias: Los PR deben pasar mypy; stubs de terceros (p. ej. PySide6) pueden requerir ajustes puntuales.

## ADR-007: Tamaño de AttackDialog 400x280
- Contexto: Mejorar legibilidad de opciones.
- Decisión: Aumentar tamaño fijo a 400x280.
- Consecuencias: Mejor UX en selección de dados y opciones.

## ADR-008: UV como gestor de dependencias
- Contexto: Velocidad y aislamiento reproducible.
- Decisión: Adoptar UV para sync/run y hatch para builds.
- Consecuencias: Comandos canon homogenizados (README y scripts).

## ADR-009: TCP sin cifrado y red de confianza
- Contexto: Pyteg es un juego multijugador local o en red cercana; añadir TLS y autenticación fuerte incrementa complejidad de despliegue y protocolo.
- Decisión: Mantener el transporte como **TCP en claro**; documentar que el modelo de amenaza asume red/host de confianza (p. ej. LAN).
- Consecuencias: No protege contra escuchas ni clientes arbitrarios en redes abiertas; operadores deben acotar el puerto con firewall o VPN si exponen el servidor. Extensiones futuras (TLS, token de sala) quedan como posibles evoluciones explícitas del protocolo.

## Cómo proponer nuevas decisiones
1. Agregar una nueva sección ADR-00X con contexto, decisión, consecuencias y referencias.
2. Enlazar commits/PRs cuando sea posible.
