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

# Mypy (estricto; configuración en pyproject.toml → pyteg/, tests/, scripts/)
uv run mypy

# Todo en una pasada (incluye auto-fix de Ruff)
./run_tests.sh
```

## Pre-commit (opcional)

En la raíz del repo hay [`.pre-commit-config.yaml`](../.pre-commit-config.yaml) con **Ruff** (misma versión mayor que en `pyproject.toml` / el hook `v0.14.10`). **Mypy** sigue siendo obligatorio vía CI y `./run_tests.sh`, no se ejecuta en cada commit para no alentar el flujo local.

```bash
pip install pre-commit   # o: uv tool install pre-commit
pre-commit install
```

Tras eso, Ruff corre en `git commit`. Quien no use pre-commit no está obligado; la fuente de verdad sigue siendo el workflow de GitHub Actions y los comandos anteriores.

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

### Estructura de archivos GUI (paquete `pyteg/gui/`)
- **`pyteg/gui/main_window.py`**: Ventana principal (`Gui`) y coordinación de gestores
- **`pyteg/gui/managers/layout.py`**: Layout y estructura visual
- **`pyteg/gui/managers/theme.py`**: Temas y estilos
- **`pyteg/gui/managers/players.py`**: Jugadores y widgets
- **`pyteg/gui/managers/status.py`**: Barra de estado
- **`pyteg/gui/managers/units.py`**: Unidades disponibles
- **`pyteg/gui/managers/game_actions.py`**: Acciones del juego (atacar, finalizar turno)

### Principios de diseño
- **Separación de responsabilidades**: Cada gestor tiene una función específica
- **Coordinación centralizada**: `Gui` en `main_window.py` orquesta los gestores
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
