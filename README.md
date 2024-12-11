![example workflow](https://github.com/cavazquez/pyteg/actions/workflows/ruff.yml/badge.svg)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

# pyteg
Project about implementation game-board Teg.

## Correr los test y el linter
### Levantar el entorno con Docker
`./ejecutar_docker.sh`

### Correr el linter y los test 
`./run_test.sh`

### Correr solo el linter
`ruff --output-format=github .`

### Correr solo los test con coverage
`coverage run --branch -m unittest`
### Mostrar el coverage
`coverage report -m`

