# Revisión de PyTeg y ruta para terminarlo

Fecha local: 20 de septiembre de 2026. Base revisada: `56b3ced991f14c6a0f4974b0b95494008e3c1c3b`.

## Diagnóstico de la base revisada

La base revisada permite jugar por TCP hasta una victoria real, pero todavía no completa
correctamente el ciclo de partida. El trabajo más urgente está en la integridad
del protocolo, la exclusión mutua del estado y el cierre de la partida. El
empaquetado también impide distribuir la aplicación tal como está documentada.
La división actual en dominio, tareas, mensajes y gestores GUI es una base útil;
no hace falta reescribir todo el proyecto.

Se crearon **26 issues atómicos: 12 P1 y 14 P2**, con evidencia, aceptación y
dependencias. No había issues abiertos al iniciar la revisión. Las prioridades
son relativas a entregar una partida local fiable; no representan una certificación
de seguridad ni compatibilidad completa con todas las reglas del TEG clásico.

## Estado tras implementar #171

El cierre de victoria ya está implementado localmente: al detectar un ganador el
servidor pasa una sola vez a `Finalizado`, detiene el temporizador y difunde el
estado antes de anunciar la victoria. Los envíos de turno y refuerzos se cortan,
las acciones de juego posteriores se rechazan y el cliente limpia el temporizador,
anula la selección y deshabilita atacar, mover y finalizar turno. El chat queda
disponible después de la partida.

La verificación añadió pruebas unitarias, GUI e integración TCP. La corrida
estricta de seis clientes clásico con semilla 45 alcanzó victoria tras 108 turnos
y 322 conquistas; los seis clientes terminaron en `Finalizado`, coincidieron en
el tablero y no recibieron errores.

## Evidencia ejecutada

- Python 3.14.0 y PySide6 6.11.1 del entorno existente.
- **332 tests pasan** con `QT_QPA_PLATFORM=offscreen`. Aparecen `ResourceWarning`
  por sockets sin cerrar, relacionados con el issue de limpieza.
- Ruff, formato y mypy pasan en la base revisada. La cobertura total con ramas
  habilitadas es **56%**; esa cifra no sustituye pruebas de partida completa.
- **Tres clientes Qt reales en modo offscreen** conectaron al servidor, recibieron
  el mapa clásico de 50 países, mostraron estado En Juego y el mismo jugador activo.
  No hubo excepciones Qt ni diálogos de error. Este smoke sólo cubrió inicio,
  no una partida completa por la interfaz ni validación visual.
- **Partida clásica por TCP**, servidor productivo en subprocess y tres bots:
  30 turnos, 223 ataques, 133 conquistas, 17,493 segundos. Ganó Bot_1 con 31 países;
  Bot_2 terminó con 11 y Bot_3 con 8. Los tres observaron el mismo mapa y ganador,
  sin mensajes de error. Se conservaron los dados productivos con `secrets`.
- **Partida reducida**, dos bots y objetivo de dos países: victoria tras seis
  turnos y nueve ataques. El mapa `test` actual tiene dos países, no seis.
- Ambos escenarios de la base conservaron **`JUGANDO` después de la victoria**.
  El modo `--require-finalized` detecta el problema y devuelve código 2.
- Dos corridas con dados instrumentados y semilla 7 produjeron el mismo tablero,
  hash y comandos. Un timeout forzado devuelve 1 y verifica cleanup del proceso.
- Se reconstruyó independientemente la traza clásica para corroborar mapa,
  ganador, ataques y conquistas publicados por el harness.

Los JSON y trazas completos quedan en `logs/simulations/`, ignorados por Git.
Los comandos y límites están en [SIMULATION.md](SIMULATION.md).
No se probaron partidas completas de Qt, tarjetas/canjes, objetivos secretos,
misiles, desconexiones, concurrencia adversaria ni red WAN. El consenso del mapa
comprueba replicación entre clientes; no es un oráculo de todas las reglas.

## Fallos reproducidos que explican las prioridades

1. Un JSON fragmentado entre dos lecturas se pierde. UTF-8 partido puede lanzar
   `UnicodeDecodeError`; una raíz JSON `[]` termina el handler y deja la conexión
   registrada. Cada lectura TCP se está tratando como un mensaje completo.
2. Después de ocho altas/bajas quedan cero clientes y cero colores disponibles;
   la novena alta falla. Falta limpieza de sockets, registro y colores.
3. Un usuario no administrador puede configurar/iniciar. Un jugador puede mover
   fuera de turno. Mover `-5` unidades transforma dos países con `2/2` en `7/-3`.
4. Una intercalación controlada entre agregar unidades y vencer el turno aplica
   una acción del jugador anterior consumiendo el pool del siguiente jugador.
5. La base sólo emitía la victoria: no congelaba estado, no detenía el timer y
   no cambiaba a `Estado.FINALIZADO` (valor wire `Finalizado`). Resuelto
   localmente por #171.
6. Los eliminados siguen recibiendo turnos/refuerzos. El orden deja de rotar
   después de la segunda ronda. Se pueden reclamar dos cartas en un mismo turno.
7. Continentes vacíos dan bonus; los refuerzos se calculan antes del turno real.
   Las fases restringidas por la GUI no tienen las mismas garantías en servidor.
8. El wheel generado contiene 222 entradas sin mapas, iconos, idiomas ni sonidos.
   Extraído fuera del checkout falla al cargar el tema. Nuitka referencia dos
   módulos inexistentes y el release busca directorios distintos de los subidos.

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

### P1

- [#163 — Reconstruir mensajes TCP fragmentados con un codec incremental compartido](https://github.com/cavazquez/pyteg/issues/163) (Red).
- [#164 — Validar el contrato de mensajes entrantes antes de construir tareas](https://github.com/cavazquez/pyteg/issues/164) (Red).
- [#165 — Exigir rol de administrador para configurar e iniciar la partida](https://github.com/cavazquez/pyteg/issues/165) (Sala).
- [#166 — Liberar socket, registro y color de forma idempotente al desconectar](https://github.com/cavazquez/pyteg/issues/166) (Red).
- [#167 — Serializar comandos de juego y vencimientos de turno en un único ejecutor](https://github.com/cavazquez/pyteg/issues/167) (Red).
- [#168 — Enviar eventos por una cola FIFO acotada por conexión](https://github.com/cavazquez/pyteg/issues/168) (Red).
- [#169 — Rechazar movimientos fuera del turno del jugador](https://github.com/cavazquez/pyteg/issues/169) (Reglas).
- [#170 — Impedir cantidades no positivas o no enteras al mover unidades](https://github.com/cavazquez/pyteg/issues/170) (Reglas).
- [x] [#171 — Pasar a FINALIZADO y detener el juego al declarar victoria](https://github.com/cavazquez/pyteg/issues/171) (Partida; implementado localmente).
- [#172 — Excluir jugadores sin territorios de los turnos y refuerzos](https://github.com/cavazquez/pyteg/issues/172) (Partida).
- [#173 — Empaquetar recursos y cargar el wheel fuera del checkout](https://github.com/cavazquez/pyteg/issues/173) (Entrega).
- [#174 — Actualizar las entradas de Nuitka a los módulos existentes](https://github.com/cavazquez/pyteg/issues/174) (Entrega).

### P2

- [#175 — Conservar la rotación acumulativa del orden entre rondas](https://github.com/cavazquez/pyteg/issues/175) (Reglas).
- [#176 — Limitar la recompensa de conquista a una tarjeta por turno](https://github.com/cavazquez/pyteg/issues/176) (Reglas).
- [#177 — Evitar bonificaciones por continentes ausentes del mapa](https://github.com/cavazquez/pyteg/issues/177) (Reglas).
- [#178 — Calcular los refuerzos con el mapa vigente al iniciar cada turno](https://github.com/cavazquez/pyteg/issues/178) (Reglas).
- [#179 — Validar en el servidor las fases de colocación, ataque y movimiento](https://github.com/cavazquez/pyteg/issues/179) (Reglas).
- [#180 — Reasignar administrador cuando abandona la sala](https://github.com/cavazquez/pyteg/issues/180) (Sala).
- [#181 — Negociar versión de protocolo y mapa antes de entrar a la sala](https://github.com/cavazquez/pyteg/issues/181) (Red).
- [#182 — Publicar snapshots atómicos con revisión y cambios coherentes](https://github.com/cavazquez/pyteg/issues/182) (Red).
- [#183 — Recuperar una sesión de jugador después de perder la conexión](https://github.com/cavazquez/pyteg/issues/183) (Red).
- [#184 — Separar estado y procesamiento de eventos del cliente de QWidget](https://github.com/cavazquez/pyteg/issues/184) (Cliente).
- [#185 — Adjuntar al release los archivos realmente generados por la matriz](https://github.com/cavazquez/pyteg/issues/185) (Entrega).
- [#186 — Ejecutar una partida multicliente hasta el estado final en CI](https://github.com/cavazquez/pyteg/issues/186) (Pruebas).
- [#187 — Volver al lobby e iniciar una revancha sin reiniciar el servidor](https://github.com/cavazquez/pyteg/issues/187) (Partida).
- [#188 — Correlacionar comandos y evitar ejecución duplicada al reintentar](https://github.com/cavazquez/pyteg/issues/188) (Red).

## Cambios dejados en este trabajo

- `scripts/simulate_game.py`: harness local acotado con evidencia y cleanup.
- `docs/SIMULATION.md`: uso, resultados y límites.
- Este informe y enlaces a los issues.
- Cierre de victoria en servidor, temporizador y GUI, con regresiones unitarias
  e integración TCP para #171.
