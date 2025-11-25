"""Módulo para el temporizador de turnos del juego."""

from __future__ import annotations

import threading
import time
from typing import Any


class TurnoTimer(threading.Thread):
    """Hilo que controla el temporizador de turnos.

    Cada jugador dispone de ``segundos_por_turno`` segundos.  Cada segundo se
    envía un mensaje a *todos* los clientes con el tiempo restante para el
    jugador cuyo turno está activo.  Cuando el tiempo llega a cero, se avanza
    al siguiente turno mediante ``server.game.finalizar_turno()``.
    """

    def __init__(self, server: Any, segundos_por_turno: int = 120) -> None:
        """Inicializa el temporizador de turnos.

        Args:
            server: Instancia del servidor.
            segundos_por_turno: Duración de cada turno en segundos (por defecto 120).

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
                print(
                    "[TurnoTimer] Error enviando tiempo a cliente "
                    f"{cliente.userid()}: {exc}"
                )

    # ------------------------------------------------------------------
    # Thread run
    # ------------------------------------------------------------------
    def run(self) -> None:
        """Ejecuta el hilo del temporizador de turnos."""
        while not self._stop_event.is_set():
            # Esperar a que exista una partida iniciada
            if not self._server.game or not self._server.game.empezo():
                time.sleep(1)
                continue

            turno_actual = self._server.game.turno_actual()
            jugador = turno_actual.jugador_actual()
            userid_turno = jugador.userid()

            # Cuenta regresiva
            for remaining in range(self._segundos_por_turno, 0, -1):
                if self._stop_event.is_set():
                    return

                # Enviar tiempo restante
                self._broadcast_tiempo(userid_turno, remaining)

                # Esperar un segundo
                time.sleep(1)

                # Si el jugador actual cambió,
                # notificar a los clientes y salir del bucle interno
                if turno_actual != self._server.game.turno_actual():
                    self._server.enviar_turno_actual()
                    break
            else:
                # Si el tiempo se agotó, pasar al siguiente turno
                if remaining <= 0:
                    msg = f"[TurnoTimer] Tiempo agotado para el turno {turno_actual}"
                    print(msg)
                    self._server.game.finalizar_turno()
                    # Enviar el nuevo número de turno a los clientes
                    self._server.enviar_turno_actual()
                else:
                    # El contador llegó a 0 -> finalizar turno automáticamente
                    self._server.game.finalizar_turno()
                    # Enviar el nuevo número de turno a los clientes
                    self._server.enviar_turno_actual()

            # Pequeño respiro antes de continuar (evita bucle tight)
            time.sleep(0.1)
