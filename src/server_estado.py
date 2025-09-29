class Estado:
    """Maneja los estados del servidor de juego."""

    # Constantes de estado
    INICIAL = "Inicial"
    ESPERAR_JUGADORES = "EsperarJugadores"
    JUGANDO = "JUGANDO"
    FINALIZADO = "Finalizado"

    def __init__(self):
        self._estado_actual = self.INICIAL

    def esperar_jugadores(self):
        """Cambia el estado a esperar jugadores."""
        if self._estado_actual == self.INICIAL:
            self._estado_actual = self.ESPERAR_JUGADORES
            return True
        return False

    def empezar_partida(self):
        """Cambia el estado a jugando."""
        if self._estado_actual == self.ESPERAR_JUGADORES:
            self._estado_actual = self.JUGANDO
            return True
        return False

    def finalizar_partida(self):
        """Cambia el estado a finalizado."""
        if self._estado_actual == self.JUGANDO:
            self._estado_actual = self.FINALIZADO
            return True
        return False

    def estado_actual(self):
        """Obtiene el estado actual."""
        return self._estado_actual

    def es_inicial(self):
        """Verifica si el estado es inicial."""
        return self._estado_actual == self.INICIAL

    def es_esperando_jugadores(self):
        """Verifica si el estado es esperar jugadores."""
        return self._estado_actual == self.ESPERAR_JUGADORES

    def es_jugando(self):
        """Verifica si el estado es jugando."""
        return self._estado_actual == self.JUGANDO

    def es_finalizado(self):
        """Verifica si el estado es finalizado."""
        return self._estado_actual == self.FINALIZADO

    @classmethod
    def get_acciones_validas(cls):
        """
        Obtiene el mapeo centralizado de acciones válidas para cada estado.

        Returns:
            Dict con las acciones válidas para cada estado
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

    def puede_ejecutar_accion(self, accion):
        """Verifica si una acción puede ejecutarse en el estado actual.

        Args:
            accion: Nombre de la acción a validar

        Returns:
            bool: True si la acción puede ejecutarse, False en caso contrario
        """
        acciones_validas = self.get_acciones_validas()
        estados_permitidos = acciones_validas.get(accion, [])
        return self._estado_actual in estados_permitidos
