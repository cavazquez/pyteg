# Simular una partida por TCP

`scripts/simulate_game.py` inicia el **servidor real en un proceso separado** y
conecta varios bots sin interfaz gráfica por sockets TCP de loopback. Los bots
configuran la sala, reparten refuerzos, atacan, conquistan, transfieren ejércitos
y finalizan turnos mediante los mensajes públicos del juego. No acceden al
estado interno del servidor.

## Ejecutar

Desde la raíz del repositorio, después de `uv sync`:

```bash
# Mapa clásico, 50 países, tres clientes, objetivo de victoria de 30 países.
uv run python -m scripts.simulate_game \
  --theme classic --clients 3 --victory 30 --seed 7 \
  --output-dir logs/simulations/classic-production-7

# Mapa de prueba: actualmente tiene DOS países, por lo que admite dos bots.
uv run python -m scripts.simulate_game \
  --theme test --clients 2 --victory 2 --seed 7 \
  --output-dir logs/simulations/test-production-7

# Revancha: reglas propias, objetivos secretos, canjes, misiles y reconexión.
uv run python -m scripts.simulate_game \
  --theme revancha --clients 5 --victory 30 --seed 234 \
  --secret-objectives --disconnect-client 2 --disconnect-after-turn 5 \
  --reconnect-client 2 --exercise-exchanges --require-finalized
```

Si ya existe el entorno virtual, se puede reemplazar `uv run python` por
`.venv/bin/python`. No hace falta levantar otro servidor: el script elige un
puerto efímero local y termina su proceso hijo al salir, incluso ante errores.
El directorio de salida se reutiliza y sobrescribe sus archivos en cada corrida;
usá nombres distintos para conservar varias ejecuciones.

`--victory 0` solicita controlar todos los países. Los límites predeterminados
son 300 segundos totales, 10 segundos para cada respuesta y 200 rondas. Se pueden
ajustar con `--timeout`, `--command-timeout` y `--max-rounds`. El tiempo de turno
se configura largo para que los bots avancen mediante comandos y no dependan del
timer para jugar.

`--secret-objectives` activa los objetivos secretos. El servidor de la simulación
recibe una fuente aleatoria derivada de `--seed`, mientras que el servidor real
usa entropía del sistema. El reporte incluye el objetivo asignado a cada identidad
y falla si falta, se duplica o se filtra entre clientes.

## Qué se comprueba

Cada comando lleva un `command_id` y el servidor responde con `command_result`;
los reintentos reciben el mismo resultado sin ejecutar la acción dos veces. Los
bots también negocian versión, tema y hash del mapa mediante `hello`, y validan
snapshots públicos con una revisión monotónica. Después de cada acción esperan
la confirmación y comprueban que todos observen el mismo tablero, con
propietarios válidos, todos los países presentes y al menos una unidad por país.

Para aceptar una victoria por países, todos los clientes deben recibir el mismo
ganador, ese jugador debe controlar el objetivo configurado y debe haber ocurrido
al menos una conquista. No alcanza con elegir un umbral que ya se cumple al
repartir. Con `--secret-objectives`, el servidor también puede terminar por un
objetivo secreto antes de alcanzar ese umbral; el harness acepta ambas condiciones
y verifica además que cada cliente conserve su objetivo privado.

Cada ejecución guarda:

- `result.json`: ganador observado por cliente, estado de sala, cantidad de
  turnos/acciones, tablero final, hash del tablero, errores y alcance de la
  prueba. También incluye `received_message_totals`,
  `country_update_messages` y bytes/tramas TCP para comparar el costo de una
  corrida antes y después de un cambio de transporte.
- `wire.jsonl`: todos los mensajes enviados y recibidos, con cliente y tiempo.
- `server.log`: salida del proceso servidor.

El workflow de CI ejecuta el flujo clásico y una partida de Revancha con cinco
clientes, objetivos secretos, canjes, misiles y una desconexión/reconexión
autenticada antes de exigir `--require-finalized`. Conserva
`logs/simulations/classic-197` y `logs/simulations/revancha-234` como artefactos,
también si alguna corrida falla.

Los registros están bajo `logs/`, que el repositorio ignora en Git.

Las actualizaciones del mapa son incrementales: la primera entrega a una
conexión contiene todos los países y las siguientes sólo los que cambiaron.
Un snapshot completo sigue siendo la vía de resincronización y actualiza el
caché incremental, por lo que no se pierde ningún estado ante una reconexión.

El smoke complementario de Qt conecta ventanas reales al mismo servidor y
comprueba lobby, desconexión y reconexión autenticada:

```bash
QT_QPA_PLATFORM=offscreen uv run python scripts/smoke_qt_multiclient.py \
  --clients 3
```

Este smoke cubre la capa Qt y su transporte; la partida completa continúa
siendo responsabilidad de `simulate_game`, que usa clientes headless para
ejercitar colocación, combate, conquistas, canjes y misiles. También hay un
recorrido Qt de partida completa, con tres ventanas reales, reconexión durante
la partida, una conquista y victoria:

```bash
QT_QPA_PLATFORM=offscreen uv run python scripts/smoke_qt_game.py --timeout 60
```

Ese smoke conserva el modelo de estado, el protocolo TCP, los comandos y los
eventos de batalla reales. En modo `offscreen` desacopla la actualización de
las 50 imágenes del tablero para que la prueba no dependa del backend gráfico;
`smoke_qt_multiclient` sigue cubriendo la construcción y conexión visual del
mapa.

Durante una reconexión Qt se espera primero el snapshot que marca la baja en el
servidor. El cliente recuperado envía `reconectar` antes de cualquier comando
de lobby; así no se rechaza un `set_username` mientras la sesión todavía está
pendiente de autenticación.

Los clientes que anuncian la capacidad `heartbeat` reciben un `ping` cuando su
socket queda inactivo y deben contestar `pong` con el mismo identificador. Si
no hay respuesta dentro del límite, el servidor cierra y limpia la conexión.
Los clientes antiguos que no anuncian esa capacidad conservan el modo de
recepción bloqueante.

Para comprobar el aislamiento de clientes lentos y la saturación de la cola de
salida, ejecutá el smoke de transporte:

```bash
uv run python scripts/stress_slow_clients.py
```

El smoke abre dos conexiones TCP reales. Una deja de leer y recibe tramas de
32 KiB hasta llenar la cola acotada; el servidor debe cerrarla sin bloquear al
productor. La otra drena en paralelo y debe recibir marcadores durante y
después de la saturación. El comando imprime evidencia JSON y devuelve un
código distinto de cero si el cliente saludable también se desconecta o si el
lento no recibe EOF. Se puede ajustar la presión con `--frames`,
`--payload-bytes` y `--timeout`.

## Victoria observada y cierre de partida

El reporte distingue `victory_observed` de `all_clients_finalized`. Una victoria
sólo certifica el ciclo completo si todos observan también `Finalizado`. El
servidor actual detiene el temporizador, bloquea acciones de juego y difunde ese
estado terminal; el chat sigue disponible para conservar la comunicación y la
barrera del harness.

Para comprobar el ciclo completo, usá el modo estricto:

```bash
uv run python -m scripts.simulate_game \
  --theme test --clients 2 --victory 2 --seed 7 \
  --deterministic-dice --require-finalized \
  --output-dir logs/simulations/test-deterministic-7-strict
```

El código de salida es `0` si la comprobación solicitada pasa, `1` ante errores
de protocolo, divergencias, rechazos o falta de victoria, y `2` si se verificó
la victoria pero el modo estricto no observó `Finalizado` en los clientes que
permanecieron conectados.

## Semilla y reproducibilidad

Con `--seed N`, el reparto, los dados del harness y la estrategia estable de
los bots producen el mismo resultado funcional. El reporte ordena
`country_counts` de mayor a menor y conserva una entrada para cada cliente,
incluidos los que terminan con cero países. Los colores siguen usando su fuente
productiva y los timestamps de la traza pueden variar, por lo que no se promete
identidad byte a byte.

Si se omite `--seed`, el script obtiene una semilla de `secrets.randbits` y la
guarda en `result.json` junto con `seed_source: "generated_by_secrets"`.
`--random-dice` mantiene los dados productivos y hace que esa corrida no sea
repetible aunque se indique una semilla. El servidor real nunca recibe una
semilla ni se parchea: usa `secrets` para dados y colores y `SystemRandom` para
objetivos secretos. `--deterministic-dice` es el modo reproducible del proceso
hijo del harness.

Para probar una baja durante la partida:

```bash
uv run python -m scripts.simulate_game \
  --theme classic --clients 4 --victory 30 --seed 801 \
  --disconnect-client 2 --disconnect-after-turn 5 \
  --require-finalized
```

`--disconnect-client` usa numeración basada en uno. El servidor conserva la
identidad, color y países del jugador que perdió la conexión, pero lo retira del
orden de turnos dentro de la transición serializada. `connected_clients_finalized`
certifica a los clientes que siguieron conectados; `all_clients_finalized` queda
en `false` si alguno fue desconectado, y `disconnected_clients` deja la evidencia
del evento.

Para comprobar la recuperación autenticada de esa misma sesión, agregá
`--reconnect-client` con el mismo número:

```bash
uv run python -m scripts.simulate_game \
  --theme classic --clients 3 --victory 30 --seed 123 \
  --disconnect-client 1 --disconnect-after-turn 2 \
  --reconnect-client 1 --require-finalized
```

El reemplazo recibe un ID temporal durante el handshake y sólo recupera el
ID original, color, países, nombre, tarjetas y turno después de presentar el
token privado de sesión. `reconnections` cuenta las recuperaciones observadas;
el reporte mantiene una sola identidad por jugador en `country_counts`.
La sesión recuperada sincroniza el estado actual y los eventos posteriores; no
se espera que reciba nuevamente eventos históricos de misiles o canjes que
ocurrieron antes de la reconexión.

## Canjes y misiles

El modo base no ejecuta acciones privadas de tarjetas ni misiles. Para probarlas
por TCP, el script ofrece modos explícitos:

```bash
# Canjes normales y especiales de tarjetas.
uv run python -m scripts.simulate_game \
  --theme classic --clients 5 --victory 30 --seed 800 \
  --exercise-cards --require-finalized

# Todos los canjes: tarjetas, canje especial y seis unidades por misil,
# seguido de lanzamientos contra países enemigos alcanzables.
uv run python -m scripts.simulate_game \
  --theme classic --clients 5 --victory 30 --seed 800 \
  --exercise-exchanges --require-finalized
```

`--exercise-missiles` habilita sólo el flujo de misiles; `--exercise-exchanges`
activa también la reclamación de tarjetas, el canje de tres tarjetas, el canje
especial país+tarjeta y el canje forzoso al alcanzar cinco tarjetas. El reporte
incluye `card_claims`, `card_exchanges`, `forced_card_exchanges`,
`special_exchanges`, `missile_exchanges` y `missile_launches`. Además, todos los
clientes conectados deben coincidir en el inventario público de misiles y en los
eventos de lanzamiento.

El servidor valida la fase antes de cada operación mutante: los canjes de
tarjetas y el canje especial ocurren durante `colocacion`; el reclamo de tarjeta,
el canje y lanzamiento de misiles ocurren durante `acciones`. El simulador
envía los comandos en ese orden y falla si alguno no llega a ejecutarse.

## Resultados observados en esta revisión

Con el código revisado y sin sustituir los dados productivos:

- **Base antes de #171 — clásico, tres clientes, objetivo 30, semilla 7:** victoria de `Bot_1` con
  31 países al terminar la ronda 10; los otros jugadores conservaron 11 y 8.
  Se jugaron 30 turnos, 223 ataques y 133 conquistas, en 17,493 segundos.
  Los tres clientes coincidieron en tablero y ganador; no recibieron errores.
  Todos conservaron `JUGANDO` después de la victoria.
- **Base antes de #171 — prueba, dos clientes, objetivo 2, semilla 7:** victoria de `Bot_1` con ambos
  países, después de 6 turnos y 9 ataques, en 0,921 segundos. Ambos clientes
  coincidieron en tablero y ganador; ambos conservaron `JUGANDO`.
- **Base antes de #171 — prueba con dados deterministas, dos repeticiones:** ambas terminaron con
  `Bot_2` como ganador, 8 turnos y 7 ataques. Coincidieron el tablero final,
  su hash SHA-256 y los contadores de comandos. El modo estricto devolvió `2`.
- **Después de #171 — prueba estricta, dos clientes, objetivo 2, semilla 7 y
  dados deterministas:** `Bot_2` controló ambos países tras 8 turnos y una
  conquista; ambos clientes observaron `Finalizado` y el modo estricto devolvió
  `0`.
- **Después de #171 — clásico estricto, seis clientes, objetivo 30, semilla 45:**
  `Bot_1` ganó con 35 países tras 108 turnos y 322 conquistas, en 45,287 segundos.
  Los seis clientes coincidieron en ganador y tablero, observaron `Finalizado` y
  no recibieron errores.
- **Canjes y misiles — clásico estricto, cinco clientes, objetivo 30, semilla 800:**
  `Bot_1` ganó con 33 países tras 66 turnos y 215 conquistas. Se observaron 215
  reclamaciones, 23 canjes normales, 39 canjes forzosos, 16 canjes especiales,
  46 canjes de misil y 15 lanzamientos. Los cinco clientes coincidieron en
  tablero, inventario de misiles, eventos y estado `Finalizado`.
- **Canjes, misiles y desconexión — clásico estricto, semilla 800:** el cliente
  2 se desconectó después del turno 5; los cuatro clientes restantes continuaron
  hasta la victoria con 35 países, 317 conquistas, 24 canjes normales, 66
  forzosos, 28 especiales, 53 canjes de misil y 22 lanzamientos.
- **Desconexión y reconexión autenticada — clásico estricto, tres clientes,
  semilla 123:** el cliente 1 se desconectó después del turno 2, recuperó su
  identidad y continuó la partida; hubo una reconexión, 67 conquistas y los
  tres clientes observaron `Finalizado`.
- **Revancha estricta — cinco clientes, objetivo 30, semilla 234:** se
  observaron objetivos privados sin filtrarlos al snapshot, 36 reclamos, 5
  canjes normales, 8 especiales, 55 canjes de misil y 10 lanzamientos. El
  cliente 2 se desconectó después del turno 5, recuperó su sesión y los cinco
  clientes terminaron sincronizados en `Finalizado`.

Los números son evidencia de esas corridas; no son una predicción para futuras
corridas con dados productivos.

## Límites

Se prueba el servidor productivo y sus mensajes, con bots que bufferizan
correctamente frames JSON terminados en NUL. **No se ejecutan el cliente Qt,
su transporte ni su interfaz gráfica**, por lo que esta simulación no demuestra
que un usuario pueda jugar la misma partida sin problemas de interfaz o red.

Las acciones se envían secuencialmente en conexiones locales. La fragmentación
del framing, los frames coalescidos, JSON inválido y las colas acotadas se
prueban en la suite TCP; `stress_slow_clients.py` agrega una prueba con un
cliente que deja de leer. Estos harnesses no simulan comandos simultáneos,
latencia WAN ni vencimiento del timer. Las opciones de desconexión y reconexión ejercitan el
cierre real de un socket, la continuidad de los clientes restantes y el
handshake autenticado de recuperación. Los objetivos secretos se verifican
cuando se solicita `--secret-objectives`. La estrategia utiliza colocación,
ataque, transferencia, tarjetas/canjes y misiles según el modo elegido; no
valida que esas reglas reproduzcan todo el reglamento del TEG clásico.
