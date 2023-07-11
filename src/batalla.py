from src.dados import Dados


class Batalla:
    @staticmethod
    def ataquen(mapa, atacante, defensor):
        cant_atacantes = mapa.cantidad_unidades(atacante)
        cant_defensores = mapa.cantidad_unidades(defensor)

        cant_dados_atacantes = Batalla.calcular_cant_dados_atacante(cant_atacantes)
        cant_dados_defensores = Batalla.calcular_cant_dados_defensor(cant_defensores)

        dados_atacantes = Dados.tirar_dados_ordenados(cant_dados_atacantes)
        dados_defensores = Dados.tirar_dados_ordenados(cant_dados_defensores)

        for combate in range(min(len(dados_atacantes), len(dados_defensores))):
            if dados_defensores[combate] < dados_atacantes[combate]:
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
