"""Canje y reclamo de tarjetas vía transmisor (padre de la ventana principal)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

from pyteg.gui.connection_utils import cliente_esta_conectado
from pyteg.logger import get_logger

if TYPE_CHECKING:
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
        if transmisor is None:
            _LOG.warning("No se puede acceder al transmisor (canje)")
            return

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
        if transmisor is None:
            _LOG.warning("No se puede acceder al transmisor (canje)")
            return

        try:
            transmisor.reclamar_tarjeta()
            transmisor.solicitar_tarjetas()
        except (AttributeError, RuntimeError) as e:
            _LOG.warning("Error al reclamar tarjeta: %s", e)

    def _get_transmisor(self: TarjetasExchangeHost) -> Any | None:
        """Obtiene el transmisor desde la ventana padre si existe.

        Returns:
            El objeto transmisor o ``None`` si no hay padre o no expone ``transmisor``.

        """
        parent = self.parent()
        if parent is None or not cliente_esta_conectado(
            cast("MainWindowProtocol", parent)
        ):
            return None
        return getattr(parent, "transmisor", None)
