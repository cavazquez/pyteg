# Arquitectura de Pyteg

Este documento describe la arquitectura de alto nivel del proyecto, el flujo cliente-servidor, el sistema de mensajes y los estados relevantes de la GUI.

## Visión general
Pyteg implementa el juego TEG en un modelo cliente-servidor:
- Servidor: valida reglas del juego, procesa acciones (agregar unidades, atacar, mover, finalizar turno), mantiene el estado y difunde actualizaciones.
- Cliente: UI con PySide6, conecta al servidor, envía acciones y procesa mensajes para reflejar el estado (mapa, chat, barra de estado, diálogos).

## Seguridad y modelo de amenaza

El transporte entre cliente y servidor es **TCP en claro**, sin TLS ni autenticación fuerte entre procesos. El diseño asume **red de confianza** (típicamente LAN o anfitrión controlado): cualquier host que pueda alcanzar el puerto del servidor puede intentar conectar; el juego no ofrece cifrado ni verificación de identidad más allá de las reglas propias de la partida (p. ej. nombres de usuario).

**Riesgos conscientes:** lectura o modificación pasiva/activa del tráfico por terceros en la misma red; conexión de clientes no deseados si el puerto es accesible desde Internet sin firewall.

**Posibles extensiones futuras** (cambian el protocolo y el despliegue): TLS u otro canal cifrado, contraseña o token de sala, lista de permitidos. No hay hoja de ruta fijada; ver [DECISIONS.md](DECISIONS.md) (ADR-009).

## Módulos principales (pyteg/)
- server.py: servidor y loop principal (acepta conexiones, dirige mensajes a tareas).
- server_tasks/: paquete de tareas validadas del servidor (`lobby`, `game_actions`, `cards_missiles`; mismo API público que antes).
- server_game.py: reglas del juego, batallas y cálculo de conquistas.
- server_mapa.py: representación del mapa, países y propietarios.
- server_transmisor.py: envío tipificado de mensajes a clientes.
- server_msg/: paquete de mensajes servidor→cliente (`connection`, `map_turn`, `battle`, `cards_missiles`, etc.).
- client_connection.py: manejo de conexión y estado conectado/desconectado.
- client_tasks/: paquete de tareas de cliente (`lobby`, `game_flow`, `battle`, `cards_missiles`).
- pyteg/gui/: paquete de la GUI del cliente (`main_window`, `managers/`, `widgets/`, `dialogs/`, `mapa/`, etc.).

### Toolbar y país en el mapa (descomposición)

La barra de herramientas y el sprite de cada país se dividieron por responsabilidad para facilitar cambios aislados:

| Módulo | Rol |
|--------|-----|
| `pyteg/gui/toolbar/toolbar.py` | Clase `ToolBar`: QAction, textos, `update_language`, cableado con la ventana principal. |
| `pyteg/gui/toolbar/actions_mixin.py` | Mixin: estado de conexión, habilitar atacar/mover, mover desde la selección del mapa (el ataque va por `main_window.atacar`). |
| `pyteg/gui/toolbar/window_mixin.py` | Mixin: tamaño de ventana, pantalla completa, centrado, reset de zoom del mapa. |
| `pyteg/gui/toolbar/size.py` | Menú de tamaños predefinidos, estilos del menú/botón, `center_window_on_screen`. |
| `pyteg/gui/toolbar/icons.py` | Carga de íconos con validación de recurso (`ImagenNoEncontradaError`). |
| `pyteg/gui/mapa/pais.py` | `Pais`: pixmap, círculo de unidades, color y datos base. |
| `pyteg/gui/mapa/pais_selection_mixin.py` | Mixin: clic → `selection_manager`, oscurecimiento origen/destino. |
| `pyteg/gui/mapa/pais_battle_fx_mixin.py` | Mixin: titilación en batalla, pérdidas flotantes, contador de misiles. |

Otros módulos voluminosos de la GUI pueden seguir el mismo patrón cuando una nueva función los haga crecer de forma desordenada.

### Diálogo de tarjetas (`pyteg/gui/tarjetas/`)

| Módulo | Rol |
|--------|-----|
| `pyteg/gui/tarjetas/dialog.py` | Clase `TarjetasDialog`: layout, objetivo secreto, botones y `actualizar_tarjetas`. |
| `pyteg/gui/tarjetas/styles.py` | Cadenas QSS y helper para el color del contador de selección. |
| `pyteg/gui/tarjetas/protocols.py` | `Protocol` para tipar `self` en los mixins sin import circular. |
| `pyteg/gui/tarjetas/selection_mixin.py` | Grilla 2x2, selección, contador y reglas locales de canje. |
| `pyteg/gui/tarjetas/exchange_mixin.py` | Canje y reclamo vía `transmisor` del padre. |

- turno_protocol.py: define la interfaz `ITurno` para desacoplar el servidor de las clases de turno.
- turnos.py: implementaciones de turnos (PrimerTurno, SegundoTurno, SiguientesTurnos).
- run_client.py: punto de entrada del cliente.

## Flujo de mensajes
1) Cliente realiza acción (UI) -> client_transmisor envía mensaje al servidor.
2) server.py enruta -> ServerTask correspondiente valida precondiciones.
3) Si es válido, aplica cambios en server_game / server_mapa.
4) El servidor emite mensajes de resultado/estado a clientes mediante server_transmisor.
5) client_tasks procesa y actualiza GUI.

### Diagrama de flujo
Para una vista visual del intercambio de mensajes, ver el diagrama de secuencia en:
- `docs/diagrams/message_flow.md`

## Mensajería clave
- MsgChat (tipos: normal, error, system). Los errores de validación se publican en chat con formato y color.
- MsgResultadoBatalla: detalla dados, pérdidas y si hubo conquista. Enviado a todos tras cada ataque.
- Turno/Unidades: al inicio de cada turno, el servidor envía el turno actual y, además, las unidades disponibles al jugador activo; tras agregar unidades, vuelve a enviar unidades disponibles.
- Actualización de mapa: se emite después de acciones que modifican el estado (agregar, mover, atacar, conquista).

## Reglas e invariantes
- Turnos: solo el jugador del turno puede realizar acciones. Validado en todas las tareas relevantes.
- Ataques: restringidos en los dos primeros turnos; requieren países adyacentes, dueño válido y unidades suficientes; el atacante puede lanzar 1 a 3 dados según unidades.
- Movimiento: requiere adyacencia y unidades disponibles (no vaciar país origen si la regla lo impide).
- Chat de errores: toda acción inválida genera un mensaje de error visible para el jugador con formato ⚠️ rojo.

## Arquitectura modular de la GUI

La interfaz gráfica ha sido refactorizada en una arquitectura modular para mejorar mantenibilidad, legibilidad y escalabilidad:

### Ventana principal (`pyteg/gui/main_window.py`)
- **Responsabilidad**: Coordinación de gestores, eventos de Qt, ventanas auxiliares
- **Gestores integrados**: Instancia y coordina todos los gestores especializados
- **Reducción**: 65% menos líneas (de ~1039 a 366 líneas)

### Gestores especializados

#### LayoutManager (`pyteg/gui/managers/layout.py`)
- **Responsabilidad**: Estructura visual, widgets base, layout de ventana
- **Funciones clave**: Creación de paneles, configuración de splitters, iconos

#### ThemeManager (`pyteg/gui/managers/theme.py`)
- **Responsabilidad**: Gestión de temas claro/oscuro, estilos CSS
- **Funciones clave**: Aplicación de temas, toggle de modo, estilos por componente

#### PlayersManager (`pyteg/gui/managers/players.py`)
- **Responsabilidad**: Lista de jugadores, widgets de jugador, indicadores de color
- **Funciones clave**: Actualización de lista, creación de widgets, iconos circulares

#### StatusManager (`pyteg/gui/managers/status.py`)
- **Responsabilidad**: Barra de estado, información de jugador actual, mensajes
- **Funciones clave**: Actualización de estado de juego, información de turno

#### UnitsManager (`pyteg/gui/managers/units.py`)
- **Responsabilidad**: Panel de unidades disponibles, efectos visuales
- **Funciones clave**: Actualización de unidades, efectos de flash, estilos

#### GameActionsManager (`pyteg/gui/managers/game_actions.py`)
- **Responsabilidad**: Acciones del juego (atacar, finalizar turno)
- **Funciones clave**: Lógica de ataque, finalización de turno, cálculo de unidades

### Beneficios de la arquitectura modular
- **Separación de responsabilidades**: Cada gestor tiene una función específica
- **Mantenibilidad**: Fácil localización y modificación de funcionalidad
- **Escalabilidad**: Nuevas funcionalidades pueden agregarse sin impactar otros módulos
- **Testabilidad**: Cada gestor puede ser probado independientemente
- **Legibilidad**: Código más organizado y comprensible

## Estados de la GUI
- Toolbar (`pyteg/gui/toolbar/`):
  - Botón Conectar habilitado cuando no hay conexión; al conectar se deshabilita.
  - Botones Atacar y Mover habilitados solo cuando hay 2 países seleccionados y hay conexión.
  - Botón Finalizar Turno permanece siempre habilitado.
- Selección de países (`pyteg/gui/mapa/scene.py` + `selection_manager.py`): gestiona origen/destino y notifica a la toolbar.
- Chat (`pyteg/gui/widgets/chat/`): mensajes tipificados con color por usuario.
- AttackDialog (`pyteg/gui/dialogs/attack.py`): tamaño 400x280 para mejor visualización.

## Logging y depuración
- Logging detallado en batallas: estado antes/después, dados, pérdidas, conquista.
- Logs del servidor y cliente configurables vía logging.conf.

## Pruebas y calidad
- Suite en `tests/` ejecutada con `python -m unittest discover` (orden de magnitud: >200 casos).
- **Tests de Integración**: `tests/test_integration.py` levanta un servidor TCP real en un hilo separado y conecta clientes reales con sockets para validar el protocolo de mensajes JSON end-to-end.
- [`run_tests.sh`](../run_tests.sh) ejecuta Ruff (formato, check con fixes), mypy según `[tool.mypy]` en `pyproject.toml`, y cobertura con `coverage run --branch`.
- El workflow [`.github/workflows/ruff-uv.yml`](../.github/workflows/ruff-uv.yml) en CI ejecuta Ruff, unittest, mypy y reporte de cobertura.

## Extensión del protocolo
Guías en docs/ sobre cómo crear mensajes cliente-servidor y bidireccionales. Ver:
- docs/como_crear_mensaje_cliente_a_servidor.md
- docs/como_crear_mensaje_servidor_a_cliente.md
- docs/como_crear_mensaje_bidireccional.md
