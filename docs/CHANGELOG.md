# CHANGELOG – Pyteg

Todas las fechas en formato YYYY-MM-DD.

## Unreleased
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
  - Condición de victoria cambiada a controlar 50 países (por defecto, configurable)
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
- run_test.sh: agregado mypy con foco en aridad de llamadas.
