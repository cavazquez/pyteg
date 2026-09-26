# TEG La Revancha

Este directorio contiene los datos y recursos aislados de Revancha. El inventario
de 72 países y el grafo de 134 aristas parten de la auditoría en
`docs/revancha-map-audit.md`.

`paises.toml` coloca los territorios siguiendo la foto frontal del tablero
compartida para #227. Los SVG son originales del repositorio: las masas
continentales y las particiones de países son aproximaciones vectoriales. El
generador asigna cada píxel de tierra a un solo país, abre una separación entre
países sin adyacencia jugable y coloca el marcador de unidades dentro de la
silueta. Se pueden regenerar con
`python themes/revancha/geometry/generate_revancha_map.py`.

`adyacencias.toml` conserva el grafo auditado. Las rutas visuales muestran sus
puentes confirmados; no habilitan movimientos. Al seleccionar un país, el mapa
resalta todos sus vecinos jugables y dibuja rutas temporales entre ellos. Esto
permite descubrir también las conexiones que no comparten una frontera en la
composición aproximada. Gran Bretaña–Francia e Irak–Ucrania siguen fuera del
grafo hasta resolver las discrepancias pendientes.
