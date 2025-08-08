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
- Modo multijugador con servidor TCP y validación de estados
- Restricción de ataques en los dos primeros turnos
- Elección de cantidad de unidades para atacar (1 a 3)
- Validación de nombres de usuario duplicados (con desconexión)
- Estado del juego visible en la barra de estado (ronda, turno, color)
- Bloqueo de nuevas conexiones cuando la partida está en curso
- 120+ tests automatizados y linting con Ruff

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
- `src/`: código fuente
  - `server.py`: servidor y loop principal
  - `server_game.py`: lógica del juego y batallas
  - `server_mapa.py`: estado del mapa y países
  - `server_tasks.py`: acciones validadas del servidor
  - `client_connection.py`: conexión del cliente
  - `client_tasks.py`: tareas que procesan mensajes
  - `gui.py` y `gui_*`: interfaz gráfica y diálogos
  - `run_client.py`: punto de entrada del cliente
- `tests/`: suite de tests
- `run_test.sh`: pruebas y linting de una pasada
- `ejecutar_docker.sh`: entorno en Docker (opcional)

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

## Contribuir
¡Contribuciones son bienvenidas! Por favor, crea un issue o pull request para sugerir mejoras o reportar problemas.
