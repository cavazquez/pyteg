"""Formato JSON versionado y escritura atómica de archivos de juego."""

from __future__ import annotations

import hashlib
import json
import os
import sys
import tempfile
import uuid
from copy import deepcopy
from pathlib import Path
from typing import Any, Protocol

ARCHIVE_VERSION = 1
MAX_ARCHIVE_BYTES = 16 * 1024 * 1024
_KINDS = frozenset({"game", "turn", "replay"})
_MAX_DEPTH = 64


def canonical_bytes(data: object) -> bytes:
    """Devuelve JSON estable para integridad y referencias entre turnos.

    Returns:
        JSON UTF-8 ordenado, sin valores flotantes no finitos.

    """
    return json.dumps(
        data, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")


def digest(data: object) -> str:
    """Calcula la identidad de un estado portable.

    Returns:
        SHA-256 del JSON canónico.

    """
    return hashlib.sha256(canonical_bytes(data)).hexdigest()


def make_archive(kind: str, payload: dict[str, Any]) -> dict[str, Any]:
    """Crea un archivo que detecta modificaciones y errores de copia.

    Returns:
        Documento independiente del sistema operativo.

    Raises:
        ValueError: Si el tipo de archivo no está soportado.

    """
    if kind not in _KINDS:
        msg = "Tipo de archivo de partida desconocido"
        raise ValueError(msg)
    body = {
        "format": "pyteg",
        "version": ARCHIVE_VERSION,
        "kind": kind,
        "payload": deepcopy(payload),
    }
    return {**body, "sha256": digest(body)}


def validate_archive(data: object, *, kind: str | None = None) -> dict[str, Any]:
    """Comprueba formato, profundidad e integridad antes de abrir el archivo.

    Returns:
        Documento validado y separado del objeto original.

    Raises:
        ValueError: Si está incompleto, alterado o usa una versión incompatible.

    """
    if not isinstance(data, dict):
        msg = "Archivo de Pyteg incompatible o incompleto"
        raise ValueError(msg)  # noqa: TRY004 -- archivo inválido.
    checks = (
        set(data) == {"format", "version", "kind", "payload", "sha256"},
        data.get("format") == "pyteg",
        type(data.get("version")) is int and data.get("version") == ARCHIVE_VERSION,
        data.get("kind") in _KINDS,
        isinstance(data.get("payload"), dict),
        kind is None or data.get("kind") == kind,
    )
    if not all(checks):
        msg = "Archivo de Pyteg incompatible o incompleto"
        raise ValueError(msg)
    pending = [(data, 0)]
    while pending:
        value, depth = pending.pop()
        if depth > _MAX_DEPTH:
            msg = "El archivo tiene demasiados niveles"
            raise ValueError(msg)
        if isinstance(value, dict):
            pending.extend((item, depth + 1) for item in value.values())
        elif isinstance(value, list):
            pending.extend((item, depth + 1) for item in value)
    body = {key: value for key, value in data.items() if key != "sha256"}
    if data["sha256"] != digest(body):
        msg = "El archivo está dañado o fue modificado"
        raise ValueError(msg)
    return deepcopy(data)


def read_archive(path: str | Path, *, kind: str | None = None) -> dict[str, Any]:
    """Abre un documento con un límite de tamaño antes de decodificar JSON.

    Returns:
        Archivo completo validado.

    Raises:
        ValueError: Si el archivo es demasiado grande o no es válido.

    """
    with Path(path).open("rb") as stream:
        raw = stream.read(MAX_ARCHIVE_BYTES + 1)
    if len(raw) > MAX_ARCHIVE_BYTES:
        msg = "El archivo supera el tamaño permitido"
        raise ValueError(msg)
    try:
        data = json.loads(raw)
        return validate_archive(data, kind=kind)
    except (UnicodeError, json.JSONDecodeError, RecursionError, TypeError) as error:
        msg = "El archivo no contiene una partida válida"
        raise ValueError(msg) from error


def write_archive(path: str | Path, archive: dict[str, Any]) -> None:
    """Reemplaza el archivo sólo después de escribir y sincronizar su contenido.

    Raises:
        ValueError: Si el documento no es válido o es demasiado grande.

    """
    data = canonical_bytes(validate_archive(archive))
    if len(data) > MAX_ARCHIVE_BYTES:
        msg = "El archivo supera el tamaño permitido"
        raise ValueError(msg)
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(
        prefix=f".{target.name}.", dir=target.parent
    )
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        Path(temporary).replace(target)
        if sys.platform != "win32":
            directory = os.open(target.parent, os.O_RDONLY | os.O_DIRECTORY)
            try:
                os.fsync(directory)
            finally:
                os.close(directory)
    finally:
        Path(temporary).unlink(missing_ok=True)


class ArchiveRepository(Protocol):
    """Estrategia de conservación de la última copia confirmada."""

    def save(self, archive: dict[str, Any]) -> None:
        """Conserva un documento completo."""
        ...

    def load(self) -> dict[str, Any] | None:
        """Obtiene la última copia, si existe."""
        ...

    def bind_session(self, session_id: str, user_id: int) -> bool:
        """Selecciona la ubicación de una identidad; indica si cambió."""
        ...

    def start_room(self) -> None:
        """Prepara otra ubicación sin reemplazar guardados de partidas previas."""
        ...


class MemoryRepository:
    """Repositorio para motores sin almacenamiento persistente."""

    def __init__(self) -> None:
        """Inicializa un repositorio vacío."""
        self._archive: dict[str, Any] | None = None

    def save(self, archive: dict[str, Any]) -> None:
        """Conserva una copia independiente del documento."""
        self._archive = validate_archive(archive)

    def load(self) -> dict[str, Any] | None:
        """Devuelve la copia conservada.

        Returns:
            Archivo completo o None.

        """
        return deepcopy(self._archive)

    def bind_session(self, _session_id: str, _user_id: int) -> bool:
        """La estrategia en memoria no cambia de ubicación.

        Returns:
            False: ya conserva sus promesas en esta instancia.

        """
        return False

    def start_room(self) -> None:
        """Descarta el documento de la sala anterior."""
        self._archive = None


class FileRepository:
    """Repositorio durable con el mismo contrato que el repositorio en memoria."""

    def __init__(self, path: str | Path, *, session_scoped: bool = False) -> None:
        """Conserva la ubicación del autoguardado."""
        self.path = Path(path)
        self.session_scoped = session_scoped

    def bind_session(self, session_id: str, user_id: int) -> bool:
        """Reutiliza el autoguardado de la misma identidad después de reiniciar.

        Returns:
            True si ahora se puede cargar su guardado y sus votos previos.

        """
        if not self.session_scoped:
            return False
        path = self.path.parent / f"{digest(session_id)[:24]}-jugador-{user_id}.pyteg"
        changed = self.path != path
        self.path = path
        return changed

    def start_room(self) -> None:
        """Conserva el archivo anterior al preparar un autoguardado de otra sala."""
        if self.session_scoped:
            self.path = self.path.parent / f"{uuid.uuid4().hex}.pyteg"

    def save(self, archive: dict[str, Any]) -> None:
        """Escribe una copia completa sin truncar la anterior."""
        write_archive(self.path, archive)

    def load(self) -> dict[str, Any] | None:
        """Lee la última copia de esta ubicación.

        Returns:
            Archivo completo o None si nunca se guardó.

        """
        return read_archive(self.path) if self.path.exists() else None
