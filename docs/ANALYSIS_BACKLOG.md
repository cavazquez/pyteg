# Decisiones de los análisis de producto

Fecha de revisión: 9 de octubre de 2026.

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

**Veredicto: implementado para los mapas.**

Los países y el tablero de Clásico y Revancha utilizan fuentes SVG editables.
La escena conserva siluetas, etiquetas, rutas, selección y marcadores de
misiles al cambiar el zoom. `smoke_visual_map.py` verifica carga y capturas
con varios tamaños y simulaciones de visión de color; wheel y Nuitka incluyen
estos recursos. Los PNG que siguen en cartas y dados no requieren
una conversión adicional para el funcionamiento actual.

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

`get_available_languages()` ofrece `es` y `en`. Los dos catálogos incorporan
los controles de los modos local, LAN y por archivos, las situaciones y los
nuevos diálogos. Cada release recompila los `.mo` desde los `.po` versionados.
Los idiomas adicionales siguen pendientes de prioridad de usuarios y revisión
humana; no se toma el inventario antiguo de cadenas como una medición vigente.

## #203 — objetivo general de 30 países

**Veredicto: implementado y coherente.**

`DEFAULT_VICTORY_COUNTRIES = 30` alimenta `GameConfig`, el gestor de
configuración y el diálogo de consulta. La ventana de administración tenía un
valor específico hardcodeado de 50; ahora usa la misma constante y comienza
con 30 países. Desactivar el checkbox sigue enviando `0`, que significa
controlar todos los países. El simulador conserva `--victory 0` como una
opción explícita de prueba, no como cambio del default del servidor.

## #205 — cartas de situaciones

**Veredicto: implementado.**

El catálogo y el runtime de situaciones definen los efectos y la selección
individual de cartas. El administrador puede habilitarlas o deshabilitarlas en
cualquiera de los dos mapas. La franja Qt muestra la carta, los afectados y las
tiradas públicas; los guardados, snapshots, turnos y repeticiones conservan ese
estado. Los smokes Qt y TCP cubren ambas combinaciones de mapa y reglas.
El contrato se mantiene en [`SITUATION_CARDS.md`](SITUATION_CARDS.md).

## #207 — `Client_Receptor`

**Veredicto: no reintroducir; responsabilidad cubierta.**

No hay referencias funcionales al nombre histórico. `ConnectionClient` recibe
bytes, `NulDelimitedUtf8Codec` reconstruye frames, `ClientEventProcessor`
actualiza `ClientStateModel`, `QtClientStateAdapter` proyecta el estado público
y `ClientTaskManager` mantiene las tareas de eventos privados. El mismo modelo
sin Qt lo usa el simulador y las pruebas. Recuperar el nombre agregaría una
capa duplicada y volvería a acoplar recepción con widgets; sólo tendría sentido
un nuevo puerto si aparece otro transporte con requisitos distintos.

## Resultado vigente

Están implementadas las conexiones visuales, legibilidad de cartas, objetivo
predeterminado, fuentes SVG de los mapas, cartas de situaciones, guardados,
descubrimiento LAN, migración del anfitrión, turnos por archivos, repeticiones,
bots básicos y pantalla de inicio común.

Quedan para nuevas tandas: dificultad y personalidad de los bots, mejoras de
accesibilidad a partir de uso real, revisión humana de traducciones y eventual
incorporación de otros idiomas. UPX sigue diferido hasta contar con medidas
comparables de distribución y arranque por plataforma. La limpieza de
revisiones antiguas de issues y comentarios en GitHub sigue pendiente por
pedido del usuario; este release no la reabre.
