

class Batalla:
    @staticmethod
    def ataquen(mapa, atacante, defensor, dados_atacante, dados_defensor):
        cant_atacantes = mapa.cantidad_unidades(atacante)
        cant_defensores = mapa.cantidad_unidades(defensor)

        for combate in range(min(len(dados_atacante), len(dados_defensor))):
            if dados_defensor[combate] < dados_atacante[combate]:
                cant_defensores -= 1
            else:
                cant_atacantes -= 1

        mapa.set_unidades(atacante, max(1, cant_atacantes))
        mapa.set_unidades(defensor, max(0, cant_defensores))

    @staticmethod
    def calcular_cant_dados_atacante(cantidad):
        return min(cantidad-1, 3)


    @staticmethod
    def calcular_cant_dados_defensor(cantidad):
        return min(cantidad, 3)
