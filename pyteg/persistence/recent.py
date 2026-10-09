"""Índice de archivos recientes separado de los guardados de partida."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

_MAX_RECENT = 12
_MAX_INDEX_BYTES = 64 * 1024


class RecentGames:
    """Recuerda rutas; descubre también los autoguardados locales y LAN."""

    def __init__(self, directory: Path) -> None:
        """Usa la misma ubicación de datos que los autoguardados."""
        self.directory = directory
        self.path = directory.parent / "recent.json"

    def _read(self) -> list[str]:
        try:
            with self.path.open("rb") as stream:
                raw = stream.read(_MAX_INDEX_BYTES + 1)
            if len(raw) > _MAX_INDEX_BYTES:
                return []
            data = json.loads(raw)
            return (
                [item for item in data if isinstance(item, str)][:_MAX_RECENT]
                if isinstance(data, list)
                else []
            )
        except OSError, ValueError:
            return []

    def remember(self, path: str | Path) -> None:
        """Actualiza el índice atómicamente después de abrir o guardar."""
        resolved = str(Path(path).resolve())
        paths = [resolved, *(item for item in self._read() if item != resolved)][
            :_MAX_RECENT
        ]
        self.path.parent.mkdir(parents=True, exist_ok=True)
        descriptor, temporary = tempfile.mkstemp(
            prefix=".recent-", dir=self.path.parent
        )
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
                json.dump(paths, stream, ensure_ascii=False)
                stream.flush()
                os.fsync(stream.fileno())
            Path(temporary).replace(self.path)
        finally:
            Path(temporary).unlink(missing_ok=True)

    def paths(self) -> list[Path]:
        """Ordena los archivos existentes por su última modificación.

        Returns:
            Hasta doce rutas únicas, incluidos autoguardados recuperables.

        """
        paths = {Path(item) for item in self._read()} | set(
            self.directory.glob("*.pyteg")
        )
        existing = []
        seen: set[Path] = set()
        for path in paths:
            try:
                resolved = path.resolve()
                if resolved not in seen and resolved.is_file():
                    existing.append((resolved.stat().st_mtime, resolved))
                    seen.add(resolved)
            except OSError:
                continue
        return [
            path
            for _time, path in sorted(
                existing, key=lambda item: (-item[0], str(item[1]))
            )[:_MAX_RECENT]
        ]
