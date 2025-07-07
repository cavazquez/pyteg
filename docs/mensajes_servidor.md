# Documentación de Mensajes del Servidor

Este documento describe todos los mensajes que el servidor puede enviar a los clientes durante una partida de TEG.

## Estructura General de los Mensajes

Todos los mensajes siguen un formato JSON con un campo `mensaje` que identifica el tipo de mensaje. Los demás campos varían según el tipo de mensaje.

## Índice de Mensajes

1. [Autenticación y Conexión](#autenticación-y-conexión)
   - [sosadmin](#sosadmin)
   - [color_asignado](#color_asignado)
   - [user_id](#user_id)
   - [username](#username)
   - [color](#color)

2. [Chat](#chat)
   - [chat](#chat-1)

3. [Estado del Juego](#estado-del-juego)
   - [estado](#estado)
   - [tiempo](#tiempo)
   - [turno](#turno)

4. [Jugadores](#jugadores)
   - [actualizar_lista_jugadores](#actualizar_lista_jugadores)

5. [Acciones de Juego](#acciones-de-juego)
   - [pais](#pais)
   - [agregar_unidad](#agregar_unidad)
   - [mover_unidad](#mover_unidad)
   - [unidades_disponibles](#unidades_disponibles)

---

## Autenticación y Conexión

### sosadmin
Informa al cliente que tiene privilegios de administrador.

**Formato JSON:**
```json
{
  "mensaje": "sosadmin"
}
```

**Cuándo se envía:**
- Cuando un cliente se conecta y es identificado como administrador.

---

### color_asignado
Informa al cliente su color asignado.

**Parámetros:**
- `id` (str): ID del usuario
- `r`, `g`, `b` (int): Componentes RGB del color asignado

**Formato JSON:**
```json
{
  "mensaje": "color_asignado",
  "id": "usuario123",
  "r": 255,
  "g": 0,
  "b": 0
}
```

---

### user_id
Envía al cliente su ID único de usuario.

**Parámetros:**
- `userid` (str): ID único del usuario

**Formato JSON:**
```json
{
  "mensaje": "user_id",
  "userid": "usuario123"
}
```

---

### username
Confirma el nombre de usuario establecido.

**Parámetros:**
- `userid` (str): ID del usuario
- `username` (str): Nombre de usuario confirmado

**Formato JSON:**
```json
{
  "mensaje": "username",
  "userid": "usuario123",
  "username": "Jugador1"
}
```

---

### color
Envía información de colores disponibles.

**Parámetros:**
- `r`, `g`, `b` (int): Componentes RGB del color

**Formato JSON:**
```json
{
  "mensaje": "color",
  "r": 255,
  "g": 0,
  "b": 0
}
```

---

## Chat

### chat
Envía un mensaje de chat a los jugadores.

**Parámetros:**
- `msg` (str): Contenido del mensaje
- `userid` (str, opcional): ID del remitente

**Formato JSON:**
```json
{
  "mensaje": "chat",
  "msg": "¡Hola a todos!",
  "userid": "usuario123"
}
```

---

## Estado del Juego

### estado
Informa sobre el estado actual del juego.

**Parámetros:**
- `estado` (str): Estado actual del juego

**Formato JSON:**
```json
{
  "mensaje": "estado",
  "estado": "esperando_jugadores"
}
```

**Posibles estados:**
- `esperando_jugadores`
- `iniciando`
- `en_curso`
- `finalizado`

---

### tiempo
Envía información sobre el tiempo restante del turno actual.

**Parámetros:**
- `userid_turno` (str): ID del usuario que tiene el turno actual
- `tiempo_restante` (int): Tiempo restante en segundos

**Formato JSON:**
```json
{
  "mensaje": "tiempo",
  "userid_turno": "usuario123",
  "tiempo_restante": 60
}
```

---

### turno
Informa sobre el turno y ronda actual.

**Parámetros:**
- `num_turno` (int): Número del turno actual
- `num_ronda` (int): Número de la ronda actual

**Formato JSON:**
```json
{
  "mensaje": "turno",
  "num_turno": 1,
  "num_ronda": 1
}
```

---

## Jugadores

### actualizar_lista_jugadores
Actualiza la lista de jugadores conectados.

**Parámetros:**
- `jugadores` (array): Lista de objetos con información de jugadores
  - `userid` (str): ID del jugador
  - `r`, `g`, `b` (int): Componentes RGB del color del jugador

**Formato JSON:**
```json
{
  "mensaje": "actualizar_lista_jugadores",
  "jugadores": [
    {
      "userid": "usuario123",
      "r": 255,
      "g": 0,
      "b": 0
    },
    {
      "userid": "usuario456",
      "r": 0,
      "g": 0,
      "b": 255
    }
  ]
}
```

---

## Acciones de Juego

### pais
Actualiza la información de un país.

**Parámetros:**
- `pais` (str): Nombre del país
- `userid` (str): ID del jugador que controla el país
- `unidades` (int): Cantidad de unidades en el país

**Formato JSON:**
```json
{
  "mensaje": "pais",
  "pais": "Argentina",
  "userid": "usuario123",
  "unidades": 5
}
```

---

### agregar_unidad
Informa sobre unidades agregadas a un país.

**Parámetros:**
- `pais` (str): Nombre del país
- `tipo_unidad` (str): Tipo de unidad agregada
- `cantidad` (int): Cantidad de unidades agregadas

**Formato JSON:**
```json
{
  "mensaje": "agregar_unidad",
  "pais": "Argentina",
  "tipo_unidad": "infanteria",
  "cantidad": 3
}
```

---

### mover_unidad
Informa sobre movimiento de unidades entre países.

**Parámetros:**
- `origen` (str): País de origen
- `destino` (str): País de destino
- `cantidad` (int): Cantidad de unidades movidas

**Formato JSON:**
```json
{
  "mensaje": "mover_unidad",
  "origen": "Argentina",
  "destino": "Brasil",
  "cantidad": 2
}
```

---

### unidades_disponibles
Indica las unidades disponibles para colocar.

**Parámetros:**
- `unidades` (object): Diccionario con el tipo de unidad y cantidad disponible

**Formato JSON:**
```json
{
  "mensaje": "unidades_disponibles",
  "unidades": {
    "infanteria": 5,
    "artilleria": 3,
    "caballeria": 2
  }
}
```

---

## Notas Adicionales

- Los mensajes se envían a través del `ServerTransmisor`.
- Cada mensaje se convierte a JSON antes de ser enviado.
- Los mensajes pueden incluir campos adicionales según sea necesario.
- Los clientes deben estar preparados para manejar mensajes inesperados o con campos faltantes.
