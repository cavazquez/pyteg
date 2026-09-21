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

## Qué se comprueba

Después de cada acción, los bots esperan un eco de chat que sirve como barrera:
el protocolo todavía no tiene identificadores de comando ni confirmaciones.
Después de esa barrera, todos deben observar el mismo tablero, con propietarios
válidos, todos los países presentes y al menos una unidad por país.

Para aceptar la victoria, todos los clientes deben recibir el mismo ganador,
ese jugador debe controlar el objetivo configurado y debe haber ocurrido al
menos una conquista. No alcanza con elegir un umbral que ya se cumple al repartir.

Cada ejecución guarda:

- `result.json`: ganador observado por cliente, estado de sala, cantidad de
  turnos/acciones, tablero final, hash del tablero, errores y alcance de la prueba.
- `wire.jsonl`: todos los mensajes enviados y recibidos, con cliente y tiempo.
- `server.log`: salida del proceso servidor.

Los registros están bajo `logs/`, que el repositorio ignora en Git.

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
la victoria pero el modo estricto no observó `Finalizado` en todos los clientes.

## Semilla y reproducibilidad

Por defecto se conserva la fuente de dados productiva, `secrets.randbelow`.
`--seed` fija la aleatoriedad del reparto; la estrategia de los bots es estable,
pero **la semilla sola no reproduce los dados ni garantiza el mismo ganador**.
Los colores también siguen usando su fuente productiva.

`--deterministic-dice` sustituye solamente `secrets.randbelow` por una fuente
semillada en el proceso hijo del harness. No modifica archivos del servidor,
reglas, propiedad de países ni unidades. Este modo facilita repetir una
secuencia de juego en el mismo entorno, pero es instrumentación de prueba y
figura explícitamente en el reporte. No garantiza identidad byte a byte de la
traza: colores, timestamps y mensajes del timer pueden variar.

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

Los números son evidencia de esas corridas; no son una predicción para futuras
corridas con dados productivos.

## Límites

Se prueba el servidor productivo y sus mensajes, con bots que bufferizan
correctamente frames JSON terminados en NUL. **No se ejecutan el cliente Qt,
su transporte ni su interfaz gráfica**, por lo que esta simulación no demuestra
que un usuario pueda jugar la misma partida sin problemas de interfaz o red.

Las acciones se envían secuencialmente en conexiones locales. No se simulan
fragmentación adversaria, pérdida de conexión, reconexión, clientes lentos,
comandos simultáneos, latencia WAN ni vencimiento del timer. Tampoco se ejercitan
objetivos secretos, tarjetas/canjes ni misiles. La estrategia utiliza colocación,
ataque y transferencia posteriores a una conquista según la API existente;
no valida que esas reglas reproduzcan todo el reglamento del TEG clásico.
