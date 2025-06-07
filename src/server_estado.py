class Estado:
    def __init__(self):
        self._estado_actual = "Inicial"

    def esperar_jugadores(self):
        self._estado_actual = "EsperarJugadores"

    def empezar_partida(self):
        self._estado_actual = "JUGANDO"

    def estado_actual(self):
        return self._estado_actual
