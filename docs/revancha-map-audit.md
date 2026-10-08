# Auditoría del mapa Revancha de Pyteg

Este documento fija el inventario que debe usar el tema `revancha` y separa los
datos confirmados de las decisiones que todavía necesitan cotejo directo con un
tablero legible. El fixture estructural asociado es
[`tests/fixtures/revancha_map_audit.toml`](../tests/fixtures/revancha_map_audit.toml).

## Datos de referencia

El fixture estructural fija 72 países en siete continentes y 134 aristas no
dirigidas. Los datos ejecutables se mantienen en `themes/revancha/paises.toml`
y `themes/revancha/adyacencias.toml`. Los IDs normalizan acentos y variantes
de nombres para que cliente, servidor y simulador usen el mismo inventario.
El mapa dispone de tarjetas de países y continentes, objetivos, situaciones
y misiles. Las dos discrepancias pendientes permanecen fuera del grafo.

## Inventario canónico

Los nombres siguientes son IDs ASCII para TOML y protocolo. La interfaz podrá
mostrar los nombres con tildes; no se deben crear aliases paralelos.

| Continente | Cantidad | Países |
| --- | ---: | --- |
| América del Norte | 12 | California, Nueva York, Las Vegas, Florida, Chicago, Terranova, Labrador, Canadá, Oregón, Isla Victoria, Alaska, Groenlandia |
| América Central | 6 | México, Honduras, El Salvador, Nicaragua, Cuba, Jamaica |
| América del Sur | 8 | Brasil, Argentina, Uruguay, Chile, Colombia, Bolivia, Paraguay, Venezuela |
| Europa | 16 | Islandia, Irlanda, Gran Bretaña, Noruega, Finlandia, Bielorrusia, Portugal, España, Francia, Alemania, Italia, Croacia, Serbia, Polonia, Albania, Ucrania |
| África | 8 | Sahara, Egipto, Etiopía, Nigeria, Angola, Mauritania, Madagascar, Sudáfrica |
| Asia | 16 | Rusia, Siberia, Chechenia, Chukchi, Kamchatka, Irán, Irak, China, Corea, Japón, Malasia, Turquía, Israel, Arabia, India, Vietnam |
| Oceanía | 6 | Sumatra, Filipinas, Tonga, Australia, Tasmania, Nueva Zelandia |

El total es `12 + 6 + 8 + 16 + 8 + 16 + 6 = 72`. Cada país aparece una sola
vez y pertenece a un único continente.

## Grafo conservador

El fixture contiene las 134 aristas aceptadas para este mapa.
Es una base conservadora para validar la estructura, no una autorización para
rellenar las dos discrepancias pendientes. Cada arista aceptada se almacena en
las dos direcciones y la prueba
`test_consensus_graph_is_complete_and_symmetric` rechaza nombres desconocidos,
lazos, asimetrías o cambios de conteo.

Los puentes intercontinentales que están en el consenso incluyen:

- Alaska–Chukchi y Alaska–Kamchatka.
- Groenlandia–Islandia.
- California–Tonga.
- Brasil–Sahara y Uruguay–Nigeria.
- España–Sahara y Polonia–Egipto.
- Chile–Australia.
- India–Sumatra y Filipinas–Australia.

Las conexiones de agua se dibujan como rutas visuales;
no se deben inferir desde la proximidad de dos sprites.

## Geometría y apariencia

`themes/revancha/geometry/board-layout.toml` contiene los 72 contornos trazados
sobre la foto frontal del tablero de colores compartida durante el desarrollo,
en coordenadas de referencia de 800×600. También fija la posición y orientación
de cada etiqueta y la posición deseada del marcador. Los contornos reemplazan
la aproximación anterior basada en áreas alrededor de centros: reproducen las
franjas de Norteamérica, el extremo alargado de Sudamérica, las penínsulas y las
islas de la referencia. Son trazados vectoriales interpretados desde una foto,
no un escaneo exacto.

Para regenerar los SVG y las posiciones:

```bash
uv run python themes/revancha/geometry/generate_revancha_map.py
```

El generador crea una partición común sin rellenos superpuestos, ubica los
marcadores dentro de cada país y agrega una ruta dorada para toda arista del
grafo cuyos contornos quedan separados. Así las islas y las separaciones no
ocultan conexiones. El grafo `[Adyacencias]` conserva sus 134 aristas y los IDs
existentes; el mapa clásico usa sus propios recursos.

La escena carga el mar y el marco como decoración pasiva, y las
etiquetas y los bordes como una segunda capa. La selección y los efectos de
batalla siguen actuando sobre los SVG individuales de los países.

Las pruebas verifican inventario, sitios de clic en los 72 marcadores, ausencia
de solapamientos y cobertura visual de todas las aristas. CI genera capturas
de los dos mapas en 1024×600, 1280×800 y 1920×1080.

## Discrepancias pendientes

Hay dos decisiones que no se deben resolver por intuición geográfica:

- Una reconstrucción visual pública muestra `Gran Bretaña–Francia`, mientras
  que el consenso de las dos implementaciones auxiliares declara
  `Gran Bretaña–Portugal` y no declara Francia.
- Las reconstrucciones comparadas difieren sobre `Irak–Ucrania`.

Ninguna de esas dos aristas cuenta con confirmación suficiente. Por eso no se
agregan al grafo ejecutable: quedan en `Meta.aristas_pendientes` y
`Discrepancias.pendientes` del fixture. El tema no puede habilitarlas hasta
resolver y documentar esas decisiones.

La resolución de estas discrepancias forma parte de #225. #226 debe consumir el
fixture, mantener los IDs y fallar si se intenta construir el tema con un país,
continente o frontera fuera de este inventario auditado.
