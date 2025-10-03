![example workflow](https://github.com/cavazquez/pyteg/actions/workflows/ruff-uv.yml/badge.svg)
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

# Pyteg

Implementación del juego Teg en Python

## ¿Qué es Teg?
T.E.G. es un juego de estrategia por turnos (similar a Risk) en el que
los jugadores conquistan países, atacan con dados y cumplen objetivos.
Este proyecto implementa una versión cliente-servidor con interfaz
gráfica en Python.

## Características clave
- Cliente gráfico con PySide6 y animación de dados en las batallas
- **Efectos visuales inmersivos**: Atacante ve animación completa, espectadores ven titilación de países y pérdidas flotantes
- **Sistema de sonidos**: Efectos de audio para batallas, movimientos, turnos y eventos del juego con controles de volumen
- Modo multijugador con servidor TCP y validación de estados
- Restricción de ataques en los dos primeros turnos
- Elección de cantidad de unidades para atacar (1 a 3)
- Validación de nombres de usuario duplicados (con desconexión)
- Estado del juego visible en la barra de estado (ronda, turno, color)
- Bloqueo de nuevas conexiones cuando la partida está en curso
- **Condición de victoria configurable**: Por defecto 50 países (configurable al crear partida)
- **Objetivos secretos**: Sistema opcional de objetivos secretos del TEG clásico
- **Ventana de configuración**: Muestra duración de turno, objetivo de países y objetivos secretos
- **Verificación automática de condición de victoria al final de cada ronda**
- **Soporte multiidioma (i18n)**: Español e inglés con selector en la interfaz
- 160+ tests automatizados y linting con Ruff

## Requisitos
- Python 3.11 o superior
- [UV](https://github.com/astral-sh/uv) para dependencias
- Docker (opcional)

## Instalación rápida
```bash
git clone https://github.com/cavazquez/pyteg.git
cd pyteg
uv sync
```

## Ejecutar (servidor y clientes)
- Con entry points instalados (recomendado):
  ```bash
  # Instala el paquete y scripts
  uv sync

  # Servidor
  uv run pyteg-server

  # Cliente
  uv run pyteg-client
  ```

- Terminal 1 (servidor):
```bash
uv run python src/server.py
```

- Terminal 2..8 (clientes):
```bash
uv run python src/run_client.py
```

Consejos:
- Primero inicia el servidor. Luego abre uno o más clientes.
- Si el juego ya está en curso, el servidor rechazará nuevas conexiones.

## Build de binarios (Hatch + Nuitka)
Requiere dependencias de desarrollo:
```bash
uv sync --group dev
```

Compilar binarios (modo onefile + standalone) para servidor y cliente:
```bash
uv run hatch build -t nuitka
```

Los ejecutables quedarán en `dist/`.

Build de wheel/sdist (empaquetado Python estándar):
```bash
uv run hatch build -t wheel -t sdist
```

## Estructura del proyecto
- `src/`: Código fuente principal
- `tests/`: Tests unitarios
- `themes/`: Temas visuales y mapas
  - `classic/`: Tema clásico con mapa mundial completo (50 países)
    - `paises.toml`: Configuración de países y continentes
    - `cartas.toml`: Configuración de cartas del juego
    - `*.png`: Archivos de imagen de países y cartas
  - `test/`: Tema de prueba con mapa reducido (6 países)
- `locales/`: Archivos de traducción (español/inglés)
- `docs/`: Documentación técnica
- `ejecutar_docker.sh`: entorno en Docker (opcional)

### Estructura de archivos de configuración

El juego utiliza archivos TOML para la configuración:

- `themes/classic/paises.toml`: Configuración de países, continentes y sus propiedades visuales
- `themes/classic/cartas.toml`: Configuración de cartas del juego (separado desde v1.x)
- `themes/classic/adyacencias.toml`: Configuración de adyacencias entre países (separado desde v1.x)
- `themes/classic/objetivos_secretos.toml`: Configuración de objetivos secretos del TEG clásico

### Arquitectura modular de la GUI
La interfaz gráfica ha sido refactorizada en módulos especializados para mejorar mantenibilidad:

- **`gui.py`** (366 líneas): Ventana principal y coordinación de gestores
- **`gui_layout_manager.py`**: Gestión de layout y estructura visual
- **`gui_theme_manager.py`**: Gestión de temas claro/oscuro
- **`gui_players_manager.py`**: Gestión de lista y widgets de jugadores
- **`gui_status_manager.py`**: Gestión de barra de estado y mensajes
- **`gui_units_manager.py`**: Gestión de unidades y efectos visuales
- **`gui_game_actions.py`**: Acciones del juego (atacar, finalizar turno)

Esta arquitectura modular reduce la complejidad del archivo principal en un 65% (de ~1039 a 366 líneas) mientras mantiene toda la funcionalidad intacta.

## Desarrollo
Formateo y estilo:
- Límite de línea: 88 caracteres (en todo el proyecto)
- Ruff para lint y formato

Comandos útiles:
```bash
# Lint
uvx ruff check .

# Formato (solo verifica)
uvx ruff format --check .

# Aplicar formato
uvx ruff format .

# Tests con coverage
uvx coverage run --branch -m unittest
uvx coverage report -m

# Todo en una pasada
./run_test.sh
```

## Logs y retención
Los logs se guardan en `logs/` con rotación automática y limpieza periódica. Puedes ajustar límites mediante variables de entorno (tamaño por archivo, cantidad de backups, tamaño total, días de retención y cantidad de logs de cliente). Consulta la sección correspondiente en `docs/CONTRIBUTING.md` para ver los nombres de variables y ejemplos.

## Docker (opcional)
Puedes levantar un entorno de desarrollo con:
```bash
./ejecutar_docker.sh
```

## Soporte multiidioma (i18n)

PyTeg incluye soporte completo para múltiples idiomas usando gettext:

### Idiomas soportados
- **Español** (es) - Idioma por defecto
- **English** (en) - Inglés

### Cambiar idioma
- El idioma se detecta automáticamente del sistema al iniciar
- Usa el selector de idioma en la barra de estado de la interfaz
- Los cambios se aplican inmediatamente

### Para desarrolladores
```bash
# Extraer strings para traducir
python3 scripts/manage_translations.py extract

# Compilar traducciones
python3 scripts/manage_translations.py compile

# Ejecutar todas las tareas de traducción
python3 scripts/manage_translations.py all
```

Para marcar texto como traducible en el código:
```python
from i18n import _

# Texto simple
label = QLabel(_("Texto a traducir"))

# Texto con formato
message = _("Jugador {} ganó").format(player_name)
```

## Documentación y diagramas
 - Documentación central:
   - Arquitectura: `docs/ARCHITECTURE.md`
   - Decisiones (ADR): `docs/DECISIONS.md`
   - Guía de contribución: `docs/CONTRIBUTING.md`
   - Cambios: `docs/CHANGELOG.md`
 - Protocolos y mensajes:
   - `docs/como_crear_mensaje_cliente_a_servidor.md`
   - `docs/como_crear_mensaje_servidor_a_cliente.md`
   - `docs/como_crear_mensaje_bidireccional.md`
 - Diagramas y notas en `docs/diagrams/`
 - El código incluye docstrings y type hints en módulos clave

## Releases y Binarios

### Descargar binarios compilados
Los binarios compilados para múltiples plataformas están disponibles en la [página de releases](https://github.com/cavazquez/pyteg/releases):

- **Linux x86_64**: `pyteg-linux-x86_64.tar.gz`
- **Windows x86_64**: `pyteg-windows-x86_64.zip`  
- **macOS x86_64**: `pyteg-macos-x86_64.tar.gz`
- **macOS ARM64**: `pyteg-macos-arm64.tar.gz`

Los binarios son standalone (no requieren Python instalado) e incluyen todos los assets necesarios.

### Crear un nuevo release
Para crear un nuevo release con binarios compilados:

1. **Actualizar la versión** en `pyproject.toml`:
   ```toml
   [project]
   version = "1.0.0"  # Nueva versión
   ```

2. **Actualizar el CHANGELOG** en `docs/CHANGELOG.md` con los cambios de la nueva versión.

3. **Crear y pushear el tag**:
   ```bash
   git add pyproject.toml docs/CHANGELOG.md
   git commit -m "Bump version to 1.0.0"
   git tag v1.0.0
   git push origin main
   git push origin v1.0.0
   ```

4. **GitHub Actions automáticamente**:
   - Construirá binarios para todas las plataformas
   - Ejecutará los tests en cada plataforma
   - Creará un **borrador de release privado** con los binarios adjuntos
   - Generará archivos comprimidos para cada plataforma

5. **Publicar el release manualmente**:
   - Ve a la [página de releases](https://github.com/cavazquez/pyteg/releases) en GitHub
   - Encontrarás un borrador con todos los binarios adjuntos
   - Revisa los binarios y la descripción del release
   - Haz clic en **"Publish release"** para hacerlo público

El workflow se ejecuta solo cuando se pushea un tag que comience con `v` (ej: `v1.0.0`, `v2.1.3`).

## Contribuir
¡Contribuciones son bienvenidas! Por favor, crea un issue o pull request para sugerir mejoras o reportar problemas.
