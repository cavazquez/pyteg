class Batalla:
    @staticmethod
    def ataquen(atacante, defensor, dados_atacante, dados_defensor):
        """
        Realiza el ataque entre el atacante y el defensor comparando los dados.

        :param atacante: Nombre del atacante
        :param defensor: Nombre del defensor
        :param dados_atacante: Lista de valores de los dados del atacante
        :param dados_defensor: Lista de valores de los dados del defensor
        :return: Diccionario con los resultados del ataque
        """
        res = {"atacante": atacante, "defensor": defensor, "restar": []}

        # Asegurarse de que las listas de dados estén ordenadas de mayor a menor
        dados_atacante.sort(reverse=True)
        dados_defensor.sort(reverse=True)

        for combate in range(min(len(dados_atacante), len(dados_defensor))):
            if dados_defensor[combate] < dados_atacante[combate]:
                res["restar"].append(defensor)
            else:
                res["restar"].append(atacante)

        return res

    @staticmethod
    def calcular_cant_dados_atacante(cantidad):
        """
        Calcula la cantidad de dados que puede usar el atacante.

        :param cantidad: Cantidad de unidades del atacante
        :return: Cantidad de dados que puede usar el atacante
        """
        return min(cantidad - 1, 3)

    @staticmethod
    def calcular_cant_dados_defensor(cantidad):
        """
        Calcula la cantidad de dados que puede usar el defensor.

        :param cantidad: Cantidad de unidades del defensor
        :return: Cantidad de dados que puede usar el defensor
        """
        return min(cantidad, 3)
