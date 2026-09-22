# Cartas de situaciones

Las cartas de situaciones son una regla opcional del servidor. El mapa y el
ruleset se configuran por separado: un mapa aporta países, propietarios y
continentes; el ruleset aporta el mazo y sus efectos.

La configuración predeterminada es `none`, que instala un objeto nulo y deja
el comportamiento clásico sin cambios. Para habilitar el mazo inicial:

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

El ruleset `revancha` contiene 50 cartas:

- 20 de `Combate clásico`.
- 4 de `Nieve`: suma un dado al defensor, hasta cuatro.
- 4 de `Viento a favor`: suma un dado al atacante, hasta cuatro.
- 4 de `Crisis`: tira un dado por jugador al revelar la carta; todos los
  empatados en el menor resultado no pueden reclamar tarjeta de país durante
  esa ronda.
- 4 de `Refuerzos extras`: suma la mitad entera de los países ocupados al
  refuerzo general de cada jugador.
- 4 de `Fronteras abiertas`: permite atacar sólo entre continentes distintos.
- 4 de `Fronteras cerradas`: permite atacar sólo dentro del mismo continente.
- 6 de `Descanso`: el color indicado no puede atacar ni mover unidades, pero
  sí puede colocar refuerzos.

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
