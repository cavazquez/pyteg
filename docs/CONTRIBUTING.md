# Contribuir a Pyteg

¡Gracias por tu interés en contribuir! Este documento resume cómo configurar el entorno, el estilo de código y el flujo de trabajo recomendado.

## Requisitos
- Python 3.11+
- [UV](https://github.com/astral-sh/uv)

## Configuración
```bash
# Solo dependencias de ejecución (cliente/servidor)
uv sync

# Incluye Ruff, mypy, coverage, etc. (recomendado para contribuir)
uv sync --group dev
```

## Comandos canon
Instala dependencias de desarrollo una vez: `uv sync --group dev`.

```bash
# Lint (misma versión que el lockfile)
uv run ruff check .

# Formato (verificar)
uv run ruff format --check .

# Formato (aplicar)
uv run ruff format .

# Tests + coverage
uv run coverage run --branch -m unittest discover
uv run coverage report -m

# Mypy (estricto; configuración en pyproject.toml → src/, tests/, scripts/)
uv run mypy

# Todo en una pasada (incluye auto-fix de Ruff)
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
