# Cartas de situaciones: contrato antes de implementar

Este documento cierra el análisis de la propuesta de cartas de situaciones sin
inventar una variante de reglas. El repositorio implementa cartas de país,
canjes, misiles y objetivos secretos; todavía no tiene un mazo de situaciones
ni una regla que explique cómo se roba, se juega o se resuelve una de esas
cartas.

La referencia pública de [TEGNet](https://www.tegnet.com.ar/es/reglamento.htm)
indica que su reglamento es prácticamente el del TEG de mesa, con diferencias
por el juego en red, pero la página no define un mazo de situaciones para este
proyecto. Hasta confirmar una edición concreta y su licencia, no se deben
copiar textos o ilustraciones de una baraja comercial.

## Decisión propuesta

La primera entrega debe ser un contrato de datos y una prueba de privacidad,
sin efectos de reglas. El mazo se mantiene separado de `cartas.toml` porque
las cartas de país participan en canjes y las situaciones podrían tener otro
ciclo de vida.

Una definición de tema tendría esta forma conceptual:

```toml
[[Situaciones]]
id = "situacion.ejemplo"
titulo = "Título traducible"
descripcion = "Texto aprobado por el proyecto"
visibilidad = "privada"
momento = "inicio_turno"
efecto = "sin_efecto"
parametros = {}
```

Los nombres son una propuesta, no un formato estable todavía. La revisión de
reglas debe decidir primero:

- si la carta se roba al comenzar el turno, al conquistar, al finalizar una
  ronda o por una acción voluntaria;
- si la ven todos los jugadores o sólo su dueño;
- si tiene un efecto inmediato, una respuesta de otro jugador, una duración o
  un descarte;
- si se puede conservar más de una, devolver al mazo, encadenar o jugar fuera
  de turno;
- qué ocurre con la carta cuando el jugador se desconecta, reconecta, es
  eliminado o inicia una revancha;
- qué edición/reglamento y qué licencia autorizan los textos y las imágenes.

## Contrato de red que se implementará cuando se cierre la regla

El servidor será la única autoridad. El diseño previsto separa tres tipos de
datos:

1. `situacion_activa`: evento público con `situation_id`, fase y jugador al
   que corresponde responder, si la variante lo requiere.
2. `carta_situacion`: evento privado con el contenido que sólo puede conocer
   el jugador autorizado. Nunca entra en el snapshot público.
3. `jugar_situacion` y, si hace falta, `descartar_situacion`: comandos con
   `command_id`, validados por fase, identidad, propiedad, expiración y
   parámetros del efecto.

Una reconexión debe recibir de nuevo la mano privada y la situación activa
vigente, sin reproducir eventos históricos. Los comandos repetidos con el
mismo `command_id` deben devolver el mismo `command_result` sin volver a
aplicar el efecto. Una revancha debe vaciar el mazo/las manos de la partida
anterior y crear una secuencia nueva.

## Criterios de aceptación de la futura implementación

- El tema que no declara situaciones sigue funcionando y conserva exactamente
  el comportamiento actual.
- Ningún snapshot, log público o cliente espectador revela una carta privada.
- Un cliente no puede robar, jugar, descartar ni resolver una carta fuera de
  la fase o del turno autorizados.
- El efecto se aplica una sola vez aunque se repita el comando o haya una
  reconexión en medio de la transición.
- La simulación multicliente cubre robo, juego, descarte, desconexión,
  reconexión, eliminación y revancha cuando la regla esté aprobada.
- Cada texto y recurso visual tiene origen y licencia documentados.

## Descomposición atómica

Cuando el usuario confirme una variante, conviene abrir estos cambios en
orden:

1. **Especificación de reglas y fuente**: cerrar momento, visibilidad, efectos
   y licencia con ejemplos de una partida.
2. **Modelo y carga de tema**: validar `Situaciones` y rechazar IDs,
   momentos o efectos desconocidos.
3. **Mazo privado y snapshots**: reparto, descarte, reconexión y revancha sin
   filtrar información.
4. **Comandos y eventos validados**: esquema de protocolo, autoridad del
   servidor e idempotencia.
5. **Primera carta sin efecto**: recorrido vertical para probar UI y transporte
   sin alterar las reglas de combate.
6. **Efectos individuales**: un issue por efecto, con tests de dominio,
   integración TCP y simulación.

No se implementa el punto 5 hasta que el punto 1 tenga una respuesta escrita:
una carta sin una regla de robo y de resolución sólo agrega estado que los
clientes no pueden interpretar de forma consistente.
