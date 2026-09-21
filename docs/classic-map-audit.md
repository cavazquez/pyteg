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

## Límites de este cambio

La sección `Adyacencias` es la fuente de verdad para servidor, cliente y simulador. Las líneas dibujadas por Qt son una capa separada. En este cambio se conservaron únicamente las conexiones visuales que siguen siendo aristas válidas después de corregir el grafo; completar y ubicar visualmente los 15 puentes queda en [#220](https://github.com/cavazquez/pyteg/issues/220).

Las regresiones de `tests/test_classic_map_audit.py` cubren países, continentes, aristas, simetría y puentes intercontinentales. Si se elimina un país, se cambia de continente o se sustituye una frontera, el test falla antes de que el cambio llegue al servidor.
