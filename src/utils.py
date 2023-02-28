import tomllib


def build_mapa():
    with open('paises.toml') as f:
        toml_string = f.read()
        parsed_toml = tomllib.loads(toml_string)

    mapa = {k: [1, parsed_toml[k]['continente'], None] for k in parsed_toml}

    return mapa


def rotar_jugadores(jugadores):
    print('Rotar jugadores')
    primer_elemento = jugadores[0]
    jugadores = jugadores[1:]
    jugadores.append(primer_elemento)
    return jugadores
