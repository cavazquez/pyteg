"""Tests para TurnoTimer."""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

from pyteg.core.turnos.timer import TurnoTimer


class TestTurnoTimerBroadcast(unittest.TestCase):
    """Comprueba el envío de tiempo restante a clientes."""

    def test_broadcast_envia_tiempo_a_todos(self) -> None:
        """Cada cliente recibe userid del turno y segundos restantes."""
        cliente_a = MagicMock()
        cliente_a.userid.return_value = 10
        cliente_b = MagicMock()
        cliente_b.userid.return_value = 20
        server = MagicMock()
        server.dame_clientes.return_value = [cliente_a, cliente_b]

        timer = TurnoTimer(server, segundos_por_turno=30)
        timer._broadcast_tiempo(1, 15)  # noqa: SLF001

        cliente_a.transmisor.enviar_tiempo.assert_called_once_with(1, 15)
        cliente_b.transmisor.enviar_tiempo.assert_called_once_with(1, 15)

    def test_broadcast_continua_si_un_cliente_falla(self) -> None:
        """Un error de socket no impide notificar al resto."""
        cliente_ok = MagicMock()
        cliente_ok.userid.return_value = 2
        cliente_fail = MagicMock()
        cliente_fail.userid.return_value = 3
        cliente_fail.transmisor.enviar_tiempo.side_effect = ConnectionError(
            "desconectado"
        )
        server = MagicMock()
        server.dame_clientes.return_value = [cliente_fail, cliente_ok]

        timer = TurnoTimer(server, segundos_por_turno=10)
        timer._broadcast_tiempo(5, 9)  # noqa: SLF001

        cliente_ok.transmisor.enviar_tiempo.assert_called_once_with(5, 9)


class TestTurnoTimerRun(unittest.TestCase):
    """Comprueba el bucle principal del temporizador."""

    _SLEEPS_BEFORE_EXPIRY_ENQUEUED = 3

    @patch("pyteg.core.turnos.timer.time.sleep")
    def test_sin_turno_publicado_no_encola_vencimiento(
        self, mock_sleep: MagicMock
    ) -> None:
        """Sin snapshot de turno el timer espera y no muta el juego."""
        server = MagicMock()
        server.turno_snapshot.return_value = None

        timer = TurnoTimer(server, segundos_por_turno=5)

        def detener_tras_espera(*_args: object) -> None:
            timer.detener()

        mock_sleep.side_effect = detener_tras_espera

        timer.run()

        server.encolar_vencimiento_turno.assert_not_called()

    @patch("pyteg.core.turnos.timer.time.sleep")
    def test_cambio_de_turno_durante_cuenta_regresiva(
        self, mock_sleep: MagicMock
    ) -> None:
        """Si cambia la generación, no se encola el vencimiento viejo."""
        server = MagicMock()
        server.dame_clientes.return_value = []
        server.turno_snapshot.side_effect = [(1, 4), (1, 4), (2, 5)]

        timer = TurnoTimer(server, segundos_por_turno=3)

        mock_sleep.side_effect = lambda *_args: timer.detener()

        timer.run()

        server.encolar_vencimiento_turno.assert_not_called()

    @patch("pyteg.core.turnos.timer.time.sleep")
    def test_tiempo_agotado_encola_vencimiento(self, mock_sleep: MagicMock) -> None:
        """Al completar la cuenta regresiva se encola el vencimiento vigente."""
        server = MagicMock()
        server.dame_clientes.return_value = []
        server.turno_snapshot.return_value = (7, 12)

        timer = TurnoTimer(server, segundos_por_turno=2)

        call_idx = 0

        def controlar_ejecucion(*_args: object) -> None:
            nonlocal call_idx
            call_idx += 1
            if call_idx >= self._SLEEPS_BEFORE_EXPIRY_ENQUEUED:
                timer.detener()

        mock_sleep.side_effect = controlar_ejecucion

        timer.run()

        server.encolar_vencimiento_turno.assert_called_once_with(12)

    def test_detener_marca_evento(self) -> None:
        """detener() activa el evento de parada del hilo."""
        timer = TurnoTimer(MagicMock(), segundos_por_turno=1)

        timer.detener()

        self.assertTrue(timer._stop_event.is_set())  # noqa: SLF001


if __name__ == "__main__":
    unittest.main()
