"""Canje y reclamo de tarjetas vía transmisor (padre de la ventana principal)."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from pyteg.client.conexion.transmisor import ClientNullTransmisor
from pyteg.logger import get_logger

if TYPE_CHECKING:
    from pyteg.client.conexion.transmisor.protocol import IClientTransmisor
    from pyteg.gui.managers.protocols import MainWindowProtocol

    from .protocols import TarjetasExchangeHost

_LOG = get_logger("gui.tarjetas_dialog")


class TarjetasExchangeMixin:
    """Acciones de red que delegan en `parent().transmisor`."""

    def realizar_canje(self: TarjetasExchangeHost) -> None:
        """Realiza el canje de las tarjetas seleccionadas."""
        if not self._puede_realizar_canje():
            return

        cantidad_seleccionadas = len(self.tarjetas_seleccionadas)

        tarjetas_info = [
            {"pais": tarjeta.pais, "simbolo": tarjeta.simbolo, "index": tarjeta.index}
            for tarjeta in self.tarjetas_seleccionadas
        ]

        transmisor = self._get_transmisor()
        try:
            if cantidad_seleccionadas == 1:
                tarjeta = self.tarjetas_seleccionadas[0]
                transmisor.canje_especial(tarjeta.pais)
            else:
                transmisor.canjear_tarjetas(tarjetas_info)

            self.deseleccionar_todas()
        except (AttributeError, RuntimeError) as e:
            _LOG.warning("Error al realizar canje: %s", e)

    def reclamar_tarjeta(self: TarjetasExchangeHost) -> None:
        """Reclama una tarjeta del servidor."""
        transmisor = self._get_transmisor()
        try:
            transmisor.reclamar_tarjeta()
            transmisor.solicitar_tarjetas()
        except (AttributeError, RuntimeError) as e:
            _LOG.warning("Error al reclamar tarjeta: %s", e)

    def _get_transmisor(self: TarjetasExchangeHost) -> IClientTransmisor:
        """Obtiene el transmisor desde la ventana padre o el objeto nulo.

        Returns:
            Un transmisor real o el Null Object si el diálogo no tiene host.

        """
        parent = self.parent()
        if parent is None:
            return ClientNullTransmisor()
        try:
            return cast("MainWindowProtocol", parent).transmisor
        except AttributeError:
            return ClientNullTransmisor()
