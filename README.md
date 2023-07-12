![example workflow](https://github.com/cavazquez/pyteg/actions/workflows/ruff.yml/badge.svg)
# pyteg
Project about implementation game-board Teg.

## Correr los test y el linter
### Levantar el entorno con Docker
./ejecutar_docker.sh

### Correr el linter y los test
Dentro de docker: ./run_test.sh


### Correr solo el linter
ruff --format=github --target-version=py311 .

### Correr solo los test con coverage
coverage run --branch -m unittest
