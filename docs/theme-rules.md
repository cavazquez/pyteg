# Mapas y perfiles de reglas

Al crear una partida se eligen por separado el **mapa** (`classic` o
`revancha`) y el **perfil de reglas** (Clásico o Revancha). Las cuatro
combinaciones son válidas: por ejemplo, se puede jugar en el mapa Clásico con
las reglas de Revancha.

En la aplicación se elige el mapa en **Conectar** y el perfil en la ventana
**Admin**. Desde la terminal, la misma combinación se inicia con
`pyteg-server --theme classic --rules-profile revancha`; luego el administrador
puede ajustar los módulos en la sala.

El selector de perfil marca de una vez todas las mecánicas de Clásico o de
Revancha. Debajo, cada casilla permite conservar o quitar por separado la
variante de Revancha de unidades iniciales, duelo de dos jugadores, dados de
defensa, refuerzos, progresión de canjes, reparto de objetivos y pactos. Una casilla
desmarcada usa la variante Clásico. Así se puede partir de cualquiera de los
dos perfiles y formar una partida mixta sin cambiar el mapa.

El mapa define países, fronteras, continentes, imágenes, distribución de
tarjetas de país y catálogo de objetivos secretos. Sus IDs de continentes y
sus bonos geográficos permanecen ligados a ese mapa. En particular, elegir
reglas de Revancha sobre el mapa Clásico no agrega América Central ni cambia
los nombres de los países. Los objetivos disponibles son siempre los que
pueden evaluarse en el mapa elegido.

La meta inicial de países se limita al tamaño del mapa. El mapa Clásico tiene
50 países, así que conserva la meta Revancha de 45. El servidor rechaza metas
manuales mayores que el total de países del mapa al intentar comenzar.

El perfil aporta los valores predeterminados de las mecánicas generales y de
victoria, misiles, objetivos y situaciones. En la sala, el administrador puede
activar cada grupo de reglas de Revancha y elegir por separado los objetivos
y las cartas de situación. La configuración efectiva se publica a todos los
clientes; el servidor es quien la aplica.

## Valores predeterminados

| Perfil | Países para ganar | Unidades en las primeras rondas | Dados máximos ataque/defensa | Objetivos secretos | Situaciones | Misiles |
| --- | ---: | ---: | ---: | --- | --- | --- |
| Clásico | 30 configurables; el lobby histórico usa todos los países | 6 / 3 | 3 / 2 | Desactivados | Desactivadas | Desactivados |
| Revancha | 45 | 8 / 4 | 3 / 3 | Activados | Los ocho tipos | Activados |

Ambos perfiles usan 20 segundos por turno de forma predeterminada. El
administrador puede modificar esa duración. Los bonos por continente y las
tarjetas de país no figuran en la tabla porque dependen del mapa.

## Selección de objetivos secretos

El control maestro **Objetivos secretos** habilita o deshabilita el grupo sin
cambiar las casillas individuales. Debajo se puede marcar cada objetivo por
separado. Una selección parcial limita el sorteo a los objetivos marcados.
Para iniciar con el grupo activo debe haber al menos un objetivo seleccionado
y suficientes objetivos para repartirlos según la modalidad. Con el grupo
apagado se permite dejar todas las casillas desmarcadas y no se asignan
objetivos secretos.

Los objetivos públicos o comunes no se reparten como objetivos secretos ni
aparecen en esta lista. La condición pública se configura con **Países para
ganar**. Los IDs y los requisitos geográficos de los objetivos privados
siempre provienen del mapa, independientemente del perfil seleccionado.

## Selección de cartas de situación

El control maestro **Cartas de situación** habilita o deshabilita el mazo sin
cambiar las casillas individuales. Se puede marcar cada uno de los ocho
efectos y cada carta física por separado. Marcar un efecto selecciona todas
sus copias; desmarcarlo las quita. Una selección parcial permite, por ejemplo,
conservar sólo algunas copias de «Combate clásico». Con el grupo activo debe
quedar al menos una carta seleccionada; con el grupo apagado se permiten cero
cartas y no se revela ninguna situación. Los tipos y sus cantidades figuran en
[Cartas de situaciones](SITUATION_CARDS.md).

El perfil Clásico empieza con las situaciones desactivadas y el de Revancha
con los ocho tipos activados. Esta opción puede usarse con cualquiera de los
dos mapas.

Al volver al lobby para otra partida se conserva el perfil y la mezcla de
módulos. Las selecciones de objetivos y cartas vuelven al catálogo completo;
el administrador puede ajustarlas para la próxima partida.

## Archivos y compatibilidad

Los perfiles se definen en `themes/<perfil>/reglas.toml`. Los mapas conservan
sus archivos `paises.toml`, `adyacencias.toml`, `cartas.toml` y
`objetivos_secretos.toml`. Un tema antiguo sin `reglas.toml` recibe los
valores históricos compatibles. Los archivos de reglas presentes se validan
al cargar; un valor inválido impide iniciar la partida.

El handshake comprueba que cliente y servidor usen el mismo mapa. Los
parámetros de reglas elegidos en la sala se comunican por la configuración y
el snapshot público. Los objetivos asignados y las manos de tarjetas siguen
siendo privados.

Este cambio de contrato de red usa la versión de protocolo 2; cliente y
servidor deben actualizarse juntos.
