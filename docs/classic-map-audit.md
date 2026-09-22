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
puentes entre continentes auditados y las rutas insulares `NuevaYork–Groenlandia`,
`Labrador–Groenlandia`, `GranBretana–Islandia`, `GranBretana–Espana`,
`Japon–Kamchatka`, `Australia–Sumatra`, `Australia–Borneo` y `Australia–Java`.
La conexión `GranBretana–Espana` pertenece al grafo clásico aunque ambos países
estén en Europa; se dibuja porque sus sprites quedan separados en la escena.
Las fronteras terrestres restantes se
leen en los contornos de los países y siguen estando respaldadas por
`Adyacencias`.

Los puntos intermedios se guardan sólo cuando una ruta necesita apartarse de
otro sprite o de sus fichas. El renderer las coloca detrás de los países, con
trazo discontinuo oscuro, extremos redondeados y ancho cosmético para que
mantengan contraste al cambiar el zoom.

La captura de regresión generada con Qt offscreen queda en
[`docs/screenshots/classic-map-bridges.png`](screenshots/classic-map-bridges.png).

## Límites de este cambio

La sección `Adyacencias` es la fuente de verdad para servidor, cliente y simulador. Las líneas dibujadas por Qt son una capa separada y se validan contra esa sección para impedir que una decoración sugiera un ataque inválido.

Las regresiones de `tests/test_classic_map_audit.py` cubren países, continentes, aristas, simetría y puentes intercontinentales. Si se elimina un país, se cambia de continente o se sustituye una frontera, el test falla antes de que el cambio llegue al servidor.

## Diagnóstico geométrico estricto

La regla visual es que dos interiores sólidos nunca se cubren, aunque los
países sean adyacentes. Las fronteras terrestres también deben tocarse dentro
de un píxel; las rutas incluidas en `ConexionesVisuales` quedan fuera de esa
exigencia porque se representan con una línea sobre el agua o el salto del
mapa.

El diagnóstico se ejecuta con:

```bash
QT_QPA_PLATFORM=offscreen uv run python scripts/check_map_overlaps.py \
  --theme classic --strict-boundaries --max-contact-gap 1
```

`--strict-boundaries` usa el interior sólido (`alpha >= 128`) para no confundir
antialiasing con cobertura. Mientras se corrige el layout heredado, el comando
funciona como informe explícito: la CI de layout conserva por ahora el umbral
histórico de bounding boxes y no oculta estos resultados.
