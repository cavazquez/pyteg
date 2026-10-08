#!/usr/bin/env bash
set -euo pipefail

# Las pruebas de PySide6 también deben poder ejecutarse sin un escritorio gráfico.
# Se puede sobrescribir desde el entorno si se necesita otro backend Qt.
export QT_QPA_PLATFORM="${QT_QPA_PLATFORM:-offscreen}"

section() {
  printf '\n==> %s\n\n' "$1"
}

section "uv sync (dev)"
uv sync --group dev

section "gettext: compilar .po → .mo (locales/)"
# Regenerar los .mo mantiene los catálogos binarios sincronizados con los .po.
uv run python scripts/manage_translations.py compile

section "Ruff format (auto-fix)"
uv run ruff format .

section "Ruff check (auto-fix)"
uv run ruff check --fix --unsafe-fixes .

section "Ruff check"
uv run ruff check .

section "Mypy"
uv run mypy

section "Coverage run"
uv run python -m coverage run --branch -m unittest discover

section "Coverage summary"
uv run coverage report
