"""Transmisor nulo (no-op) para cuando no hay conexión activa."""

from __future__ import annotations

from typing import Any

from pyteg.client.conexion.transmisor.protocol import IClientTransmisor
from pyteg.logger import get_logger

_LOG = get_logger("client.transmisor")


class ClientNullTransmisor(IClientTransmisor):
    """Transmisor nulo que no envía mensajes (para cuando no hay conexión)."""

    def __init__(self) -> None:
        """Inicializa el transmisor nulo."""

    def enviar_chat(self, _: str) -> None:
        """Envía un mensaje de chat (no-op cuando no hay conexión).

        Args:
            _: Mensaje de chat (ignorado).

        """
        _LOG.debug("No estas conectado")

    def empezar(
        self,
        segundos: int | None = None,
        paises_para_victoria: int | None = None,
        *,
        objetivos_secretos: bool = False,
        misiles_habilitados: bool = False,
    ) -> None:
        """No-op para el transmisor nulo."""

    def seleccionar_color(self, _color: Any) -> None:
        """Selecciona un color (no-op cuando no hay conexión).

        Args:
            _color: Color a seleccionar (ignorado).

        """
        _LOG.debug("No estas conectado")

    def empezar_partida(self) -> None:
        """Inicia la partida (no-op cuando no hay conexión)."""
        _LOG.debug("No estas conectado")

    def set_username(self, _: str) -> None:
        """Establece el nombre de usuario (no-op cuando no hay conexión).

        Args:
            _: Nombre de usuario (ignorado).

        """
        _LOG.debug("No estas conectado")

    def agregar_unidad(self, _pais: str, _tipo_unidad: str, _cantidad: int = 1) -> None:
        """Agrega una unidad (no-op cuando no hay conexión).

        Args:
            _pais: País donde agregar (ignorado).
            _tipo_unidad: Tipo de unidad (ignorado).
            _cantidad: Cantidad de unidades (ignorado).

        """
        _LOG.debug("No estas conectado")

    def mover_unidad(self, _origen: str, _destino: str, _cantidad: int = 1) -> None:
        """Mueve unidades (no-op cuando no hay conexión).

        Args:
            _origen: País de origen (ignorado).
            _destino: País de destino (ignorado).
            _cantidad: Cantidad de unidades (ignorado).

        """
        _LOG.debug("No puedes mover unidades. No estas conectado.")

    def atacar(self, _: str, __: str, cantidad_unidades: int | None = None) -> None:  # noqa: ARG002
        """Ataca (no-op cuando no hay conexión).

        Args:
            _: País de origen (ignorado).
            __: País de destino (ignorado).
            cantidad_unidades: Cantidad de unidades (ignorado).

        """
        _LOG.debug("No puedes atacar. No estas conectado.")

    def actualizar_lista_jugadores(self, _: list[dict[str, Any]]) -> None:
        """Actualiza la lista de jugadores (no-op cuando no hay conexión).

        Args:
            _: Lista de jugadores (ignorado).

        """

    def finalizar_turno(self) -> None:
        """Finaliza el turno (no-op cuando no hay conexión)."""
        _LOG.debug("No puedes finalizar el turno. No estás conectado.")

    def solicitar_tarjetas(self) -> None:
        """Solicita tarjetas (no-op cuando no hay conexión)."""
        _LOG.debug("No puedes ver tarjetas. No estás conectado.")

    def reclamar_tarjeta(self) -> None:
        """Reclama una tarjeta (no-op cuando no hay conexión)."""
        _LOG.debug("No puedes reclamar tarjetas. No estás conectado.")

    def canje_especial(self, pais: str) -> None:
        """Realiza un canje especial cuando no está conectado."""
        _ = pais
        _LOG.debug("No puedes realizar canje especial. No estás conectado.")

    def canjear_misil(self, pais: str) -> None:
        """Canjea un misil cuando no está conectado."""
        _ = pais
        _LOG.debug("No puedes canjear misiles. No estás conectado.")

    def lanzar_misil(self, pais_origen: str, pais_destino: str) -> None:
        """Lanza un misil cuando no está conectado."""
        _, _ = pais_origen, pais_destino
        _LOG.debug("No puedes lanzar misiles. No estás conectado.")
