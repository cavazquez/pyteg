import tomllib


class XYZ:
    def __init__(self):
        with open("src/paises.toml") as f:
            toml_string = f.read()
            self.parsed_toml = tomllib.loads(toml_string)
        self.continentes = {}
        self.cartas = self.parsed_toml["Cartas"]
        del self.parsed_toml["Cartas"]

        for continente in self.parsed_toml:
            datos  = self.parsed_toml[continente]
            print(datos)
            self.continentes[continente] = (datos['pos_x'])

    def paises(self, continente):
        return [k for k in self.parsed_toml]

    def coordenadas(self, pais, continente):
        p = self.parsed_toml[continente][pais]
        return p["pos_x"], p["pos_y"], p["army_x"], p["army_y"]

    def get_cartas(self):
        return self.parsed_toml['Cartas']

    def img_path(self, pais, continente):
        return self.parsed_toml[pais]["file"]

    def continente(self, pais, continente):
        return self.parsed_toml[pais]["continente"]
