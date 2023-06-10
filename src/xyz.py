import tomllib


class XYZ:
    def __init__(self):
        with open("src/paises.toml") as f:
            toml_string = f.read()
            self.parsed_toml = tomllib.loads(toml_string)
        self.cartas = self.parsed_toml["Cartas"]
        del self.parsed_toml["Cartas"]

    def paises(self):
        return [k for k in self.parsed_toml]

    def coordenadas(self, pais):
        p = self.parsed_toml[pais]
        return p["pos_x"], p["pos_y"], p["army_x"], p["army_y"]

    def get_cartas(self):
        return self.cartas

    def img_path(self, pais):
        return self.parsed_toml[pais]["file"]

    def continente(self, pais):
        return self.parsed_toml[pais]["continente"]
