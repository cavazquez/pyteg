class TarjetaDePais:
    def __init__(self, pais, simbolo):
        self._pais = pais
        self._simbolo = simbolo
        self._usado = False
        self._jugador = None

    def dame_pais(self):
        return self._pais

    def dame_simbolo(self):
        return self._simbolo

    def fue_usada(self):
        return self._usado

    def jugador(self):
        return self._jugador

    def asignar(self, jugador):
        self._jugador = jugador
        self._usado = True

    def asignada(self):
        return self._jugador is not None

    def se_puede_asignar(self):
        return (self._jugador is None) and (self._usado is False)

    def desasignar(self):
        self._jugador = None

    def desusar(self):
        self._usado = False

    def __str__(self):
        return (
            f"pais: {self._pais}\n simbolo: {self._simbolo}\n"
            f"usado: {self._usado}\n jugador: {self._jugador}"
        )
