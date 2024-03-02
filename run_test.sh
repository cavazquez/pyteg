ruff check .
coverage run --branch -m unittest
black --check .
