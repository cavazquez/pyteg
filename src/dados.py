from random import choices


class Dados:

    @staticmethod
    def tirar_dados(cant):
        return choices(range(1, 6), k=cant)

    @staticmethod
    def tirar_dados_ordenados(cant):
        return sorted(choices(range(1, 6), k=cant), reverse=True)
