# CHANGELOG – Pyteg

Todas las fechas en formato YYYY-MM-DD.

## [Unreleased]

### Changed
- **Logging del servidor**: reemplazo de `print` por el sistema `pyteg.logger`; flags CLI `--quiet`, `--log-level` y `-v` para controlar la salida en consola (tráfico de red y batallas en DEBUG).
- **Logging del cliente y temporizador**: flags CLI equivalentes en el cliente; `TurnoTimer` usa logger (WARNING en fallos de envío, INFO al agotar el turno). Lógica compartida en `pyteg/log_cli.py`.
- **Logging en runtime restante**: `VictoryChecker` registra victorias en INFO; `SoundManager` avisa WAV faltantes en WARNING.
- **i18n en flujos de batalla**: cadenas de ataque, dados y turno en diálogos, managers y tareas del cliente; traducciones en `locales/en`.
- **Modularización de `main_window.py`**: delegaciones públicas en `MainWindowDelegatesMixin`; `show_battle_result_dialog` y `refresh_open_tarjetas_dialogs` movidos a managers.

### Added
- **Tests de `VictoryChecker` y `TurnoTimer`**: cobertura de victoria por países/objetivos y del temporizador de turno.
- **Tests de integración de gameplay**: turno y tiempo restante tras el inicio de partida.

### Security
- **Dependabot GHSA-537c-gmf6-5ccf**: actualización de `cryptography` transitiva (cadena dev `hatch` → `keyring` → `secretstorage`) a `>= 48.0.1`; restricción en `pyproject.toml` para evitar regresiones en el lockfile.

## [0.0.7] - 2026-06-17

### Changed
- **Identidad canónica del jugador = `userid` (int)** (ADR-012): en dominio servidor (mapa, turnos, mazo, cartas, validadores, combate, objetivos) y en mensajes JSON que transportan identidad; `username` queda solo para UI y chat. **Rompe compatibilidad de protocolo** entre versiones mezcladas de cliente/servidor.
- **Tipado por capas (Protocols y TypedDict)**:
  - Dominio: protocolo `IJugador`; `Mazo` / `TarjetaDePais` / `CardManager` comparan y asignan por `userid`.
  - Mensajes: `TypedDict` en payloads frecuentes (`BattleResultPayload`, `MissileResultPayload`, turno, lista de jugadores, configuración de partida) y en `data` de tareas servidor/cliente.
  - Servidor: `IClientProtocol` y `ServerLikeProtocol` ampliados; tareas y `Game` usan interfaces en lugar de `client: Any`.
  - GUI: `GameWindowProtocol`, `MainWindowProtocol` y `LobbyWindowProtocol` con tipos concretos (Qt, managers, `Client`); mixins y tareas sin `main_window: Any`.
  - Tests: `FakePlayer` conforme estructuralmente a `IClientProtocol`; `Game` acepta `Sequence[IClientProtocol]`; menos `cast` en `test_game`.
- **Refactor de módulos monolíticos en paquetes por dominio** (ADR-010): `pyteg/protocols/`, `pyteg/exceptions/`, `pyteg/logger/` con reexport en `__init__.py`; sin shims de compatibilidad.
- **Protocolos para tipar `Gui` desde tareas y managers** (ADR-011): eliminación de `hasattr` defensivos donde el contrato es estable; smoke test `test_gui_protocol_compat.py`.
- **Paquete Python renombrado de `src` a `pyteg`**: imports `from pyteg.…`, entry points y builds Nuitka apuntan al directorio `pyteg/`; actualizar scripts locales que ejecuten `python src/...` a `python pyteg/...`.

### Fixed
- **Servidor: ruido «Mensaje no JSON recibido»**: el transporte parte buffers con `\0`; se ignoran fragmentos vacíos tras `split("\0")` antes de `json.loads` (cada mensaje bien formado dejaba un `""` al final).
- **GUI: `RuntimeWarning` al cablear idioma** en `VentanaConectar` al conectar señales de i18n.
- **Corrección de carga de recursos en binarios**: Solucionado problema donde los binarios compilados con Nuitka no podían cargar iconos y otros recursos
  - Implementada función `get_resource_path()` en `pyteg/utils.py` que maneja rutas de recursos tanto en desarrollo como en binarios empaquetados
  - Actualizada carga de iconos en toolbar, imágenes de países, imágenes de tarjetas y archivos TOML
  - Servidor ahora incluye directorio `themes` en el build para acceder a archivos de configuración
  - Los binarios ahora funcionan correctamente sin errores de `ImagenNoEncontradaError`

### Added
- **Efectos de sonido WAV (CC0)**: assets en `sounds/` (Juhani Junkala / OpenGameArt); ver `sounds/README.md`.
- **Nuevos módulos de tipos**: `pyteg/protocols/jugador.py`, `pyteg/server/msg/types.py`, `pyteg/server/tasks/types.py`, `pyteg/client/tasks/types.py`.
- **Documentación ADR**: ADR-010 (splits protocols/exceptions/logger), ADR-011 (protocolos GUI), ADR-012 (`userid` canónico) en `docs/DECISIONS.md`.
- **Sistema de versionado consistente**: Los binarios ahora incluyen la versión en el nombre del archivo y la muestran al ejecutarse
  - Nuevo módulo `pyteg/version.py` para gestión centralizada de versiones
  - Consistencia entre `pyproject.toml` y tags de Git
  - Binarios nombrados con formato `pyteg-{server|client}-{version}` (ej: `pyteg-server-0.0.7`)
  - Archivos comprimidos incluyen versión: `pyteg-{version}-{platform}-{arch}` (ej: `pyteg-0.0.7-linux-x86_64.tar.gz`)
- **Sistema automatizado de releases multiplataforma**:
  - Nuevo workflow de GitHub Actions (`build-release.yml`) que construye binarios para múltiples plataformas
  - Se activa automáticamente al pushear tags que comiencen con `v` (ej: `v1.0.0`)
  - Soporta 4 plataformas: Linux x86_64, Windows x86_64, macOS x86_64, macOS ARM64
  - Construye binarios standalone usando Nuitka para servidor y cliente
  - Incluye todos los assets necesarios (themes, locales) en los binarios del cliente
  - Ejecuta tests en cada plataforma antes de construir
  - Crea borrador de release privado con binarios adjuntos y descripción detallada (requiere publicación manual)
  - Genera archivos comprimidos apropiados para cada plataforma (.tar.gz para Unix, .zip para Windows)
  - Documentación actualizada en README con instrucciones para crear releases
- **Sistema de objetivos secretos**: Implementación completa del sistema de objetivos secretos del TEG clásico
  - Archivo de configuración `themes/classic/objetivos_secretos.toml` con objetivos tradicionales
  - Opción configurable para activar/desactivar objetivos secretos al crear partida
  - Asignación aleatoria de objetivos secretos a jugadores al iniciar la partida
  - Visualización del objetivo secreto en la ventana de tarjetas del jugador
  - Verificación automática de condiciones de victoria por objetivo secreto
  - Soporte para tres tipos de objetivos: conquistar países, destruir jugador, conquistar continentes
  - Tests unitarios para el sistema de objetivos secretos
- **Separación de adyacencias en archivo independiente**:
  - Creado archivo `themes/classic/adyacencias.toml` con todas las adyacencias del mapa clásico
  - Removida sección `[Adyacencias]` de `paises.toml` para mejor organización modular
  - Actualizado `TomlReader` para cargar adyacencias desde archivo separado con compatibilidad hacia atrás
  - Mejorada separación de responsabilidades: geografía vs. conectividad del mapa
  - Todos los tests (137) pasan correctamente tras la refactorización
- **Separación de configuración de cartas y países**:
  - Creado archivo `themes/classic/cartas.toml` separado para configuración de cartas del juego
  - Removida sección `[Cartas]` de `paises.toml` para mejor separación de responsabilidades
  - Actualizado `TomlReader` para cargar ambos archivos con compatibilidad hacia atrás
  - Mejorada organización modular: países/continentes vs. mecánicas de juego
  - Todos los tests (137) pasan correctamente tras la refactorización
- **Sistema de efectos visuales inmersivos para batallas**:
  - Comportamiento diferenciado según rol del jugador:
    - **Atacante**: Ve animación completa de dados y diálogo de resultado
    - **Espectadores**: Ven efectos visuales (titilación de países + pérdidas flotantes)
  - Efectos visuales implementados:
    - Titilación roja/naranja en países origen y destino durante la batalla (2.5 segundos)
    - Animación de pérdidas flotantes en rojo con desvanecimiento y movimiento hacia arriba
    - Mensajes informativos en barra de estado con colores diferenciados
  - Reutilización del mensaje `MsgResultadoBatalla` existente sin cambios en el protocolo
  - Detección automática del rol del jugador comparando con el atacante
  - Integración completa con sistema de animación de dados existente
  - Manejo robusto de errores con excepciones específicas
- **Refactorización modular completa de la GUI**:
  - Arquitectura modular para mejorar mantenibilidad, legibilidad y escalabilidad
  - Reducción del 65% en líneas de código del archivo principal (de ~1039 a 366 líneas)
  - Separación en 6 gestores especializados con responsabilidades específicas:
    - `LayoutManager` (313 líneas): Estructura visual, widgets base, layout de ventana
    - `ThemeManager` (115 líneas): Gestión de temas claro/oscuro, estilos CSS
    - `PlayersManager` (92 líneas): Lista de jugadores, widgets de jugador, indicadores de color
    - `StatusManager` (125 líneas): Barra de estado, información de jugador actual, mensajes
    - `UnitsManager` (111 líneas): Panel de unidades disponibles, efectos visuales
    - `GameActionsManager` (79 líneas): Acciones del juego (atacar, finalizar turno)
  - Ventana principal (`gui.py`) enfocada en coordinación de gestores y eventos de Qt
  - Mantenimiento de toda la funcionalidad original con 121 tests pasando
  - Documentación actualizada en README.md y ARCHITECTURE.md
- **Sistema de internacionalización (i18n) completo**:
  - Soporte para múltiples idiomas usando gettext de Python
  - Idiomas disponibles: español (por defecto) e inglés
  - Detección automática del idioma del sistema al iniciar
  - Selector de idioma integrado en la barra de estado de la GUI
  - Módulo `i18n.py` para gestión centralizada de traducciones
  - Archivos de traducción `.po` para español e inglés en `locales/`
  - Script de gestión `scripts/manage_translations.py` para extraer, compilar y validar traducciones
  - Widget `LanguageSelector` para cambio dinámico de idioma
  - Refactorización de GUI con funciones `_()` para traducción
  - Documentación completa en README.md sobre uso del sistema i18n
- **Sistema completo de condición de victoria configurable**: 
  - Objetivo por defecto: 30 países (`DEFAULT_VICTORY_COUNTRIES` en `pyteg/config.py`, configurable al crear partida)
  - Configuración del objetivo de países al crear la partida (similar a duración de turno)
  - Verificación automática al final de cada ronda
  - Mensaje de victoria (MsgVictoria) con diálogo informativo y notificación en chat
  - Nueva ventana de configuración en el cliente mostrando duración de turno y objetivo de países
  - Botón "Configuración" en la toolbar para acceder a la información de la partida
- Documentación centralizada: ARCHITECTURE.md, DECISIONS.md (ADR), CONTRIBUTING.md, CHANGELOG.md.
- README.md actualizado con enlaces a documentación y comandos canon.
 - Diagrama de flujo de mensajes en `docs/diagrams/message_flow.md` y referencia en `docs/ARCHITECTURE.md`.
 - Logging: política de retención configurable por variables de entorno (tamaño por archivo, cantidad de backups, tamaño total de carpeta, días de retención y cantidad de logs de cliente). Rotación con `RotatingFileHandler` ahora configurable. Ver `docs/CONTRIBUTING.md`.

## 2025-08-07
- Sistema de mensajes de error en chat (tipos: normal, error, system). Ref: 2e82a38.
- Resultado de batalla difundido a clientes (MsgResultadoBatalla). Ref: e1d1709.
- Validación para impedir agregar unidades fuera de turno. Ref: 947060a.
- Envío de unidades disponibles al inicio de turno y tras agregar unidades.
- Toolbar: botones Atacar/Mover según selección y conexión; Finalizar Turno siempre habilitado.
- AttackDialog: tamaño aumentado a 400x280 para mejor UX. Ref: edfc535.
- run_tests.sh: agregado mypy con foco en aridad de llamadas.
