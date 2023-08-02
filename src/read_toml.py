import tomllib


class ReadToml:
    def __init__(self, toml_string):
        #with open("src/paises.toml") as f:
        #    toml_string = f.read()
        #    self.parsed_toml = tomllib.loads(toml_string)
        self.parsed_toml = tomllib.loads(toml_string)
        self.continentes = {}
        self.paises = {}
        self.cartas = self.parsed_toml["Cartas"]
        del self.parsed_toml["Cartas"]

        for continente in self.parsed_toml:
            datos = self.parsed_toml[continente]
            self.continentes[continente] = (datos.get("pos_x"), datos.get("pos_y"))
            del datos["pos_x"]
            del datos["pos_y"]
            self.paises[continente] = datos

    def todos_los_paises(self):
        res = []
        for continente in self.get_continentes():
            for pais in self.get_paises(continente):
                res.append(pais)

        return res

    def get_paises(self, continente):
        return self.paises[continente]

    def get_continentes(self):
        return [k for k in self.continentes]

    def coordenadas_continente(self, continente):
        return self.continentes[continente]

    def coordenadas(self, pais):
        continente = self.continente(pais)
        p = self.paises[continente][pais]
        return p["pos_x"], p["pos_y"], p["army_x"], p["army_y"]

    def get_cartas(self):
        return self.cartas

    def img_path(self, pais):
        continente = self.continente(pais)
        return self.paises[continente][pais]["file"]

    def continente(self, pais):
        for continente in self.get_continentes():
            if pais in self.get_paises(continente):
                return continente
