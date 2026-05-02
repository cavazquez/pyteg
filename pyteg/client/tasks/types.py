"""TypedDict para los `data` de tareas del cliente.

Estos `TypedDict` son simétricos con los del servidor (ver
`pyteg/server/msg/types.py` y `pyteg/server/tasks/types.py`). Modelan los
payloads JSON que llegan desde el servidor y permiten a mypy validar el
acceso a campos en cada `IClientTask`.

Todos los campos son opcionales (`total=False`) excepto `mensaje`, ya que
los `IClientTask` toleran ausencia de campos vía `dict.get(..., default)`.
"""

from __future__ import annotations

from typing import TypedDict


class BaseClientTaskData(TypedDict):
    """Forma mínima del `data` de toda tarea cliente: incluye `mensaje`."""

    mensaje: str


class _OptResultadoBatalla(TypedDict, total=False):
    """Campos opcionales del payload de batalla recibido por el cliente."""

    origen: str | None
    destino: str | None
    atacante_id: int | None
    defensor_id: int | None
    atacante: str | None
    defensor: str | None
    dados_atacante: list[int]
    dados_defensor: list[int]
    resultado: dict[str, list[str]]
    conquistado: bool


class ResultadoBatallaTaskData(BaseClientTaskData, _OptResultadoBatalla):
    """`data` de `ClientTaskResultadoBatalla`."""


class _OptResultadoMisil(TypedDict, total=False):
    """Campos opcionales del payload de resultado de misil."""

    jugador_id: int | None
    jugador: str | None
    pais_origen: str | None
    pais_destino: str | None
    distancia: int | None
    dano: int | None
    unidades_restantes: int | None


class ResultadoMisilTaskData(BaseClientTaskData, _OptResultadoMisil):
    """`data` de `ClientTaskResultadoMisil`."""


class _OptTurno(TypedDict, total=False):
    """Campos opcionales del payload de turno."""

    num_turno: int
    num_ronda: int
    jugador_actual_id: int | None
    jugador_actual_nombre: str | None
    jugador_actual_color: str | None


class TurnoTaskData(BaseClientTaskData, _OptTurno):
    """`data` de `ClientTaskTurno`."""


class JugadorListaItem(TypedDict, total=False):
    """Item recibido en la lista de `actualizar_lista_jugadores`."""

    userid: int
    color: dict[str, int]


class _OptListaJugadores(TypedDict, total=False):
    """Campos opcionales del payload de actualización de lista."""

    jugadores: list[JugadorListaItem]


class ActualizarListaJugadoresTaskData(BaseClientTaskData, _OptListaJugadores):
    """`data` de `ClientTaskActualizarListaJugadores`."""


class _OptAsignarPais(TypedDict, total=False):
    """Campos opcionales del payload de asignación inicial de país."""

    pais: str | None
    userid: int | None
    unidades: int


class AsignarPaisTaskData(BaseClientTaskData, _OptAsignarPais):
    """`data` de `ClientTaskAsignarPais`."""


class _OptConfiguracionPartida(TypedDict, total=False):
    """Campos opcionales del payload de configuración de partida."""

    segundos_por_turno: int
    paises_para_victoria: int
    objetivos_secretos: bool
    misiles_habilitados: bool


class ConfiguracionPartidaTaskData(BaseClientTaskData, _OptConfiguracionPartida):
    """`data` de `ClientTaskConfiguracionPartida`."""


class _OptVictoria(TypedDict, total=False):
    """Campos opcionales del payload de victoria."""

    ganador_id: int | None
    ganador_nombre: str | None


class VictoriaTaskData(BaseClientTaskData, _OptVictoria):
    """`data` de `ClientTaskVictoria`."""


class TarjetaItem(TypedDict, total=False):
    """Item de tarjeta enviado al cliente."""

    pais: str
    simbolo: str


class _OptTarjetasJugador(TypedDict, total=False):
    """Campos opcionales del payload de tarjetas del jugador."""

    tarjetas: list[TarjetaItem]


class TarjetasJugadorTaskData(BaseClientTaskData, _OptTarjetasJugador):
    """`data` de `ClientTaskTarjetasJugador`."""


class _OptMisilAgregado(TypedDict, total=False):
    """Campos opcionales del payload de misil agregado."""

    pais: str | None
    cantidad_misiles: int | None


class MisilAgregadoTaskData(BaseClientTaskData, _OptMisilAgregado):
    """`data` de `ClientTaskMisilAgregado`."""


class _OptUnidadesDisponibles(TypedDict, total=False):
    """Campos opcionales del payload de unidades disponibles."""

    unidades: dict[str, int]


class UnidadesDisponiblesTaskData(BaseClientTaskData, _OptUnidadesDisponibles):
    """`data` de `ClientTaskUnidadesDisponibles`."""


class _OptObjetivoSecreto(TypedDict, total=False):
    """Campos opcionales del payload de objetivo secreto."""

    objetivo_id: str
    descripcion: str


class ObjetivoSecretoTaskData(BaseClientTaskData, _OptObjetivoSecreto):
    """`data` de `ClientTaskObjetivoSecreto`."""


class _OptTiempo(TypedDict, total=False):
    """Campos opcionales del payload de tiempo."""

    tiempo: int


class TiempoTaskData(BaseClientTaskData, _OptTiempo):
    """`data` de `ClientTaskTiempo`."""


class _OptUserId(TypedDict, total=False):
    """Campos opcionales del payload de user_id."""

    user_id: int


class UserIdTaskData(BaseClientTaskData, _OptUserId):
    """`data` de `ClientTaskUserId`."""


class _OptUsername(TypedDict, total=False):
    """Campos opcionales del payload de username."""

    username: str | None
    user_id: int | None


class UsernameTaskData(BaseClientTaskData, _OptUsername):
    """`data` de `ClientTaskUsername`."""


class _OptChat(TypedDict, total=False):
    """Campos opcionales del payload de chat."""

    msg: str | None
    msg_type: str
    nombre: str | None


class ChatClientTaskData(BaseClientTaskData, _OptChat):
    """`data` de `ClientTaskChat`."""


class _OptError(TypedDict, total=False):
    """Campos opcionales del payload de error."""

    error_type: str | None
    message: str | None


class ErrorTaskData(BaseClientTaskData, _OptError):  # noqa: N818
    """`data` de `ClientTaskError`.

    Nombre por convención de la fase: `<accion>TaskData`.
    """


class _OptColorAsignado(TypedDict, total=False):
    """Campos opcionales del payload de color asignado."""

    id: int
    r: int
    g: int
    b: int


class ColorAsignadoTaskData(BaseClientTaskData, _OptColorAsignado):
    """`data` de `ClientTaskColorAsignado`."""


class _OptColor(TypedDict, total=False):
    """Campos opcionales del payload de color (un color disponible)."""

    r: int
    g: int
    b: int


class ColorTaskData(BaseClientTaskData, _OptColor):
    """`data` de `ClientTaskColor`."""


class _OptEstado(TypedDict, total=False):
    """Campos opcionales del payload de estado."""

    estado: str | None


class EstadoTaskData(BaseClientTaskData, _OptEstado):
    """`data` de `ClientTaskEstado`."""
