# Auditoría del mapa del mapa Revancha

Este documento fija el inventario que debe usar el tema `revancha` y separa los
datos confirmados de las decisiones que todavía necesitan cotejo directo con un
tablero legible. El fixture estructural asociado es
[`tests/fixtures/revancha_map_audit.toml`](../tests/fixtures/revancha_map_audit.toml).

## Fuentes y nivel de confianza

   confirma que el tablero tiene 72 países en siete continentes. También da
   ejemplos de conexiones y puentes: Alaska–Chukchi, Chile–Australia,
   Argentina–Brasil y España–Portugal.
   confirma el conjunto de componentes de esta edición (72 tarjetas de países,
   siete tarjetas de continente, objetivos, situaciones y misiles).
3. El inventario completo de nombres y su distribución se cotejó con la lista
   fuente auxiliar, no una especificación de el editor del juego de mesa.
4. Para las adyacencias se compararon dos implementaciones públicas auxiliares:
   [Kamchatka `mapa.json`](https://github.com/ericbrandwein/kamchatka/blob/master/core/assets/mapa.json)
   Tras normalizar acentos y variantes (`Kamtchatka`/`Kamchatka`,
   `Nueva Zelanda`/`Nueva Zelandia`) coinciden en 134 aristas no dirigidas.

No se copiaron países ni fronteras del mapa clásico para completar huecos. La
declara 43 aristas adicionales que no aparecen en ese consenso auxiliar; se
conserva como referencia de discrepancias y no como fuente normativa.

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

El fixture contiene las 134 aristas que aparecen en ambas fuentes auxiliares.
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

El reglamento usa además `Alaska–Chukchi` y `Chile–Australia` como ejemplos de
fronteras abiertas. Las conexiones de agua se dibujarán como rutas visuales en
#227; no se deben inferir desde la proximidad de dos sprites.

## Discrepancias pendientes

Hay dos decisiones que no se deben resolver por intuición geográfica. La
primera proviene de una reconstrucción fotográfica pública del tablero, como

- Una reconstrucción visual pública muestra `Gran Bretaña–Francia`, mientras
  que el consenso de las dos implementaciones auxiliares declara
  `Gran Bretaña–Portugal` y no declara Francia.
- la implementación auxiliar declara `Irak–Ucrania`; Kamchatka no la declara.

El reglas configuradas no enumera ninguna de esas dos aristas. Por eso no se
agregan al grafo ejecutable: quedan en `Meta.aristas_pendientes` y
`Discrepancias.pendientes` del fixture. El tema no puede habilitarlas hasta
cotejar una imagen legible del tablero original o una fuente normativa de el editor del juego de mesa.

La resolución de estas discrepancias forma parte de #225. #226 debe consumir el
fixture, mantener los IDs y fallar si se intenta construir el tema con un país,
continente o frontera fuera de este inventario auditado.
