class Calculos:
    @staticmethod
    def calcular_unidades_generales(mapa, jugador):
        return max(mapa.cantidad_de_paises_del_jugador(jugador) // 2, 3)

    @staticmethod
    def calcular_unidades_europa(mapa, jugador):
        if mapa.tiene_toda_europa(jugador):
            return 5
        return 0

    @staticmethod
    def calcular_unidades_asia(mapa, jugador):
        if mapa.tiene_toda_asia(jugador):
            return 7
        return 0

    @staticmethod
    def calcular_unidades_africa(mapa, jugador):
        if mapa.tiene_toda_africa(jugador):
            return 3
        return 0

    @staticmethod
    def calcular_unidades_oceania(mapa, jugador):
        if mapa.tiene_toda_oceania(jugador):
            return 2
        return 0

    @staticmethod
    def calcular_unidades_america_del_sur(mapa, jugador):
        if mapa.tiene_toda_america_del_sur(jugador):
            return 3
        return 0

    @staticmethod
    def calcular_unidades_america_del_norte(mapa, jugador):
        if mapa.tiene_toda_america_del_norte(jugador):
            return 5
        return 0
