![example workflow](https://github.com/cavazquez/pyteg/actions/workflows/ruff-uv.yml/badge.svg)
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

# pyteg
Project about implementation game-board Teg.

## Configuración
`uv sync`

## Correr los test y el linter
### Levantar el entorno con Docker
`./ejecutar_docker.sh`

### Correr el linter y los test 
`./run_test.sh`

### Correr solo el linter
`uvx ruff --output-format=github .`

### Correr solo el formater
`uvx ruff format --check .`

### Correr solo los test con coverage
`uvx coverage run --branch -m unittest`
### Mostrar el coverage
`uvx coverage report -m`

