from dataclasses import dataclass

@dataclass
class TarjetaDePais:
    pais: str
    simbolo: str

    def dame_pais(self):
        return self.pais

    def dame_simbolo(self):
        return self.simbolo
