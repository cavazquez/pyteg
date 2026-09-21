# Decisiones de los análisis de producto

Fecha de revisión: 21 de septiembre de 2026.

Este documento cierra los análisis de la lista visual y de distribución con
evidencia del código actual. Las reglas del servidor y el protocolo quedan
fuera de estos cambios salvo cuando se indica expresamente.

## #198 — conexiones sobre el agua

**Veredicto: implementado en #213.**

`themes/classic/adyacencias.toml` y `themes/test/adyacencias.toml` contienen el
grafo completo y `TomlReader.from_theme(..., strict=True)` valida cobertura y
simetría. El servidor construye el mapa desde ese lector, `map_rules.py` usa la
misma fuente para `son_adyacentes` y el simulador carga el archivo del tema.
Por lo tanto, las conexiones de juego ya son configurables y no hay una lista
paralela codificada en Python.

La escena `QCustomGraphicsScene` ahora crea, además, líneas opcionales declaradas
en `[[ConexionesVisuales]]` dentro de `adyacencias.toml`. Cada entrada valida
sus países, exige una adyacencia existente, acepta puntos intermedios y queda
por debajo de los sprites sin recibir eventos del mouse. Las líneas sólo son
presentación: `Adyacencias` sigue siendo la fuente de verdad de las reglas.

## #199 — símbolo de carta

**Veredicto: implementado.**

Los cuatro recursos clásicos son PNG de 95×145. El widget los escalaba al
cuadrado de 32×32, así que el aspecto conservado dejaba el glifo visible de
aproximadamente 21×32. Ahora usa un máximo de 48×48, una tarjeta de 140×120 y
placeholders con el mismo tamaño. La proporción del recurso se conserva y el
nombre de país mantiene su etiqueta. `tests/test_gui_tarjeta_widget.py`
comprueba el pixmap cargado y la geometría en Qt offscreen.

## #200 — migración de imágenes a SVG

**Veredicto: diferido.**

El inventario tiene 73 PNG y 2 SVG. El tema de prueba ya demuestra que
`QPixmap` y el lector aceptan SVG; el clásico usa PNG para siluetas de países,
cartas, dados, tablero e iconos. Convertir automáticamente las siluetas no
aporta un SVG de calidad sin redibujado manual, y no hay una medición de
memoria, carga o calidad HiDPI que justifique cambiar los assets existentes.
Los nuevos iconos geométricos pueden nacer en SVG y una migración futura debe
medir arranque, wheel y Nuitka por plataforma antes de sustituir recursos.

## #201 — compresión UPX

**Veredicto: diferido.**

El workflow ya construye cuatro variantes con Nuitka `--onefile --standalone`,
incluye los recursos y verifica los nombres de los artefactos antes del release.
El checkout local no tiene `upx` y no sería válido recomendarlo con una medida
de una sola plataforma: hay que comparar tamaño y arranque en Linux, Windows,
macOS x86_64 y macOS arm64, además de observar firma, antivirus y
reproducibilidad. Hasta tener esos binarios, UPX agrega una variable de
distribución sin una mejora demostrada.

## #202 — diez idiomas adicionales

**Veredicto: diferido; primero cobertura de traducción.**

`get_available_languages()` sólo ofrece `es` y `en`. Hay dos catálogos PO:
el inglés contiene 186 `msgid` y el español 134, mientras que el extractor
actual sólo encuentra llamadas simples a `_()` y todavía existen textos
directos en widgets (por ejemplo, valores de campos y botones de sonido).
No hay datos de usuarios o distribución en el repositorio para justificar un
orden de diez idiomas ni revisores humanos para aceptar traducciones. Antes de
añadir idiomas hace falta medir cobertura, extraer cadenas dinámicas y definir
responsables de revisión; los códigos de mensajes de red deben permanecer
independientes del texto traducido.

## #203 — objetivo general de 30 países

**Veredicto: implementado y coherente.**

`DEFAULT_VICTORY_COUNTRIES = 30` alimenta `GameConfig`, el gestor de
configuración y el diálogo de consulta. La ventana de administración tenía un
valor específico hardcodeado de 50; ahora usa la misma constante y comienza
con 30 países. Desactivar el checkbox sigue enviando `0`, que significa
controlar todos los países. El simulador conserva `--victory 0` como una
opción explícita de prueba, no como cambio del default del servidor.

## #205 — cartas de situaciones

**Veredicto: diferido por especificación incompleta.**

Los temas sólo definen cartas de país (`Galeon`, `Globo`, `Canon` y
`Comodin`); el juego ya tiene canjes normales/especiales, misiles y objetivos
secretos. No existe una definición de cuándo se roba una carta de situación,
si es pública o privada, su efecto, una respuesta posible o su interacción con
snapshot, reconexión y revancha. Implementarla ahora duplicaría mecánicas sin
una variante escrita. Sólo debe abrirse una implementación cuando exista una
especificación cerrada y tests de privacidad/protocolo.

## #207 — `Client_Receptor`

**Veredicto: no reintroducir; responsabilidad cubierta.**

No hay referencias funcionales al nombre histórico. `ConnectionClient` recibe
bytes, `NulDelimitedUtf8Codec` reconstruye frames, `ClientEventProcessor`
actualiza `ClientStateModel`, `QtClientStateAdapter` proyecta el estado público
y `ClientTaskManager` mantiene las tareas de eventos privados. El mismo modelo
sin Qt lo usa el simulador y las pruebas. Recuperar el nombre agregaría una
capa duplicada y volvería a acoplar recepción con widgets; sólo tendría sentido
un nuevo puerto si aparece otro transporte con requisitos distintos.

## Resultado

El trabajo de código de esta tanda incluye la legibilidad de cartas, la
unificación del objetivo predeterminado y el trazado visual opcional de
conexiones marítimas. SVG, UPX, idiomas adicionales y cartas de situaciones
quedan documentados como decisiones diferidas con condiciones concretas para
retomarlos.
