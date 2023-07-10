ruff --format=github --target-version=py311 .
coverage run -m unittest
coverage report
