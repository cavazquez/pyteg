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

Los SVG de `Canada–NuevaYork`, `Aral–Mongolia`, `China–Iran`,
`China–Mongolia`, `China–Siberia`, `India–Iran` e `Iran–Mongolia` comparten
ahora un tramo vectorial corto: cada extensión termina en el contorno del país
vecino. Los PNG equivalentes se regeneraron como respaldo del mismo dibujo; el
grafo de adyacencias no cambia.
