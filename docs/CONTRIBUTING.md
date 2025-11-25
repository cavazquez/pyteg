# Contribuir a Pyteg

¡Gracias por tu interés en contribuir! Este documento resume cómo configurar el entorno, el estilo de código y el flujo de trabajo recomendado.

## Requisitos
- Python 3.11+
- [UV](https://github.com/astral-sh/uv)

## Configuración
```bash
uv sync
```

## Comandos canon
```bash
# Lint
uvx ruff check .

# Formato (verificar)
uvx ruff format --check .

# Formato (aplicar)
uvx ruff format .

# Tests + coverage
uvx coverage run --branch -m unittest
uvx coverage report -m

# mypy (foco en aridad de llamadas)
uvx mypy --ignore-missing-imports --explicit-package-bases --no-error-summary \
  --disable-error-code=import --disable-error-code=attr-defined \
  --disable-error-code=assignment --disable-error-code=return-value \
  --disable-error-code=operator --disable-error-code=index \
  --disable-error-code=misc --disable-error-code=type-arg \
  --disable-error-code=union-attr --disable-error-code=override \
  --disable-error-code=var-annotated --disable-error-code=valid-type \
  --disable-error-code=name-defined --disable-error-code=has-type \
  --disable-error-code=abstract --disable-error-code=no-untyped-def \
  --disable-error-code=no-untyped-call src/

# Todo en una pasada
./run_tests.sh
```

## Política de retención de logs
Los logs se escriben en `logs/` con rotación automática y limpieza periódica. Puedes ajustar los límites vía variables de entorno:

- `PYTEG_LOG_MAX_BYTES` (por archivo, defecto: `10485760` = 10 MB)
- `PYTEG_LOG_BACKUP_COUNT` (backups por archivo, defecto: `5`)
- `PYTEG_LOG_MAX_TOTAL_MB` (tamaño total de la carpeta `logs/`, defecto: `200` MB)
- `PYTEG_LOG_MAX_DAYS` (días máximos de retención, defecto: `14`)
- `PYTEG_LOG_MAX_CLIENT_FILES` (máximo de archivos `client_*.log`, defecto: `20`)

Ejemplo de ejecución con límites personalizados:
```bash
PYTEG_LOG_MAX_BYTES=5242880 \
PYTEG_LOG_BACKUP_COUNT=3 \
PYTEG_LOG_MAX_TOTAL_MB=100 \
PYTEG_LOG_MAX_DAYS=7 \
PYTEG_LOG_MAX_CLIENT_FILES=10 \
uv run pyteg-server
```

## Arquitectura modular de la GUI

La interfaz gráfica sigue una arquitectura modular con gestores especializados:

### Estructura de archivos GUI
- **`gui.py`**: Ventana principal y coordinación de gestores
- **`gui_layout_manager.py`**: Gestión de layout y estructura visual
- **`gui_theme_manager.py`**: Gestión de temas y estilos
- **`gui_players_manager.py`**: Gestión de jugadores y widgets
- **`gui_status_manager.py`**: Gestión de barra de estado
- **`gui_units_manager.py`**: Gestión de unidades disponibles
- **`gui_game_actions.py`**: Acciones del juego (atacar, finalizar turno)

### Principios de diseño
- **Separación de responsabilidades**: Cada gestor tiene una función específica
- **Coordinación centralizada**: `gui.py` orquesta todos los gestores
- **Referencias compartidas**: Los gestores acceden al main window para UI y estado
- **Modularidad**: Nuevas funcionalidades se agregan en el gestor apropiado

### Guías para modificaciones GUI
1. **Nuevas funcionalidades**: Agregar al gestor apropiado o crear uno nuevo
2. **Cambios de layout**: Modificar `LayoutManager`
3. **Cambios de tema**: Modificar `ThemeManager`
4. **Nuevas acciones**: Agregar a `GameActionsManager`
5. **Cambios de estado**: Modificar `StatusManager`

Ver diagrama completo en `docs/diagrams/gui_modular_architecture.md`.

## Estilo y convenciones
- Límite de línea: 88 caracteres.
- Ruff como linter y formateador.
- Docstrings y type hints en módulos clave.
- Mantener `README.md` y `docs/` actualizados (arquitectura, decisiones, cambios).

## Flujo de trabajo
1. Crear rama desde `main`.
2. Hacer cambios con commits atómicos y mensajes claros.
3. Asegurarse de que `./run_tests.sh` pase localmente.
4. Abrir PR describiendo el cambio y motivación; enlazar issues cuando aplique.
5. Actualizar `docs/DECISIONS.md` si hay cambios arquitectónicos; `docs/CHANGELOG.md` si es un cambio visible para usuarios.

## Guía de protocolo
Para extender el protocolo o agregar mensajes:
- Ver `docs/como_crear_mensaje_cliente_a_servidor.md`.
- Ver `docs/como_crear_mensaje_servidor_a_cliente.md`.
- Ver `docs/como_crear_mensaje_bidireccional.md`.

## Contacto
Abrir un issue en GitHub para preguntas o discutir cambios.
