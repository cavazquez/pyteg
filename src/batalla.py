class Batalla:
    @staticmethod
    def ataquen(mapa, atacante, defensor, dados_atacante, dados_defensor):
        res = []

        for combate in range(min(len(dados_atacante), len(dados_defensor))):
            if dados_defensor[combate] < dados_atacante[combate]:
                res.append(defensor)
            else:
                res.append(atacante)

        return res

    @staticmethod
    def calcular_cant_dados_atacante(cantidad):
        return min(cantidad - 1, 3)

    @staticmethod
    def calcular_cant_dados_defensor(cantidad):
        return min(cantidad, 3)


