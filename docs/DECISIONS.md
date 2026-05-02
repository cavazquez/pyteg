# DECISIONS (ADR) – Pyteg

Este documento registra decisiones de arquitectura y sus motivaciones.

## ADR-001: Cliente-Servidor con mensajes tipificados
- Contexto: Necesidad de multijugador y UI reactiva.
- Decisión: Arquitectura TCP cliente-servidor. Mensajes tipificados en `pyteg/server/msg/` y `pyteg/client/msg/`, con transmisores `pyteg/server/conexion/transmisor.py` y `pyteg/client/conexion/transmisor/transmisor.py`.
- Consecuencias: Facilita validaciones centralizadas y broadcast selectivo. El protocolo JSON evoluciona de forma explícita; los cambios incompatibles se documentan en ADR (p. ej. ADR-012).

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

## ADR-010: Splits por dominio de `protocols`, `exceptions` y `logger`
- Contexto: Módulos monolíticos (`protocols.py`, `exception.py`, `logger.py`) concentraban muchas responsabilidades y dificultaban revisión y navegación.
- Decisión: Reorganizar en paquetes por dominio o responsabilidad (`pyteg/protocols/{client,server,game,mapa}`, `pyteg/exceptions/{base,system,game_rules}`, `pyteg/logger/{config,retention,formatter,handlers,process,manager}`), con `__init__.py` que reexporta la API pública. Sin capas de compatibilidad (“shims”): cada migración actualiza todos los importadores en el mismo cambio.
- Consecuencias: Imports más largos solo donde se importa un símbolo interno; los puntos de entrada habituales siguen siendo `from pyteg.protocols import …`, `from pyteg.exceptions import …`, `from pyteg.logger import get_logger`. Rompe código externo que importara rutas antiguas (no era API estable de librería).

## ADR-011: Protocolos para tipar `Gui` visto desde tareas y managers
- Contexto: Tras modularizar la GUI, las tareas y los managers tomaban `main_window: Any` y abundaban `hasattr` defensivos.
- Decisión: Introducir `GameWindowProtocol` (`pyteg/client/tasks/protocols.py`) para `IClientTask.run` y `MainWindowProtocol` (`pyteg/gui/managers/protocols.py`) que extiende el anterior para los gestores. Sub-objetos con tipos que arrastran dependencias Qt/GUI se declaran como `Any` en el protocolo; el cumplimiento sigue siendo estructural vía Mypy. Atributos que solo los managers tocaban como privados de `Gui` se promovieron a públicos donde hacía falta tipar sin `# noqa: SLF001`. En `Gui.__init__`, los gestores se construyen pasando `cast(MainWindowProtocol, self)` porque los sub-gestores se asignan de forma incremental antes de que existan todos los campos del protocolo.
- Consecuencias: Menos acoplamiento conceptual a `Any`, menos `hasattr(main_window, …)` donde el contrato es estable; los padres `QWidget` en diálogos usan `cast(QWidget, …)` en el sitio de llamada. Un smoke test (`tests/test_gui_protocol_compat.py`) comprueba presencia de métodos/atributos clave sin levantar `QApplication` completo.

## ADR-012: Identidad canónica del jugador = `userid` (int) en dominio y wire format
- Contexto: En el dominio (mapa, turnos, canjes, validadores, combate, objetivos) se usaba el **nombre** (`str`) como clave, mientras otras partes del servidor (colores, lobby, temporizador) ya usaban **userid** (`int`). Eso mezclaba identidades, desalineaba tipos en mensajes (`MsgPais` como int pero alimentado con nombres) y produjo bugs (comparaciones `str` vs `int`, lookups inviables).
- Decisión: En **dominio servidor** y en los **mensajes JSON que transportan identidad de jugador**, la identidad canónica es **`userid: int`**. `username` queda para **presentación** (UI/chat). Donde el tipo JSON y el contenido estaban desalineados, se ajusta el payload (p. ej. `ganador_id`, `atacante_id`/`defensor_id`, `jugador_id` en misiles).
- Consecuencias: **Se rompe compatibilidad de protocolo** entre clientes y servidores de versiones mezcladas; desplegar cliente y servidor alineados. Los tests deben modelar dueños de país y turnos como enteros; no basar reglas en nombres de usuario.

## Cómo proponer nuevas decisiones
1. Agregar una nueva sección ADR-00X con contexto, decisión, consecuencias y referencias.
2. Enlazar commits/PRs cuando sea posible.
