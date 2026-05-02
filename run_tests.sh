#!/usr/bin/env bash
set -euo pipefail

section() {
  printf '\n==> %s\n\n' "$1"
}

section "gettext: compilar .po → .mo (locales/)"
# Los .mo no se versionan (.gitignore); regenerarlos evita inglés roto tras git pull.
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
uv run python -m coverage run --branch -m unittest

section "Coverage summary"
uv run python - <<'PY'
import contextlib
import coverage
import io

cov = coverage.Coverage(data_file=".coverage")
cov.load()
with contextlib.redirect_stdout(io.StringIO()):
    total = cov.report(show_missing=False)
print(f"Total coverage: {total:.1f}%")
PY

