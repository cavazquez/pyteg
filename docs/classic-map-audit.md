# Auditoría del grafo clásico del TEG

Fecha de la auditoría: 2026-09-21.

## Referencias

- [Matriz de adyacencias de Tenés Empanadas Graciela](https://github.com/wfx/teg/blob/master/common/limitrof.h): fuente primaria para compatibilidad con la implementación libre de TEG. La matriz GPL enumera las 50 posiciones del mapa y sus 89 aristas.
- [Reglamento de TEGNet](https://www.tegnet.com.ar/es/reglamento.htm): segunda implementación de TEG usada para contrastar reglas de partida en red; su página ofrece el reglamento de TEGNet y el reglamento de mesa.
- [Mapa del TEG](https://www.calculadorteg.com/mapa-del-teg.html): índice auxiliar para leer las fronteras y los puentes en lenguaje humano. No se usa como autoridad única.

## Resultado

El tema clásico queda definido por:

- 50 países en seis continentes: Sudamérica (6), Norteamérica (10), Europa (9), África (6), Asia (15) y Oceanía (4).
- 89 aristas no dirigidas y simétricas.
- 15 aristas entre continentes:
  `Alaska–Kamchatka`, `Brasil–Sahara`, `Chile–Australia`, `Colombia–México`,
  `Egipto–Israel`, `Egipto–Polonia`, `Egipto–Turquía`, `España–Sahara`,
  `Groenlandia–Islandia`, `India–Sumatra`, `Malasia–Borneo`, `Polonia–Turquía`,
  `Rusia–Aral`, `Rusia–Irán` y `Rusia–Turquía`.

La fuente anterior tenía relaciones de otro mapa en varios continentes. Entre las correcciones relevantes están `Chile–Australia`, `Brasil–Sahara`, `Polonia–Egipto`, `Polonia–Turquía`, `Rusia–Turquía`, `India–Sumatra` y `Malasia–Borneo`; también se eliminaron relaciones como `Italia–Egipto`, `Polonia–Tartaria`, `Java–Sumatra` y `Borneo–Sumatra`.

La decisión de usar esta matriz como baseline es de compatibilidad del software: pyteg busca interoperar con el mapa clásico de Tenés Empanadas Graciela y contrastar las reglas de red de TEGNet. No se presenta a Yetem como fuente de los datos de esta auditoría.

## Puentes visuales

`ConexionesVisuales` no crea reglas nuevas: es la representación de las
aristas que el jugador debe poder seguir cuando los sprites quedan separados
por agua o por el salto del mapa. La lista del tema clásico cubre los quince
puentes entre continentes auditados y trece rutas dentro de un continente
que atraviesan agua: `NuevaYork–Groenlandia`, `Labrador–Groenlandia`,
`GranBretana–Islandia`, `GranBretana–Espana`, `GranBretana–Alemania`,
`Islandia–Suecia`, `Japon–Kamchatka`, `China–Japon`,
`Madagascar–Egipto`, `Madagascar–Zaire`, `Australia–Sumatra`,
`Australia–Borneo` y `Australia–Java`.
La conexión `GranBretana–Espana` pertenece al grafo clásico aunque ambos países
estén en Europa; se dibuja porque sus sprites quedan separados en la escena.
Las fronteras terrestres restantes se
leen en los contornos de los países y siguen estando respaldadas por
`Adyacencias`.

Los puntos intermedios se guardan sólo cuando una ruta necesita apartarse de
otro sprite o de sus fichas. Alaska–Kamchatka y Chile–Australia envuelven el
mapa: la ruta termina en el borde izquierdo y reaparece desde el derecho, con
ambos extremos calibrados contra las flechas del `board.png` clásico. El
renderer crea dos subtramos independientes para que no haya una línea continua
cruzando el tablero. Las conexiones se colocan detrás de los países, con trazo
discontinuo oscuro, extremos redondeados y ancho cosmético para que mantengan
contraste al cambiar el zoom.

La captura de regresión generada con Qt offscreen queda en
[`docs/screenshots/classic-map-bridges.png`](screenshots/classic-map-bridges.png).

## Límites de este cambio

La sección `Adyacencias` es la fuente de verdad para servidor, cliente y simulador. Las líneas dibujadas por Qt son una capa separada y se validan contra esa sección para impedir que una decoración sugiera un ataque inválido.

Las regresiones de `tests/test_classic_map_audit.py` cubren países, continentes, aristas, simetría y puentes intercontinentales. Si se elimina un país, se cambia de continente o se sustituye una frontera, el test falla antes de que el cambio llegue al servidor.

## Diagnóstico geométrico estricto

La auditoría separa el relleno del trazo SVG y comprueba los interiores a
escala 4× para evitar falsos solapes del antialiasing a tamaño normal: un trazo
de frontera compartido no se considera territorio superpuesto. Las siluetas
visibles de las fronteras
terrestres deben tocarse dentro de un píxel; las rutas incluidas en
`ConexionesVisuales` se excluyen porque cruzan agua o el salto del mapa.

El diagnóstico se ejecuta con:

```bash
QT_QPA_PLATFORM=offscreen uv run python scripts/check_map_overlaps.py \
  --theme classic --strict-boundaries --max-contact-gap 1
```

Las cinco masas terrestres principales se guardan como bloques y particiones
comunes en `themes/classic/geometry/`: Norteamérica, Sudamérica, Europa,
África y Asia. Cada píxel de la partición a escala 4× pertenece exactamente a
un país o al agua; la unión de los 41 países continentales coincide píxel por
píxel con su bloque. `scripts/generate_classic_geometry.py` deriva de esa
misma partición los SVG individuales, el contorno exterior y las divisiones
internas, que se dibujan una sola vez en Qt. Así, dos países vecinos comparten
la *misma* frontera, sin alargar salientes para cerrar huecos. Los nueve países
insulares conservan sus siluetas independientes y sus rutas sobre agua.

Los pares que antes mostraban una barra —`Canada–NuevaYork`,
`Aral–Mongolia`, `China–Iran`, `China–Mongolia`, `China–Siberia`,
`India–Iran` e `Iran–Mongolia`— ahora comparten un tramo de la partición.
El grafo de reglas permanece igual. Las rutas visuales incluyen además
`GranBretana–Alemania`, `Islandia–Suecia` y `China–Japon`, conexiones que
atraviesan agua en el dibujo aunque sean adyacencias válidas.

Para verificar que los SVG no se alejaron de sus máscaras fuente:

```bash
uv run python scripts/generate_classic_geometry.py --check
```

La auditoría estricta ahora confirma cero solapamientos de relleno y cero
fronteras terrestres separadas. El gate adicional de bounding boxes permite
`Groenlandia–Islandia`, `Aral–Rusia`, `California–Colombia` y
`México–Colombia`: sus rectángulos se cruzan, pero el análisis de píxeles no
encuentra rellenos superpuestos en esos pares. Una regresión en
`tests/test_classic_map_audit.py` impide volver a introducir solapamientos de
relleno o huecos de frontera.
