"""Módulo para el temporizador de turnos del juego."""

from __future__ import annotations

import threading
import time
from typing import Any, Protocol

from pyteg.config import DEFAULT_TURN_SECONDS
from pyteg.logger import get_logger

LOGGER = get_logger(__name__)


class TurnTimerProtocol(Protocol):
    """Puerto mínimo que necesita el coordinador para gestionar un timer."""

    def start(self) -> None:
        """Inicia el temporizador real o ejecuta un no-op seguro."""
        ...

    def detener(self) -> None:
        """Solicita detener el temporizador."""
        ...

    def join(self, timeout: float | None = None) -> None:
        """Espera el cierre del temporizador si tiene hilo."""
        ...

    def is_alive(self) -> bool:
        """Indica si existe un hilo de temporizador activo."""
        ...


class NullTurnTimer:
    """Objeto nulo para el estado anterior al inicio de una partida.

    No hereda de ``threading.Thread`` y por lo tanto no crea hilos ni puede
    encolar vencimientos. Su API coincide con la que usa el coordinador para
    que detener una partida, volver al lobby o iniciar una revancha sea
    idempotente.
    """

    def __init__(self) -> None:
        """Crea un temporizador inerte."""
        self._detenido = True

    def start(self) -> None:
        """No inicia ningún hilo."""

    def detener(self) -> None:
        """Mantiene el temporizador detenido y no hace trabajo adicional."""
        self._detenido = True

    def join(self, timeout: float | None = None) -> None:
        """No espera porque este objeto nunca tiene un hilo."""
        del timeout

    def is_alive(self) -> bool:
        """Siempre retorna ``False`` porque no existe un hilo asociado.

        Returns:
            Siempre ``False``.

        """
        return False


class TurnoTimer(threading.Thread):
    """Hilo que controla el temporizador de turnos.

    Cada jugador dispone de ``segundos_por_turno`` segundos. Cada segundo se
    envía un mensaje a *todos* los clientes con el tiempo restante para el
    jugador cuyo turno está activo. Cuando el tiempo llega a cero, encola un
    vencimiento asociado a la generación del turno; el ejecutor del servidor
    decide si aún corresponde aplicarlo.
    """

    def __init__(
        self, server: Any, segundos_por_turno: int = DEFAULT_TURN_SECONDS
    ) -> None:
        """Inicializa el temporizador de turnos.

        Args:
            server: Instancia del servidor.
            segundos_por_turno: Duración de cada turno en segundos (por defecto 20).

        """
        super().__init__(daemon=True)
        self._server: Any = server
        self._segundos_por_turno = segundos_por_turno
        self._stop_event = threading.Event()

    # ---------------------------------------------------------------------
    # API pública
    # ---------------------------------------------------------------------
    def detener(self) -> None:
        """Detiene el hilo de forma segura."""
        self._stop_event.set()

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------
    def _broadcast_tiempo(self, userid_turno: int, tiempo_restante: int) -> None:
        """Envía el mensaje de tiempo restante a todos los clientes."""
        for cliente in self._server.dame_clientes():
            try:
                cliente.transmisor.enviar_tiempo(userid_turno, tiempo_restante)
            except (ConnectionError, OSError, AttributeError) as exc:
                # No queremos que un fallo en un cliente interrumpa el temporizador
                LOGGER.warning(
                    "Error enviando tiempo a cliente %s: %s",
                    cliente.userid(),
                    exc,
                )

    # ------------------------------------------------------------------
    # Thread run
    # ------------------------------------------------------------------
    def run(self) -> None:
        """Ejecuta el hilo del temporizador de turnos."""
        while not self._stop_event.is_set():
            snapshot = self._server.turno_snapshot()
            if snapshot is None:
                time.sleep(0.1)
                continue

            userid_turno, generation = snapshot

            # Cuenta regresiva
            for remaining in range(self._segundos_por_turno, 0, -1):
                if self._stop_event.is_set():
                    return

                if self._server.turno_snapshot() != snapshot:
                    break

                # Enviar tiempo restante
                self._broadcast_tiempo(userid_turno, remaining)

                # Esperar un segundo
                time.sleep(1)

                # Si cambió la generación, el timer pertenece a un turno viejo.
                if self._server.turno_snapshot() != snapshot:
                    break
            else:
                if (
                    not self._stop_event.is_set()
                    and self._server.turno_snapshot() == snapshot
                ):
                    LOGGER.info("Tiempo agotado para jugador %s", userid_turno)
                    self._server.encolar_vencimiento_turno(generation)

            # Pequeño respiro antes de continuar (evita bucle tight)
            time.sleep(0.1)
