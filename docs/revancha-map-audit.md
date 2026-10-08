# Auditoría del mapa Revancha de Pyteg

Este documento fija el inventario y el grafo que debe usar el tema `revancha`
de Pyteg, junto con las decisiones tomadas al comparar las fuentes de #225.
El fixture estructural asociado es
[`tests/fixtures/revancha_map_audit.toml`](../tests/fixtures/revancha_map_audit.toml).

## Datos de referencia

El fixture estructural fija 72 países en siete continentes y 134 aristas no
dirigidas. Los datos ejecutables se mantienen en `themes/revancha/paises.toml`
y `themes/revancha/adyacencias.toml`. Los IDs normalizan acentos y variantes
de nombres para que cliente, servidor y simulador usen el mismo inventario.
El mapa dispone de tarjetas de países y continentes, objetivos, situaciones
y misiles. La revisión del 8 de octubre de 2026 resuelve las dos aristas que
estaban pendientes sin agregarlas: el grafo conserva sus 134 conexiones.

### Procedencia y criterio de decisión

- **Tablero de referencia:** fotografía de colores de 800×600 aportada por el
  usuario, identificada como
  `codex-clipboard-ed8184cc-a250-49f8-aad3-aa452154cde3.png`. Es la misma referencia
  elegida para los contornos de #227. Se usa para distinguir países, fronteras y
  extremos de los puentes, no para inferir vecindad por geografía real.
- **Reglamento consultado:** documento de 40 páginas; SHA-256
  `e6b3f6b021f86e577bc1c1c50f84ad39c99385cf4bfff737678c3715269a8047`.
  La página 5 fija 72 países y siete continentes; la 12 define adyacencia por
  frontera común o puente sobre agua; las páginas 19, 30 y 33 aportan ejemplos.
  No incluye una matriz completa de adyacencias.
- **Matrices auxiliares:** aportaron la transcripción inicial de 134 aristas.
  Su coincidencia sirve como contraste, pero una reconstrucción visual o una
  implementación auxiliar no basta para agregar una conexión ausente del
  tablero elegido.

La fotografía y el PDF se consultan como referencias externas y no se
distribuyen con el tema. El fixture registra su procedencia sin incorporar
logotipos ni assets comerciales. Cuando un ejemplo textual discrepa del
tablero elegido, la decisión se registra como parte del mapa de Pyteg; no se
atribuye a todas las ediciones de otros productos.

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

## Grafo auditado para Pyteg

El fixture contiene las 134 aristas aceptadas para este mapa.
Cada arista aceptada se almacena en las dos direcciones. La prueba
`test_audited_graph_is_complete_and_symmetric` rechaza nombres desconocidos,
lazos, duplicados, asimetrías o cambios de conteo. Otras pruebas comparan el
tema cargado en modo estricto contra el fixture: los 72 IDs, la pertenencia a
los siete continentes y los vecinos de cada país deben coincidir exactamente.

Los puentes largos registrados en `Puentes.consenso`, tanto entre continentes
como dentro de Oceanía, son:

- Alaska–Chukchi y Alaska–Kamchatka.
- Groenlandia–Islandia.
- California–Tonga.
- Brasil–Sahara y Uruguay–Nigeria.
- España–Sahara y Polonia–Egipto.
- Chile–Australia.
- India–Sumatra y Filipinas–Australia.

Las conexiones de agua se dibujan como rutas visuales;
no se deben inferir desde la proximidad de dos sprites.
Además, `FronterasIntercontinentales.pares` enumera las 20 aristas entre
continentes, incluidas las terrestres. Una prueba exige que la lista coincida
con la pertenencia continental y el grafo del fixture. Las rutas más cortas y
las separaciones de la geometría se declaran en `ConexionesVisuales` del tema;
la prueba de cobertura verifica que toda arista jugable tenga una frontera
visible o una ruta.

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

## Discrepancias resueltas

Las decisiones siguientes están en `Discrepancias.resueltas` del fixture.
`Meta.aristas_pendientes` y `Discrepancias.pendientes` quedan vacíos.

- **Gran Bretaña–Francia: excluida.** El puente al sudoeste de Gran Bretaña
  termina en Portugal en la fotografía de referencia. Se conserva
  `GranBretana–Portugal`; la conexión a Francia de una reconstrucción auxiliar
  no se adopta. Los vecinos completos de Gran Bretaña quedan fijados en
  Alemania, Irlanda y Portugal. El mapa clásico tiene su conexión propia con
  España.
- **Irak–Ucrania: excluida.** En la referencia, la zona de Albania e Irán
  separa ambos países y no aparece un puente directo entre ellos. Se conserva
  `Iran–Ucrania`, coherente con los ejemplos de las páginas 30 y 33 del
  reglamento. Esos ejemplos corroboran Irán–Ucrania; por sí solos no demostrarían
  la ausencia de Irak–Ucrania. Los vecinos completos de Ucrania son Albania,
  Bielorrusia, Irán, Polonia y Rusia.
- **Uruguay–Mauritania: excluida para este tema.** El ejemplo de la página 12
  del reglamento nombra Mauritania–Uruguay. El puente de la fotografía de
  colores termina en Nigeria, y las dos matrices auxiliares coinciden con
  Uruguay–Nigeria. Pyteg adopta esa conexión de su tablero de referencia.
  Se documenta la diferencia sin agregar ambos destinos ni afirmar que el texto
  sea una errata confirmada.

Estas exclusiones se comprueban en ambas direcciones, junto con las conexiones
aceptadas que explican cada decisión. Cambiar el mapa exige actualizar su
auditoría, el fixture y los datos ejecutables en el mismo cambio.

La auditoría de #225 queda definida para el mapa de Pyteg. La legibilidad de
etiquetas y marcadores y la revisión de colores de #227 siguen siendo tareas
de presentación independientes.
