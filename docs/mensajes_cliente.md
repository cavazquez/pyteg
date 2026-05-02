# Documentación de Mensajes del Cliente

Este documento describe todos los mensajes que el cliente puede enviar al servidor durante una partida de TEG.

Los mensajes entrantes (servidor→cliente), incluyendo campos como `userid` / `user_id` / `jugador_actual_id`, están documentados en `docs/mensajes_servidor.md`. La identidad canónica en wire format es **`userid` numérico (JSON number)**; ver `docs/DECISIONS.md` (ADR-012).

## Estructura General de los Mensajes

Todos los mensajes siguen un formato JSON con un campo `mensaje` que identifica el tipo de mensaje. Los demás campos varían según el tipo de mensaje.

## Índice de Mensajes

1. [Conexión y Autenticación](#conexión-y-autenticación)
   - [set_username](#set_username)
   - [seleccionar_color](#seleccionar_color)

2. [Chat](#chat)
   - [chat](#chat-1)

3. [Gestión de Partida](#gestión-de-partida)
   - [empezar](#empezar)
   - [empezar_partida](#empezar_partida)
   - [finalizar_turno](#finalizar_turno)

4. [Acciones de Juego](#acciones-de-juego)
   - [agregar_unidad](#agregar_unidad)
   - [mover_unidad](#mover_unidad)

---

## Conexión y Autenticación

### set_username
Establece el nombre de usuario del jugador.

**Parámetros:**
- `username` (str): Nombre de usuario elegido

**Formato JSON:**
```json
{
  "mensaje": "set_username",
  "username": "nombre_de_usuario"
}
```

**Ejemplo:**
```python
msg = MsgSetUsername("jugador1")
```

**Respuesta del servidor:**
- Éxito: `{"status": "ok"}`
- Error: `{"status": "error", "error": "Mensaje de error"}`

### seleccionar_color
Selecciona el color del jugador.

**Parámetros:**
- `color` (str): Nombre del color seleccionado

**Formato JSON:**
```json
{
  "mensaje": "seleccionar_color",
  "color": "nombre_del_color"
}
```

**Ejemplo:**
```python
msg = MsgSeleccionarColor(color_object)
```

---

## Chat

### chat
Envía un mensaje de chat a todos los jugadores.

**Parámetros:**
- `msg` (str): Contenido del mensaje

**Formato JSON:**
```json
{
  "mensaje": "chat",
  "msg": "¡Hola a todos!"
}
```

**Ejemplo:**
```python
msg = MsgChat("¡Hola a todos!")
```

---

## Gestión de Partida

### empezar
Solicita al servidor que inicie la partida. Solo disponible para el administrador.

**Formato JSON:**
```json
{
  "mensaje": "empezar"
}
```

**Ejemplo:**
```python
msg = MsgEmpezar()
```

### empezar_partida
Indica que el jugador está listo para comenzar la partida.

**Formato JSON:**
```json
{
  "mensaje": "empezar_partida"
}
```

**Ejemplo:**
```python
msg = MsgEmpezarPartida()
```

### finalizar_turno
Finaliza el turno actual del jugador.

**Formato JSON:**
```json
{
  "mensaje": "finalizar_turno"
}
```

**Ejemplo:**
```python
msg = MsgFinalizarTurno()
```

---

## Acciones de Juego

### agregar_unidad
Agrega unidades a un país específico.

**Parámetros:**
- `pais` (str): Nombre del país
- `tipo_unidad` (str): Tipo de unidad a agregar
- `cantidad` (int, opcional): Cantidad de unidades (default: 1)

**Formato JSON:**
```json
{
  "mensaje": "agregar_unidad",
  "pais": "Argentina",
  "tipo_unidad": "infanteria",
  "cantidad": 3
}
```

**Ejemplo:**
```python
msg = MsgAgregarUnidad("Argentina", "infanteria", 3)
```

### mover_unidad
Mueve unidades entre países.

**Parámetros:**
- `origen` (str): País de origen
- `destino` (str): País de destino
- `cantidad` (int, opcional): Cantidad de unidades a mover (default: 1)

**Formato JSON:**
```json
{
  "mensaje": "mover_unidad",
  "origen": "Argentina",
  "destino": "Brasil",
  "cantidad": 2
}
```

**Ejemplo:**
```python
msg = MsgMoverUnidad("Argentina", "Brasil", 2)
```
---

## Notas Adicionales

- Los mensajes se envían a través del `ClientTransmisor`.
- Cada mensaje se convierte a JSON antes de ser enviado.
- El servidor responde con un estado y, en caso de error, incluye un mensaje descriptivo.
