# Assets del mapa clásico

Los sprites de países se referencian desde `paises.toml` como SVG y conservan
el PNG con el mismo nombre como respaldo. El renderer de Qt mantiene el
`viewBox` y vuelve a dibujar el SVG al hacer zoom; si un SVG no se puede abrir,
`Pais` carga automáticamente el PNG equivalente.

Los SVG conservan el tamaño lógico y la paleta del sprite original. Las
posiciones, los offsets de unidades y las conexiones siguen siendo datos de
`paises.toml` y `adyacencias.toml`, por lo que cambiar la resolución del asset
no cambia las reglas ni el grafo del mapa.
