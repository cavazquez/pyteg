import tomllib


class TomlReader:
    def __init__(self, toml_string):
        self.parsed_toml = tomllib.loads(toml_string)
        self.continentes = {}
        self.paises = {}
        self.cartas = self.parsed_toml["Cartas"]
        del self.parsed_toml["Cartas"]

        # Inicializar adyacencias
        self.adyacencias = {}
        if "Adyacencias" in self.parsed_toml:
            self.adyacencias = self.parsed_toml["Adyacencias"]
            del self.parsed_toml["Adyacencias"]

        for continente in self.parsed_toml:
            if not isinstance(self.parsed_toml[continente], dict):
                continue

            datos = self.parsed_toml[continente]
            if "pos_x" in datos and "pos_y" in datos:
                self.continentes[continente] = (datos.get("pos_x"), datos.get("pos_y"))
                del datos["pos_x"]
                del datos["pos_y"]
                self.paises[continente] = datos

    def todos_los_paises(self):
        res = []
        for continente in self.get_continentes():
            res.extend(self.get_paises(continente))

        return res

    def get_paises(self, continente):
        return self.paises[continente]

    def get_continentes(self):
        return list(self.continentes)

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
        return None

    def obtener_paises_adyacentes(self, pais):
        """
        Devuelve la lista de países adyacentes al país especificado.

        Args:
            pais (str): Nombre del país del que se quieren obtener los adyacentes

        Returns:
            list: Lista de nombres de países adyacentes,
            o lista vacía si no hay adyacentes definidos
        """
        return self.adyacencias.get(pais, [])
        return None
