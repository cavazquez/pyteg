# Arquitectura de Pyteg

Este documento describe la arquitectura de alto nivel del proyecto, el flujo cliente-servidor, el sistema de mensajes y los estados relevantes de la GUI.

## Visión general
Pyteg implementa el juego TEG en un modelo cliente-servidor:
- Servidor: valida reglas del juego, procesa acciones (agregar unidades, atacar, mover, finalizar turno), mantiene el estado y difunde actualizaciones.
- Cliente: UI con PySide6, conecta al servidor, envía acciones y procesa mensajes para reflejar el estado (mapa, chat, barra de estado, diálogos).

## Módulos principales (src/)
- server.py: servidor y loop principal (acepta conexiones, dirige mensajes a tareas).
- server_tasks.py: tareas validadas del servidor (AgregarUnidad, Atacar, MoverUnidad, FinalizarTurno, etc.).
- server_game.py: reglas del juego, batallas y cálculo de conquistas.
- server_mapa.py: representación del mapa, países y propietarios.
- server_transmisor.py: envío tipificado de mensajes a clientes.
- server_msg.py: definición de mensajes (chat, mapa, turnos, resultados de batalla, etc.).
- client_connection.py: manejo de conexión y estado conectado/desconectado.
- client_tasks.py: procesamiento de mensajes en el cliente y actualización de UI.
- gui.py y gui_*: ventanas, diálogos y toolbar.
- run_client.py: punto de entrada del cliente.

## Flujo de mensajes
1) Cliente realiza acción (UI) -> client_transmisor envía mensaje al servidor.
2) server.py enruta -> ServerTask correspondiente valida precondiciones.
3) Si es válido, aplica cambios en server_game / server_mapa.
4) El servidor emite mensajes de resultado/estado a clientes mediante server_transmisor.
5) client_tasks procesa y actualiza GUI.

### Diagrama de flujo
Para una vista visual del intercambio de mensajes, ver el diagrama de secuencia en:
- `docs/diagrams/message_flow.md`

## Mensajería clave
- MsgChat (tipos: normal, error, system). Los errores de validación se publican en chat con formato y color.
- MsgResultadoBatalla: detalla dados, pérdidas y si hubo conquista. Enviado a todos tras cada ataque.
- Turno/Unidades: al inicio de cada turno, el servidor envía el turno actual y, además, las unidades disponibles al jugador activo; tras agregar unidades, vuelve a enviar unidades disponibles.
- Actualización de mapa: se emite después de acciones que modifican el estado (agregar, mover, atacar, conquista).

## Reglas e invariantes
- Turnos: solo el jugador del turno puede realizar acciones. Validado en todas las tareas relevantes.
- Ataques: restringidos en los dos primeros turnos; requieren países adyacentes, dueño válido y unidades suficientes; el atacante puede lanzar 1 a 3 dados según unidades.
- Movimiento: requiere adyacencia y unidades disponibles (no vaciar país origen si la regla lo impide).
- Chat de errores: toda acción inválida genera un mensaje de error visible para el jugador con formato ⚠️ rojo.

## Estados de la GUI
- Toolbar (gui_toolbar.py):
  - Botón Conectar habilitado cuando no hay conexión; al conectar se deshabilita.
  - Botones Atacar y Mover habilitados solo cuando hay 2 países seleccionados y hay conexión.
  - Botón Finalizar Turno permanece siempre habilitado.
- Selección de países (gui_scene.py): gestiona origen/destino y notifica a la toolbar para habilitar/deshabilitar acciones.
- Chat (gui_chat.py): muestra mensajes tipificados con color asignado a usuarios y formato consistente.
- AttackDialog (gui_attack_dialog.py): tamaño 400x280 para mejor visualización.

## Logging y depuración
- Logging detallado en batallas: estado antes/después, dados, pérdidas, conquista.
- Logs del servidor y cliente configurables vía logging.conf.

## Pruebas y calidad
- 120+ tests en tests/.
- run_test.sh ejecuta: ruff check, ruff format, coverage, y mypy (enfoque en aridad de llamadas).

## Extensión del protocolo
Guías en docs/ sobre cómo crear mensajes cliente-servidor y bidireccionales. Ver:
- docs/como_crear_mensaje_cliente_a_servidor.md
- docs/como_crear_mensaje_servidor_a_cliente.md
- docs/como_crear_mensaje_bidireccional.md
