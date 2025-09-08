from pathlib import Path

from src.toml_reader import TomlReader


def build_mapa():
    # Crear el lector TOML
    toml_path = Path("themes/classic/paises.toml")
    toml_content = toml_path.read_text(encoding="utf-8")
    reader = TomlReader(toml_content)

    # Construir el diccionario del mapa
    # Ahora cada país tendrá: [unidades, continente, dueño, [paises_adyacentes]]
    mapa = {}
    paises = reader.todos_los_paises()

    # Primero creamos todos los países con su información básica
    for pais in paises:
        continente = reader.continente(pais)
        # Inicializamos con unidades=1, continente, dueño=None, paises_adyacentes=[]
        mapa[pais] = [1, continente, None, []]

    # Luego agregamos las adyacencias a cada país
    for pais in paises:
        # Obtenemos los países adyacentes del lector TOML
        adyacentes = reader.obtener_paises_adyacentes(pais)
        # Aseguramos que el país exista en el mapa antes de agregar adyacencias
        if pais in mapa:
            mapa[pais][3] = adyacentes

    return mapa
