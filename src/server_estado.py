"""Estados posibles del servidor de juego."""

from __future__ import annotations


class Estado:
    """Maneja los estados del servidor de juego."""

    # Constantes de estado
    INICIAL = "Inicial"
    ESPERAR_JUGADORES = "EsperarJugadores"
    JUGANDO = "JUGANDO"
    FINALIZADO = "Finalizado"

    def __init__(self) -> None:
        """Inicializa el estado del servidor en INICIAL."""
        self._estado_actual = self.INICIAL

    def esperar_jugadores(self) -> bool:
        """Cambiar el estado a "esperar jugadores".

        Returns:
            True si el cambio fue exitoso, False en caso contrario.

        """
        if self._estado_actual == self.INICIAL:
            self._estado_actual = self.ESPERAR_JUGADORES
            return True
        return False

    def empezar_partida(self) -> bool:
        """Cambiar el estado a "jugando".

        Returns:
            True si el cambio fue exitoso, False en caso contrario.

        """
        if self._estado_actual == self.ESPERAR_JUGADORES:
            self._estado_actual = self.JUGANDO
            return True
        return False

    def finalizar_partida(self) -> bool:
        """Cambiar el estado a "finalizado".

        Returns:
            True si el cambio fue exitoso, False en caso contrario.

        """
        if self._estado_actual == self.JUGANDO:
            self._estado_actual = self.FINALIZADO
            return True
        return False

    def estado_actual(self) -> str:
        """Obtener el estado actual.

        Returns:
            Estado actual del servidor.

        """
        return self._estado_actual

    def es_inicial(self) -> bool:
        """Verifica si el estado actual es INICIAL.

        Returns:
            True si el estado es INICIAL, False en caso contrario.

        """
        return self._estado_actual == self.INICIAL

    def es_esperando_jugadores(self) -> bool:
        """Verifica si el estado actual es ESPERAR_JUGADORES.

        Returns:
            True si el estado es ESPERAR_JUGADORES, False en caso contrario.

        """
        return self._estado_actual == self.ESPERAR_JUGADORES

    def es_jugando(self) -> bool:
        """Verifica si el estado actual es JUGANDO.

        Returns:
            True si el estado es JUGANDO, False en caso contrario.

        """
        return self._estado_actual == self.JUGANDO

    def es_finalizado(self) -> bool:
        """Verifica si el estado actual es FINALIZADO.

        Returns:
            True si el estado es FINALIZADO, False en caso contrario.

        """
        return self._estado_actual == self.FINALIZADO

    @classmethod
    def get_acciones_validas(cls) -> dict[str, list[str]]:
        """Obtener el mapeo centralizado de acciones válidas para cada estado.

        Returns:
            Diccionario con las acciones válidas para cada estado.

        """
        return {
            "empezar": [cls.INICIAL],
            "empezar_partida": [cls.ESPERAR_JUGADORES],
            "seleccionar_color": [cls.INICIAL, cls.ESPERAR_JUGADORES],
            "set_username": [cls.INICIAL, cls.ESPERAR_JUGADORES],
            "chat": [cls.INICIAL, cls.ESPERAR_JUGADORES, cls.JUGANDO],
            "agregar_unidad": [cls.JUGANDO],
            "mover_unidad": [cls.JUGANDO],
            "atacar": [cls.JUGANDO],
            "finalizar_turno": [cls.JUGANDO],
            "solicitar_tarjetas": [cls.JUGANDO],
            "reclamar_tarjeta": [cls.JUGANDO],
            "canje_especial": [cls.JUGANDO],
            "canjear_misil": [cls.JUGANDO],
            "lanzar_misil": [cls.JUGANDO],
        }

    def puede_ejecutar_accion(self, accion: str) -> bool:
        """Verifica si una acción puede ejecutarse en el estado actual.

        Returns:
            True si la acción puede ejecutarse, False en caso contrario.

        """
        acciones_validas = self.get_acciones_validas()
        estados_permitidos = acciones_validas.get(accion, [])
        return self._estado_actual in estados_permitidos
