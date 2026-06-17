# Arquitectura de Pyteg

Este documento describe la arquitectura de alto nivel del proyecto, el flujo cliente-servidor, el sistema de mensajes y los estados relevantes de la GUI.

## Visión general
Pyteg implementa el juego TEG en un modelo cliente-servidor:
- Servidor: valida reglas del juego, procesa acciones (agregar unidades, atacar, mover, finalizar turno), mantiene el estado y difunde actualizaciones.
- Cliente: UI con PySide6, conecta al servidor, envía acciones y procesa mensajes para reflejar el estado (mapa, chat, barra de estado, diálogos).

### Identidad del jugador (dominio vs presentación)
- **Dominio (servidor / core)**: el jugador se identifica de forma canónica con **`userid: int`** (dueño de país en el mapa, orden de turnos, canjes, validadores, combate, objetivos secretos, victoria).
- **Presentación**: el **`username`** es texto para UI/chat; no debe usarse como clave de reglas cuando exista `userid`.
- **Red**: los mensajes que transportan identidad usan **`userid`/`user_id` como number JSON** cuando corresponde; ver `docs/mensajes_servidor.md` y `docs/DECISIONS.md` (ADR-012).

## Seguridad y modelo de amenaza

El transporte entre cliente y servidor es **TCP en claro**, sin TLS ni autenticación fuerte entre procesos. El diseño asume **red de confianza** (típicamente LAN o anfitrión controlado): cualquier host que pueda alcanzar el puerto del servidor puede intentar conectar; el juego no ofrece cifrado ni verificación de identidad más allá de las reglas propias de la partida (p. ej. nombres de usuario).

**Riesgos conscientes:** lectura o modificación pasiva/activa del tráfico por terceros en la misma red; conexión de clientes no deseados si el puerto es accesible desde Internet sin firewall.

**Posibles extensiones futuras** (cambian el protocolo y el despliegue): TLS u otro canal cifrado, contraseña o token de sala, lista de permitidos. No hay hoja de ruta fijada; ver [DECISIONS.md](DECISIONS.md) (ADR-009).

## Módulos principales (pyteg/)
- `pyteg/server/app.py`: servidor y loop principal (acepta conexiones, dirige mensajes a tareas). Entry point: `uv run pyteg-server`.
- `pyteg/server/tasks/`: paquete de tareas validadas del servidor (`lobby`, `game_actions/`, `cards_missiles/`; mismo API público que antes).
- `pyteg/server/juego/game.py`: reglas del juego, batallas y cálculo de conquistas.
- `pyteg/server/juego/mapa.py`: representación del mapa, países y propietarios.
- `pyteg/server/conexion/transmisor.py`: envío tipificado de mensajes a clientes.
- `pyteg/server/conexion/broadcaster.py`: difusión de mensajes a todos los clientes conectados.
- `pyteg/server/msg/`: paquete de mensajes servidor→cliente (`connection`, `map_turn`, `battle`, `cards_missiles`, etc.).
- `pyteg/client/app.py`: cliente del juego (estado de usuario, transmisor, etc.).
- `pyteg/client/run.py`: punto de entrada del cliente. Entry point: `uv run pyteg-client`.
- `pyteg/client/conexion/connection.py`: manejo de conexión y estado conectado/desconectado.
- `pyteg/client/conexion/transmisor/`: paquete con `ClientTransmisor` y `ClientNullTransmisor`.
- `pyteg/client/msg/`: paquete de mensajes cliente→servidor (`lobby`, `actions`, `cards`, `missiles`).
- `pyteg/client/tasks/`: paquete de tareas de cliente (`lobby/`, `game_flow/`, `battle`, `cards_missiles`).
- `pyteg/core/`: dominio puro reutilizable.
  - `core/mapa/`: `CountryData` (estado runtime), `ThemeCountryLayout` / `ThemeContinentLayout` (layout TOML) y constructor del mapa (`build_mapa`, `build_mapa_from_reader`).

### Temas de mapa (`themes/{nombre}/`)
- **Fuente de verdad**: `TomlReader.from_theme(nombre, strict=True)` carga `paises.toml`, y opcionalmente `cartas.toml`, `adyacencias.toml` y `objetivos_secretos.toml`.
- **Constante**: `DEFAULT_MAP_THEME = "classic"` en `pyteg/config.py`; servidor acepta `--theme`; cliente usa `map_theme` en `Gui` y `QCustomGraphicsScene`.
- **Símbolos de cartas**: claves de `[Cartas]` en TOML (orden = reparto en `Mazo`); `TarjetaWidget` resuelve imágenes vía `pyteg/core/theme_resources.py`.
- **Limitación conocida**: cliente y servidor no negocian el tema por red; deben usar el mismo valor manualmente.
  - `core/cartas/`: mazo y tarjeta de país.
  - `core/turnos/`: protocolo `ITurno`, implementaciones (`turnos.py`) y temporizador.
  - `core/combate/`: `batalla`, `dados`, `calculos` y sistema de misiles. `core/combate/protocols.py` define `MapaCalculos` (Protocol estructural usado por `calculos`).
  - `core/partida/`: contexto, manager de cartas/turnos, comprobador de victoria, configuración y objetivos secretos.
- `pyteg/gui/`: paquete de la GUI del cliente (`main_window`, `managers/`, `widgets/`, `dialogs/`, `mapa/`, `tarjetas/`, `toolbar/`, `status_bar/`).

### Infraestructura transversal y tipado estático

Paquetes en la raíz de `pyteg/` que centralizan contratos y utilidades compartidas (imports públicos vía `__init__.py` de cada paquete):

| Ubicación | Contenido |
|-----------|-----------|
| `pyteg/protocols/` | `Protocol` por dominio servidor/cliente: `IClientProtocol`, `ServerLikeProtocol`, `IGameProtocol`, `IMapProtocol` (`client.py`, `server.py`, `game.py`, `mapa.py`). Consumidos por tareas del servidor y validadores. |
| `pyteg/exceptions/` | Excepciones por familia: `base.py` (`PyTegError`), `system.py` (mensajes/estado/recursos), `game_rules.py` (`GameRuleViolationError` y subclases). Import canónico: `from pyteg.exceptions import …`. |
| `pyteg/logger/` | Logging por responsabilidad (`config`, `retention`, `formatter`, `handlers`, `process`, `manager`); API pública estable: `get_logger`, `set_console_level`, `set_file_level`, `configure_logging`, `logger`. |

Tipado estructural de la ventana principal (`Gui`):

| Ubicación | Rol |
|-----------|-----|
| `pyteg/client/tasks/protocols.py` | `GameWindowProtocol`: API mínima que consumen las tareas del cliente (`IClientTask.run`). Sub-objetos pesados (scene, chat, transmisor, etc.) se declaran como `Any` en el protocolo para evitar imports circulares; `Gui` conserva los tipos reales. |
| `pyteg/gui/managers/protocols.py` | `MainWindowProtocol`: extiende `GameWindowProtocol` con la superficie adicional usada por los gestores (`managers/`) y el panel de unidades (widgets internos, tema, filas de unidades, referencias cruzadas entre managers). |

Las tareas del cliente no deben importar widgets concretos salvo factories ya expuestas en `Gui`; los managers reciben `MainWindowProtocol` y, donde Qt exige `QWidget` como padre (diálogos), se usa `cast(QWidget, …)` en el punto de llamada.

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

## Flujo de mensajes
1) Cliente realiza acción (UI) → `pyteg/client/conexion/transmisor/` envía mensaje al servidor.
2) `pyteg/server/app.py` enruta → `ServerTask` correspondiente valida precondiciones.
3) Si es válido, aplica cambios en `pyteg/server/juego/game.py` / `pyteg/server/juego/mapa.py`.
4) El servidor emite mensajes de resultado/estado a clientes mediante `pyteg/server/conexion/transmisor.py` y `broadcaster.py`.
5) `pyteg/client/tasks/` procesa y actualiza GUI mediante la API pública de `Gui` (sin importar widgets directamente).

### Diagrama de flujo
Para una vista visual del intercambio de mensajes, ver el diagrama de secuencia en:
- `docs/diagrams/message_flow.md`

## Mensajería clave
- MsgChat (tipos: normal, error, system). Los errores de validación se publican en chat con formato y color.
- MsgPais: actualiza ocupación de un país; `userid` es **int** (o `null` si no hay dueño).
- MsgResultadoBatalla: dados, pérdidas y conquista; incluye `atacante_id`/`defensor_id` (**int**) además de nombres para UI/chat.
- MsgVictoria: `ganador_id` (**int**) y `ganador_nombre` (texto).
- MsgResultadoMisil: `jugador_id` (**int**) y `jugador` (nombre opcional para UI/chat).
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
