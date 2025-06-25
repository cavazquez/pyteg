import threading
import time


class TurnoTimer(threading.Thread):
    """Hilo que controla el temporizador de turnos.

    Cada jugador dispone de ``segundos_por_turno`` segundos.  Cada segundo se
    envía un mensaje a *todos* los clientes con el tiempo restante para el
    jugador cuyo turno está activo.  Cuando el tiempo llega a cero, se avanza
    al siguiente turno mediante ``server.game.finalizar_turno()``.
    """

    def __init__(self, server, segundos_por_turno: int = 120):
        super().__init__(daemon=True)
        self._server = server
        self._segundos_por_turno = segundos_por_turno
        self._stop_event = threading.Event()

    # ---------------------------------------------------------------------
    # API pública
    # ---------------------------------------------------------------------
    def detener(self):
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
            except Exception as exc:
                # No queremos que un fallo en un cliente interrumpa el temporizador
                print(
                    "[TurnoTimer] Error enviando tiempo a cliente "
                    f"{cliente.userid()}: {exc}"
                )

    # ------------------------------------------------------------------
    # Thread run
    # ------------------------------------------------------------------
    def run(self):
        while not self._stop_event.is_set():
            # Esperar a que exista una partida iniciada
            if not self._server.game or not self._server.game.empezo():
                time.sleep(1)
                continue

            turno_actual = self._server.game.turno_actual()
            try:
                jugador = turno_actual.jugador_actual()
            except AttributeError:
                # Turno no implementa jugador_actual
                time.sleep(1)
                continue

            userid_turno = jugador.userid()

            # Cuenta regresiva
            for remaining in range(self._segundos_por_turno, 0, -1):
                if self._stop_event.is_set():
                    return

                # Enviar tiempo restante
                self._broadcast_tiempo(userid_turno, remaining)

                # Esperar un segundo
                time.sleep(1)

                # Si terminaron prematuramente el turno, salir del countdown
                nuevo_turno = self._server.game.turno_actual()
                if nuevo_turno is not turno_actual:
                    break
            else:
                # El contador llegó a 0 -> finalizar turno automáticamente
                try:
                    self._server.game.finalizar_turno()
                except Exception as exc:
                    print(
                        f"[TurnoTimer] Error al finalizar turno automáticamente: {exc}"
                    )

            # Pequeño respiro antes de continuar (evita bucle tight)
            time.sleep(0.1)
