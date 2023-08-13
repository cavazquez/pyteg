class Batalla:
    @staticmethod
    def ataquen(atacante, defensor, dados_atacante, dados_defensor):
        res = {"atacante": atacante, "defensor": defensor, "restar": []}

        for combate in range(min(len(dados_atacante), len(dados_defensor))):
            if dados_defensor[combate] < dados_atacante[combate]:
                res["restar"].append(defensor)
            else:
                res["restar"].append(atacante)

        return res

    @staticmethod
    def calcular_cant_dados_atacante(cantidad):
        return min(cantidad - 1, 3)

    @staticmethod
    def calcular_cant_dados_defensor(cantidad):
        return min(cantidad, 3)
