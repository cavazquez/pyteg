"""Protocolos (interfaces) para mejorar type safety.

Este paquete define protocolos que especifican las interfaces necesarias
para diferentes componentes del sistema, permitiendo reemplazar `Any`
con tipos específicos y mejorar la seguridad de tipos.

Organización por dominio:
- `client`: borde entre el cliente conectado y el objeto servidor en
  tareas del servidor (`IClientProtocol`).
- `server`: API que el servidor expone a sus tareas (`ServerLikeProtocol`).
- `game`: reglas del juego, turnos, batalla, tarjetas (`IGameProtocol`).
- `mapa`: unidades, ocupación, misiles, distancias (`IMapProtocol`).

Estabilidad:
Los protocolos son contratos de tipado para el código del monorepo; no
constituyen una API pública versionada como librería externa. Los cambios
deben ir acompañados de actualizaciones en las implementaciones concretas
bajo `pyteg`.
"""

from __future__ import annotations

from pyteg.protocols.client import IClientProtocol
from pyteg.protocols.game import IGameProtocol
from pyteg.protocols.mapa import IMapProtocol
from pyteg.protocols.server import ServerLikeProtocol

__all__ = [
    "IClientProtocol",
    "IGameProtocol",
    "IMapProtocol",
    "ServerLikeProtocol",
]
