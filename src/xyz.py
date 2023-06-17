import tomllib


class XYZ:
    def __init__(self):
        with open("src/paises.toml") as f:
            toml_string = f.read()
            self.parsed_toml = tomllib.loads(toml_string)
        self.continentes = {}
        self.paises = {}
        self.cartas = self.parsed_toml["Cartas"]
        del self.parsed_toml["Cartas"]

        for continente in self.parsed_toml:
            datos  = self.parsed_toml[continente]
            self.continentes[continente] = (datos.get('pos_x'), datos.get('pos_y'))
            del datos['pos_x']
            del datos['pos_y']
            for k in datos:
                self.paises[k] = datos.get(k)

    def paises(self):
        return [k for k in self.paises]

    def coordenadas_continente(self, continente):
        return self.continentes[continente]

    def coordenadas(self, pais):
        p = self.paises[pais]
        return p["pos_x"], p["pos_y"], p["army_x"], p["army_y"]

    def get_cartas(self):
        return self.cartas

    def img_path(self, pais):
        return self.paises[pais]["file"]

    def continente(self, pais):
        return self.paises[pais]["continente"]
