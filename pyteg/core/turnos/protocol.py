"""Protocolo (interfaz) para los tipos de turno del juego.

Este módulo define el Protocol ``ITurno`` que unifica la interfaz de
``PrimerTurno``, ``SegundoTurno`` y ``SiguientesTurnos`` sin requerir herencia.
Al usar *structural subtyping* de Python, las tres clases satisfacen la
interfaz automáticamente si implementan los métodos requeridos.
"""

from __future__ import annotations

from typing import Protocol


class ITurno(Protocol):
    """Interfaz mínima compartida por todos los tipos de turno.

    Cualquier objeto que implemente estos métodos satisface el protocolo
    sin necesidad de heredar explícitamente de esta clase.
    """

    def jugador_actual(self) -> int:
        """Obtiene el userid (int) del jugador en turno.

        Returns:
            userid (int) del jugador actual.

        """
        ...

    def cant_unidades(self) -> int:
        """Obtiene las unidades generales disponibles del jugador.

        Returns:
            Cantidad de unidades generales disponibles.

        """
        ...

    def usar_unidad(self) -> None:
        """Consume una unidad general disponible."""
        ...

    def agregar_unidades_generales(self, num: int) -> None:
        """Agrega unidades generales al turno.

        Args:
            num: Cantidad de unidades a agregar.

        """
        ...

    def unidades_por_tipo(self) -> dict[str, int]:
        """Retorna todas las unidades disponibles clasificadas por tipo/continente.

        El dict siempre incluye la clave ``"infanteria"`` con las unidades
        generales. ``SiguientesTurnos`` agrega además claves de continente
        cuando su valor es > 0.

        Returns:
            Diccionario ``{tipo: cantidad}`` listo para enviar al cliente.
            Ejemplo: ``{"infanteria": 3, "Africa": 1, "Europa": 2}``.

        """
        ...
