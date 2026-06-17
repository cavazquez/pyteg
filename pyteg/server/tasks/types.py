"""TypedDict para los `data` de entrada de las tareas del servidor.

Cada tarea recibe un `data` con forma `{"mensaje": <accion>, ...}`. Estos
`TypedDict` (con `total=False` salvo `mensaje`) describen la forma
esperada para que mypy detecte campos mal escritos o no soportados.

El tipo `BaseTaskData` solo exige `mensaje`; cada tarea define su propio
subtipo con campos adicionales opcionales.
"""

from __future__ import annotations

from typing import TypedDict


class BaseTaskData(TypedDict):
    """Forma mínima del `data` de toda tarea: incluye el campo `mensaje`."""

    mensaje: str


class _OptEmpezar(TypedDict, total=False):
    """Campos opcionales de configuración inicial de la partida."""

    segundos: int | str | None
    paises_para_victoria: int | str | None
    objetivos_secretos: bool
    misiles_habilitados: bool


class EmpezarTaskData(BaseTaskData, _OptEmpezar):
    """`data` de la tarea `empezar`."""


class _OptAtacar(TypedDict, total=False):
    """Campos opcionales del ataque."""

    origen: str | None
    destino: str | None
    cantidad_unidades: int | None


class AtacarTaskData(BaseTaskData, _OptAtacar):
    """`data` de la tarea `atacar`."""


class _OptAgregarUnidad(TypedDict, total=False):
    """Campos opcionales de agregar unidad."""

    pais: str | None
    tipo_unidad: str | None
    cantidad: int


class AgregarUnidadTaskData(BaseTaskData, _OptAgregarUnidad):
    """`data` de la tarea `agregar_unidad`."""


class _OptMoverUnidad(TypedDict, total=False):
    """Campos opcionales de mover unidad."""

    origen: str | None
    destino: str | None
    cantidad: int


class MoverUnidadTaskData(BaseTaskData, _OptMoverUnidad):
    """`data` de la tarea `mover_unidad`."""


class _OptLanzarMisil(TypedDict, total=False):
    """Campos opcionales de lanzar misil."""

    pais_origen: str | None
    pais_destino: str | None


class LanzarMisilTaskData(BaseTaskData, _OptLanzarMisil):
    """`data` de la tarea `lanzar_misil`."""


class _OptCanjeEspecial(TypedDict, total=False):
    """Campos opcionales de canje especial."""

    pais: str | None


class CanjeEspecialTaskData(BaseTaskData, _OptCanjeEspecial):
    """`data` de la tarea `canje_especial`."""


class _OptCanjearMisil(TypedDict, total=False):
    """Campos opcionales de canjear misil."""

    pais: str | None


class CanjearMisilTaskData(BaseTaskData, _OptCanjearMisil):
    """`data` de la tarea `canjear_misil`."""


class _TarjetaCanjePayload(TypedDict, total=False):
    """Elemento de la lista de tarjetas enviada por el cliente."""

    pais: str
    simbolo: str
    index: int


class _OptCanjearTarjetas(TypedDict, total=False):
    """Campos opcionales de canje de tres tarjetas."""

    tarjetas: list[_TarjetaCanjePayload]


class CanjearTarjetasTaskData(BaseTaskData, _OptCanjearTarjetas):
    """`data` de la tarea `canjear_tarjetas`."""


class _OptSetUsername(TypedDict, total=False):
    """Campos opcionales de set_username."""

    username: str | None


class SetUsernameTaskData(BaseTaskData, _OptSetUsername):
    """`data` de la tarea `set_username`."""


class _OptSeleccionarColor(TypedDict, total=False):
    """Campos opcionales de seleccionar_color."""

    color: str | None


class SeleccionarColorTaskData(BaseTaskData, _OptSeleccionarColor):
    """`data` de la tarea `seleccionar_color`."""


class _OptChat(TypedDict, total=False):
    """Campos opcionales del chat."""

    msg: str | None


class ChatTaskData(BaseTaskData, _OptChat):
    """`data` de la tarea `chat`."""
