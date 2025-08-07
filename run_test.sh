uvx ruff check .
uvx mypy
uvx coverage run --branch -m unittest
uvx ruff format --check .
