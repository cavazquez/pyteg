# Revisión de PyTeg y ruta para terminarlo

Fecha local: 21 de septiembre de 2026. Base revisada: `27b4c81`.

## Diagnóstico de la base revisada

La base revisada permite jugar por TCP hasta una victoria real, pero todavía no completa
correctamente el ciclo de partida. El trabajo más urgente está en la integridad
del protocolo, la exclusión mutua del estado y el cierre de la partida. El
empaquetado también impide distribuir la aplicación tal como está documentada.
La división actual en dominio, tareas, mensajes y gestores GUI es una base útil;
no hace falta reescribir todo el proyecto.

Se crearon **35 issues atómicos**, con evidencia, aceptación y
dependencias. No había issues abiertos al iniciar la revisión. Las prioridades
son relativas a entregar una partida local fiable; no representan una certificación
de seguridad ni compatibilidad completa con todas las reglas del TEG clásico.

## Estado tras implementar #163–#172

La capa TCP ahora reconstruye tramas UTF-8/NUL incrementales, valida el contrato
antes de construir tareas y libera socket, registro y color de forma idempotente.
Sólo el administrador puede configurar o iniciar la sala.

El servidor valida que quien mueve unidades sea el jugador activo. La cantidad
de movimiento debe ser un entero positivo, tanto en el contrato TCP como antes
de consultar o mutar el mapa; el origen conserva al menos una unidad.

Las acciones TCP validadas y los vencimientos se serializan en un único ejecutor.
El temporizador publica `TurnExpired` con una generación del turno, por lo que un
vencimiento obsoleto no puede avanzar dos veces ni intercalarse entre validar y
mutar una acción. Las salidas pasan por una cola FIFO de hasta 128 tramas por
conexión; un cliente lento agota su propia cola y se desconecta después del plazo
de envío, sin bloquear la transición del juego.

El cierre de victoria conserva `Finalizado`, detiene el temporizador y difunde el
estado antes de anunciar la victoria. Las acciones posteriores se rechazan y el
chat sigue disponible después de la partida.

Al perder el último país, un jugador se elimina una sola vez del orden de turnos,
de los refuerzos y de las acciones. Sus cartas asignadas se transfieren al
conquistador, sin volver al mazo, y todos los clientes reciben un aviso de sistema
junto con la lista activa actualizada. El último superviviente gana incluso si el
umbral de países configurado no se alcanza.

## Estado tras implementar #175, #177 y #183

La rotación conserva el orden de la ronda vigente y lo desplaza una posición en
cada ronda nueva. Las eliminaciones y desconexiones se quitan del turno
pendiente en cualquier posición; si se retira el último turno, la siguiente
ronda comienza inmediatamente sin repetir al jugador anterior.

Los bonus continentales se calculan contra la posesión actual del mapa y un
continente sin países no puede cumplir control total. La simulación cubre
conquistas, pérdidas y bajas mientras recalcula la ronda siguiente.

Cada cliente recibe un token privado al entrar. Si pierde el socket durante una
partida puede conectarse con un ID temporal, autenticarse con ese token y
recuperar su identidad, color, países, tarjetas y turno. La reconexión no crea
un jugador adicional ni consume un color nuevo.

## Estado tras implementar #189 y #190

El servidor exige que toda conexión negocie versión, tema y mapa antes de
aceptar comandos o iniciar la partida. Las tareas de juego no dependen de que
el cliente haya anunciado una fase: consultan una matriz única y rechazan el
comando antes de validar o modificar recursos si la fase no corresponde.

La política vigente es: `agregar_unidad`, `canjear_tarjetas` y `canje_especial`
durante `colocacion`; `atacar`, `mover_unidad`, `reclamar_tarjeta`,
`canjear_misil`, `lanzar_misil` y `finalizar_turno` durante `acciones`.
`solicitar_tarjetas` es una consulta sin fase. La simulación TCP cubre los
canjes y misiles respetando ese orden.

## Estado tras implementar #191

El snapshot público ahora tiene el esquema versionado `snapshot_version = 1`.
Incluye revisión, estado, tema y hash del mapa, configuración, jugadores con
color/administración/conexión/eliminación, países con misiles, fase, turno y
refuerzos pendientes. Las cartas y los objetivos secretos siguen viajando sólo
por sus mensajes privados.

Toda mutación aceptada desde el executor publica una sola revisión. Las
transiciones que ya publican internamente (inicio, victoria y revancha)
reutilizan esa revisión, mientras que un rechazo no cambia el snapshot. La
solicitud `solicitar_snapshot` devuelve al cliente un snapshot completo marcado
como `resync`, sin avanzar la revisión. El modelo independiente de Qt acepta
esa resincronización incluso cuando repite la revisión que había detectado
incompleta.

## Estado tras implementar #192

`ClientStateModel` ahora normaliza snapshots, mapa, jugadores, fase, turno,
misiles, configuración y resultados correlacionados. `QtClientStateAdapter`
proyecta ese estado hacia la GUI; los mensajes de cartas, objetivos y unidades
propias siguen una vía privada explícita. Snapshots y `command_result` ya no
caen en `ClientTaskNull` ni se ejecutan como acciones duplicadas.

El simulador utiliza el mismo codec NUL/UTF-8 incremental, validador de eventos
y modelo que el cliente Qt. Un hueco de revisión solicita `solicitar_snapshot`,
el snapshot de resincronización reemplaza el estado completo y los snapshots
viejos o duplicados no retroceden la revisión.

## Estado tras implementar #193

Toda mutación TCP exige un `command_id` no vacío antes de construir o ejecutar
su tarea. Las consultas de snapshot, tarjetas, chat y el handshake siguen siendo
mensajes no mutantes y conservan su contrato independiente.

El servidor guarda por sesión los últimos resultados junto con el payload sin
su identificador. Si una conexión reintenta el mismo ID y payload, reproduce el
resultado anterior sin repetir la tarea, la mutación ni la revisión. Si reutiliza
el ID con otro payload, devuelve `command_id_conflict` y conserva el estado. La
caché se transfiere al reemplazar una conexión durante una reconexión autenticada,
por lo que un cliente puede reintentar después de perder la respuesta TCP.

## Evidencia ejecutada

- Python 3.14.0 y el entorno PySide6 existente.
- **411 tests pasan** con `QT_QPA_PLATFORM=offscreen`; Ruff, formato y mypy también
  pasan (mypy verificó 231 archivos fuente).
- Regresiones de red cubren fragmentación y coalescencia TCP, JSON y payloads
  inválidos, ciclo de conexión/color, permisos de administrador, una carrera
  determinista acción/timeout, vencimientos obsoletos, cola de salida saturada,
  movimientos fuera de turno y cantidades inválidas.
- **Partida clásica por TCP**, servidor productivo en subprocess y seis bots:
  semilla 45, victoria a 30 países, 78 turnos y 224 conquistas en 32,825 segundos.
  Los seis clientes terminaron en `Finalizado`, coincidieron en el tablero y no
  recibieron errores.
- **Partida clásica estricta por TCP**, cinco bots con semilla 900 y victoria a
  30 países: 60 turnos y 182 conquistas en 24,328 segundos. La victoria fue
  observada y los cinco clientes terminaron en `Finalizado`.
- **Reconexión TCP autenticada**, cinco bots con canjes y misiles, semilla 800:
  un cliente recuperó identidad, tarjetas e inventario de misiles después de
  perder el socket; la partida alcanzó `Finalizado` en los cinco clientes.
- **Snapshot público versionado**, tres clientes recibieron el mismo estado
  inicial completo y uno se resincronizó con la misma revisión sin crear una
  mutación adicional.
- **Simulación actualizada**, cinco clientes con canjes y misiles alcanzaron
  `victory_verified` en 74 turnos, 125 conquistas y 10 lanzamientos de misil;
  los cinco finalizaron correctamente. Evidencia: `logs/simulations/classic-800`.
- **Bot con modelo compartido**, cinco clientes alcanzaron `victory_verified`
  en 98 turnos, 212 conquistas y 12 lanzamientos de misil; cuatro clientes
  completaron además una desconexión/reconexión autenticada. Evidencia:
  `logs/simulations/classic-192` y `logs/simulations/classic-193`.

Los JSON y trazas completos quedan en `logs/simulations/`, ignorados por Git.
Los comandos y límites están en [SIMULATION.md](SIMULATION.md).
No se probaron partidas completas de Qt, objetivos secretos ni red WAN. El
consenso del mapa comprueba replicación entre
clientes; no es un oráculo de todas las reglas.

## Fallos reproducidos que explican las prioridades

1. Resuelto por #163 y #164: un JSON fragmentado, UTF-8 partido o una raíz JSON
   inválida ya no se interpreta como un mensaje completo ni deja una conexión
   registrada al fallar la validación.
2. Resuelto por #166: altas y bajas repetidas liberan socket, registro y color;
   el noveno cliente puede entrar después de ocho desconexiones.
3. Resuelto por #165, #169 y #170: sólo el administrador puede configurar o
   iniciar; mover exige el turno activo y una cantidad entera positiva antes de
   alterar países.
4. Resuelto por #167: una intercalación entre agregar unidades y vencer el turno
   queda ordenada en el mismo ejecutor FIFO; una generación obsoleta no puede
   avanzar dos veces ni consumir el pool del jugador siguiente.
5. Resuelto por #171: la victoria congela estado, detiene el temporizador y
   cambia a `Estado.FINALIZADO` (valor wire `Finalizado`).
6. Resuelto por #172: un jugador sin países ya no recibe turnos ni refuerzos, no
   puede ejecutar acciones y sus cartas se transfieren una única vez al
   conquistador.
7. Se pueden reclamar dos cartas en un mismo turno.
8. Resuelto por #190: los comandos mutantes de cartas, misiles y turno pasan
   por una matriz de fases autoritativa y no dejan mutaciones parciales cuando
   se reciben fuera de fase.
9. El wheel ahora incluye mapas, iconos, idiomas y sonidos; el smoke test lo
   extrae fuera del checkout e inicia servidor y cliente Qt offscreen. Las
   entradas Nuitka y los cuatro artefactos del release se validan antes de
   compilar o publicar.

## Arquitectura de red recomendada

Mantener **TCP + JSON** inicialmente, con un codec compartido que acumule bytes
hasta el NUL, límites de tamaño y esquemas de mensajes validados en ejecución.
El cambio decisivo es dar a un único ejecutor la propiedad del estado del juego:

```text
QTcpSocket / bot → codec → contrato validado → cola de comandos
                                               ↑
                                       TurnExpired(turn_id)
                                               ↓
                                único ejecutor del dominio
                                               ↓
                              eventos + revisión del estado
                                               ↓
                              cola FIFO acotada por conexión
                                               ↓
                              modelo del cliente → señales Qt
```

Lectores y temporizadores no mutan el motor. Las transiciones producen eventos
y una revisión, y el envío ocurre fuera de la transición. Un cliente lento tiene
su propia política de cola/timeout. Snapshots completos de este tablero son una
opción simple; los deltas pueden esperar hasta que exista una medición que los
justifique. La corrida clásica recibió **22.900 mensajes `pais` por cliente**,
lo que da una referencia concreta para evaluar agregación y envíos redundantes.

Después se incorporan handshake de versión/mapa, snapshots atómicos, comandos
correlacionados y sesiones reanudables. Cartas y objetivos permanecen privados.
El modelo de cliente debería poder ejecutarse sin Qt y ser compartido por bots
y GUI para que el E2E no replique otra implementación del protocolo.

No condicionaría estas correcciones a cambiar de biblioteca. Para pocos jugadores
se pueden conservar lectores con hilos y centralizar comandos/escrituras.
`asyncio.start_server` y streams son una opción posterior para simplificar I/O,
sin cambiar dominio ni contratos. WebSocket/WSS es una alternativa si se decide
crear cliente web o despliegue web; no resuelve por sí solo las carreras ni las
reglas actuales. Para una primera entrega mantendría el alcance LAN documentado.

La necesidad de conservar fragmentos es parte del contrato de TCP, documentado
en el [Socket Programming HOWTO de Python](https://docs.python.org/3/howto/sockets.html).
Las opciones de control de flujo se describen en [asyncio streams](https://docs.python.org/3/library/asyncio-stream.html),
y el cliente actual puede conservar [QTcpSocket](https://doc.qt.io/qtforpython-6/PySide6/QtNetwork/QTcpSocket.html).
La elección de migrar gradualmente es una recomendación de esta revisión.

## Orden de implementación y definición de terminado

1. **Cerrar fallos de integridad:** framing, contratos, permisos, cleanup,
   movimientos válidos y finalización real. Cada regresión debe fallar en la base
   actual y pasar con su arreglo.
2. **Un solo dueño del juego:** cola de comandos/timers y salidas por conexión.
   Probar carreras con barreras, sin depender de sleeps probabilísticos.
3. **Completar reglas y lifecycle:** eliminaciones, rotación, cartas, continentes,
   refuerzos y fases. Documentar variantes de reglas; luego habilitar revancha.
4. **Estado de red recuperable:** handshake, snapshots, confirmaciones,
   reconexión y modelo compartido de cliente. Verificar privacidad y consenso.
5. **Entregar y mantener:** instalar wheel fuera del checkout, ejecutar binarios,
   verificar paquetes de release y poner E2E estricto en CI.

Una primera versión LAN terminada debería permitir iniciar, jugar hasta victoria,
cerrar sin acciones posteriores y comenzar otra partida, con varios clientes Qt
y sin perder mensajes ante fragmentación. El servidor debe ser la autoridad de
reglas y sus artefactos deben arrancar fuera del repositorio. Reconexión y otras
variantes avanzadas pueden quedar como segunda entrega explícita; no declararlas
soportadas antes de sus pruebas.

## Backlog publicado

### P0

- [x] [#191 — Completar el contrato público de snapshots versionados](https://github.com/cavazquez/pyteg/issues/191) (Red; implementado).
- [x] [#192 — Convertir `ClientStateModel` en la fuente única de GUI y bots](https://github.com/cavazquez/pyteg/issues/192) (Cliente; implementado).
- [x] [#193 — Exigir `command_id` y hacer idempotentes los reintentos](https://github.com/cavazquez/pyteg/issues/193) (Red; implementado).

### P1

- [x] [#163 — Reconstruir mensajes TCP fragmentados con un codec incremental compartido](https://github.com/cavazquez/pyteg/issues/163) (Red; implementado).
- [x] [#164 — Validar el contrato de mensajes entrantes antes de construir tareas](https://github.com/cavazquez/pyteg/issues/164) (Red; implementado).
- [x] [#165 — Exigir rol de administrador para configurar e iniciar la partida](https://github.com/cavazquez/pyteg/issues/165) (Sala; implementado).
- [x] [#166 — Liberar socket, registro y color de forma idempotente al desconectar](https://github.com/cavazquez/pyteg/issues/166) (Red; implementado).
- [x] [#167 — Serializar comandos de juego y vencimientos de turno en un único ejecutor](https://github.com/cavazquez/pyteg/issues/167) (Red; implementado).
- [x] [#168 — Enviar eventos por una cola FIFO acotada por conexión](https://github.com/cavazquez/pyteg/issues/168) (Red; implementado).
- [x] [#169 — Rechazar movimientos fuera del turno del jugador](https://github.com/cavazquez/pyteg/issues/169) (Reglas; implementado).
- [x] [#170 — Impedir cantidades no positivas o no enteras al mover unidades](https://github.com/cavazquez/pyteg/issues/170) (Reglas; implementado).
- [x] [#171 — Pasar a FINALIZADO y detener el juego al declarar victoria](https://github.com/cavazquez/pyteg/issues/171) (Partida; implementado).
- [x] [#172 — Excluir jugadores sin territorios de los turnos y refuerzos](https://github.com/cavazquez/pyteg/issues/172) (Partida; implementado).
- [x] [#173 — Empaquetar recursos y cargar el wheel fuera del checkout](https://github.com/cavazquez/pyteg/issues/173) (Entrega; implementado).
- [x] [#174 — Actualizar las entradas de Nuitka a los módulos existentes](https://github.com/cavazquez/pyteg/issues/174) (Entrega; implementado).

### P2

- [x] [#175 — Conservar la rotación acumulativa del orden entre rondas](https://github.com/cavazquez/pyteg/issues/175) (Reglas; implementado).
- [x] [#176 — Limitar la recompensa de conquista a una tarjeta por turno](https://github.com/cavazquez/pyteg/issues/176) (Reglas; implementado).
- [x] [#177 — Evitar bonificaciones por continentes ausentes del mapa](https://github.com/cavazquez/pyteg/issues/177) (Reglas; implementado).
- [x] [#178 — Calcular los refuerzos con el mapa vigente al iniciar cada turno](https://github.com/cavazquez/pyteg/issues/178) (Reglas; implementado).
- [x] [#179 — Validar en el servidor las fases de colocación, ataque y movimiento](https://github.com/cavazquez/pyteg/issues/179) (Reglas; implementado).
- [x] [#180 — Reasignar administrador cuando abandona la sala](https://github.com/cavazquez/pyteg/issues/180) (Sala; implementado).
- [x] [#181 — Negociar versión de protocolo y mapa antes de entrar a la sala](https://github.com/cavazquez/pyteg/issues/181) (Red; implementado).
- [x] [#182 — Publicar snapshots atómicos con revisión y cambios coherentes](https://github.com/cavazquez/pyteg/issues/182) (Red; implementado).
- [x] [#183 — Recuperar una sesión de jugador después de perder la conexión](https://github.com/cavazquez/pyteg/issues/183) (Red; implementado).
- [x] [#184 — Separar estado y procesamiento de eventos del cliente de QWidget](https://github.com/cavazquez/pyteg/issues/184) (Cliente; implementado).
- [x] [#185 — Adjuntar al release los archivos realmente generados por la matriz](https://github.com/cavazquez/pyteg/issues/185) (Entrega; implementado).
- [x] [#186 — Ejecutar una partida multicliente hasta el estado final en CI](https://github.com/cavazquez/pyteg/issues/186) (Pruebas; implementado).
- [x] [#187 — Volver al lobby e iniciar una revancha sin reiniciar el servidor](https://github.com/cavazquez/pyteg/issues/187) (Partida; implementado).
- [x] [#188 — Correlacionar comandos y evitar ejecución duplicada al reintentar](https://github.com/cavazquez/pyteg/issues/188) (Red; implementado).
- [x] [#189 — Exigir handshake antes de aceptar comandos o iniciar la partida](https://github.com/cavazquez/pyteg/issues/189) (Red; implementado).
- [x] [#190 — Hacer obligatoria la matriz de fases para todas las acciones TCP](https://github.com/cavazquez/pyteg/issues/190) (Reglas; implementado).

### P1 siguiente

- [x] [#194 — Usar un identificador de turno inmutable para la recompensa de conquista](https://github.com/cavazquez/pyteg/issues/194) (Reglas; implementado).
- [x] [#195 — Mantener la sucesión de administrador tras desconexión o eliminación](https://github.com/cavazquez/pyteg/issues/195) (Sala; implementado).
- [x] [#196 — Reiniciar una revancha sin heredar estado de la partida anterior](https://github.com/cavazquez/pyteg/issues/196) (Partida; implementado).
- [ ] [#197 — Completar CI con fragmentación, resincronización y smoke Qt](https://github.com/cavazquez/pyteg/issues/197) (Pruebas; pendiente).

## Cambios dejados en este trabajo

- `scripts/simulate_game.py`: harness local acotado con evidencia y cleanup.
- `docs/SIMULATION.md`: uso, resultados y límites.
- Este informe y enlaces a los issues.
- Cierre de victoria en servidor, temporizador y GUI, con regresiones unitarias
  e integración TCP para #171.
- Ejecutor FIFO único para comandos y vencimientos, con generación de turno y
  regresiones deterministas para #167.
- Escritor FIFO acotado por conexión, plazo de envío y desconexión del cliente
  lento, con regresiones de orden y saturación para #168.
- Validación de turno activo y cantidad positiva en movimientos, con regresiones
  de tarea, contrato y TCP para #169 y #170.
- Eliminación idempotente con transferencia de cartas al conquistador, exclusión
  de turnos y acciones, actualización de la lista activa y victoria del último
  superviviente para #172.
- Rotación acumulativa, bonus continentales contra el mapa vigente y
  reconexión autenticada con sincronización de sesión para #175, #177 y #183.
- Recompensa de una tarjeta por turno y refuerzos calculados al entrar al turno,
  con fase de colocación autoritativa en el servidor para #176, #178 y #179.
- Sucesión determinista del administrador y limpieza completa para revancha sin
  reiniciar el proceso para #180 y #187.
- Handshake de protocolo/tema/mapa, snapshots públicos versionados y resultados
  idempotentes de comandos, con modelo de estado Qt-independiente para #181,
  #182, #184, #188 y #189.
- Matriz única de fases para colocación, acciones, canjes, reclamos y misiles,
  con rechazos antes de mutar el estado para #190.
- Contrato completo de snapshots públicos, publicación de revisión única y
  resincronización explícita para #191.
- Modelo compartido para eventos públicos y datos privados, adaptador Qt y bot
  headless con el mismo codec/validador para #192.
- Simulación TCP multicliente estricta en CI, incluyendo canjes, misiles,
  desconexión, reconexión y artefactos de evidencia para #186.
