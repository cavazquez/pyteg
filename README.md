![example workflow](https://github.com/cavazquez/pyteg/actions/workflows/ruff.yml/badge.svg)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
# pyteg
Project about implementation game-board Teg.

## Correr los test y el linter
### Levantar el entorno con Docker
`./ejecutar_docker.sh`

### Correr el linter y los test 
`./run_test.sh`

### Correr solo el linter
`ruff --format=github --target-version=py311 .`

### Correr solo los test con coverage
`coverage run --branch -m unittest`

### Correr black
`./reformater.sh`

### Mostrar que cambios haria black
`black -t py311 --diff --check .`
