# Assets del mapa clásico

Los sprites de países se referencian desde `paises.toml` como SVG y conservan
el PNG con el mismo nombre como respaldo. El renderer de Qt mantiene el
`viewBox` y vuelve a dibujar el SVG al hacer zoom; si un SVG no se puede abrir,
`Pais` carga automáticamente el PNG equivalente.

Los SVG conservan el tamaño lógico y la paleta del sprite original. Las
posiciones, los offsets de unidades y las conexiones siguen siendo datos de
`paises.toml` y `adyacencias.toml`, por lo que cambiar la resolución del asset
no cambia las reglas ni el grafo del mapa.

En `adyacencias.toml`, las conexiones `Alaska–Kamchatka` y
`Chile–Australia` usan `envolver = "horizontal"`: los puntos listados marcan
la salida por el borde izquierdo y la reentrada por el derecho. El renderer
las dibuja como dos tramos separados, con flechas en los extremos del mapa.
El resto de las rutas recorta sus extremos al contorno visible de cada país y
descarta waypoints ocultos dentro de los sprites de salida o llegada.

Las masas de Norteamérica, Sudamérica, Europa, África y Asia se definen por
una máscara de bloque y una partición etiquetada a 4× en `geometry/`. Los
SVG de los 41 países continentales, los cinco contornos exteriores y sus
divisiones internas se generan a partir de esas mismas máscaras mediante
`scripts/generate_classic_geometry.py`. La escena dibuja las divisiones una
sola vez; las siluetas individuales siguen siendo interactivas y tienen PNG
de respaldo. Los nueve países insulares mantienen sus siluetas independientes.

Para cambiar una frontera terrestre, se edita la partición y se regenera. El
comando `uv run python scripts/generate_classic_geometry.py --check` comprueba
que los SVG y PNG publicados coincidan con las fuentes. La tabla de reglas en
`adyacencias.toml` sigue siendo independiente y debe coincidir con los
contactos terrestres y las rutas dibujadas.
