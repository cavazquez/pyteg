pyright --pythonversion 3.11 . .
ruff --format=github --target-version=py311 .
coverage run --branch -m unittest
coverage report -m
black -t py311 --check .
