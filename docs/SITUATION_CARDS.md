# Cartas de situaciones

Las cartas de situaciones son una regla opcional del servidor. El mapa y el
perfil de reglas se eligen por separado: el mapa aporta países, propietarios y
continentes; las situaciones funcionan con cualquiera de los dos mapas.

El perfil Clásico desactiva el mazo de forma predeterminada (`none`); el perfil
Revancha activa sus ocho tipos. En la sala, el control maestro **Cartas de
situación** enciende o apaga el grupo y conserva las casillas individuales.
Cada tipo permite marcar o desmarcar todas sus copias, y cada una de las 50
cartas físicas puede elegirse por separado. Con el grupo encendido debe
quedar al menos una carta marcada; con el grupo apagado se permiten cero
cartas y no se revela ninguna situación.

Para habilitar el mazo completo en un servidor configurado con el mapa
Clásico:

```bash
uv run pyteg-server --theme classic --situation-ruleset revancha
```

También se puede inyectar la configuración desde Python:

```python
server = Server(theme="classic", situation_ruleset="revancha")
```

## Ciclo de una partida

- La primera ronda conserva las reglas base y no revela una carta.
- Al iniciar cada ronda posterior el servidor revela exactamente una carta.
- La carta se revela antes de preparar los refuerzos del primer turno de esa
  ronda. Por eso los bonus consultan el mapa vigente y no un snapshot viejo.
- El inicio de ronda es idempotente: repetir la misma clave de ronda por una
  reconexión no roba otra carta ni vuelve a tirar Crisis.
- El mazo usa `SystemRandom` en producción. Las pruebas y simulaciones pueden
  inyectar `random.Random(seed)` para reproducibilidad.

El snapshot público incluye `situacion` con `id`, `nombre`, `efecto`,
`parametro` y `ronda`. No se agregan manos privadas ni datos de objetivos al
snapshot.

## Reglas disponibles

El ruleset de situaciones `revancha` contiene 50 cartas cuando están activos
todos los tipos. Los IDs usados para seleccionar cada tipo son:

- 20 de `classic_combat` (Combate clásico).
- 4 de `snow` (Nieve): suma un dado al defensor, hasta cuatro.
- 4 de `tailwind` (Viento a favor): suma un dado al atacante, hasta cuatro.
- 4 de `crisis` (Crisis): tira un dado por jugador al revelar la carta; todos
  los empatados en el menor resultado no pueden reclamar tarjeta de país
  durante esa ronda.
- 4 de `extra_reinforcements` (Refuerzos extras): suma la mitad entera de los
  países ocupados al refuerzo general de cada jugador.
- 4 de `open_borders` (Fronteras abiertas): permite atacar sólo entre
  continentes distintos.
- 4 de `closed_borders` (Fronteras cerradas): permite atacar sólo dentro del
  mismo continente.
- 6 de `rest` (Descanso): el color indicado no puede atacar ni mover unidades,
  pero sí puede colocar refuerzos.

El catálogo `available_situation_effects()` devuelve los tipos; el catálogo
`available_situation_cards()` devuelve los IDs de las 50 copias. La fábrica
`build_situation_deck` acepta `enabled_effects` para elegir tipos o
`enabled_cards` para elegir copias exactas. Cuando se indican cartas concretas,
esa lista tiene prioridad. Omitir el filtro conserva el mazo completo; pasar
una selección vacía crea un mazo vacío. Un ID desconocido produce un error.

Las elecciones de máximo de dados, redondeo de refuerzos y empates están
centralizadas en los efectos y cubiertas por tests. Si la edición física que
se quiere reproducir usa otra interpretación, se cambia el efecto o se crea
otro ruleset sin acoplarlo a nombres de países.

## Diseño

El código está en `pyteg/core/situaciones/`:

- `SituationCard` y `SituationContext` son modelos inmutables y expresan sólo
  datos del dominio.
- `SituationEffect` es la estrategia base. Cada carta concreta implementa
  únicamente la política que modifica.
- `NoSituationEffect` y `NoSituationCard` forman el Null Object para `none`,
  mazos agotados y mapas sin un color de descanso compatible.
- `SituationDeck` separa orden, descarte y aleatoriedad del mapa.
- `SituationRuntime` es el estado de una partida: revela, inicializa el
  efecto, conserva resultados de Crisis y delega validaciones.
- `catalog.py` es la fábrica/registro. Agregar un ruleset no requiere cambiar
  `Game` ni la GUI.

Los efectos reciben `IMapProtocol` y consultan sólo `paises()`,
`ocupado_por()` y `continente()`. No hay nombres de países ni continentes
clavados en el mazo, así que un tema compatible puede usar las mismas cartas.
Una carta `Descanso` cuyo color no participa se descarta y se intenta otra; si
no queda ninguna aplicable se usa el objeto nulo.

## Autoridad y extensiones

Las tareas TCP validan las restricciones de ataque, movimiento y reclamo
antes de modificar el dominio. Los clientes sólo renderizan la situación del
snapshot; el servidor sigue siendo la autoridad.

Para sumar una carta:

1. Añadir una estrategia pequeña en `effects.py`.
2. Registrarla en `_EFFECTS` y, si corresponde, en `build_situation_deck`.
3. Declarar qué capacidades del mapa necesita en `is_applicable`.
4. Cubrir el efecto con tests unitarios y una prueba de ronda idempotente.
5. Actualizar este documento y el contrato público si cambia el snapshot.

Los textos e imágenes de una futura interfaz deben tener una fuente y licencia
documentadas; el ruleset actual sólo usa nombres y datos propios del proyecto.
