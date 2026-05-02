"""Transmisor del cliente: protocolo, implementación nula y real.

Cada clase vive en su propio módulo; este paquete las reexporta para
preservar el contrato `from pyteg.client.conexion.transmisor import X`.
"""

from __future__ import annotations

from pyteg.client.conexion.transmisor.null import ClientNullTransmisor
from pyteg.client.conexion.transmisor.protocol import IClientTransmisor
from pyteg.client.conexion.transmisor.transmisor import ClientTransmisor

__all__ = ["ClientNullTransmisor", "ClientTransmisor", "IClientTransmisor"]
