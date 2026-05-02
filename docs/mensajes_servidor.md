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
   - [resultado_batalla](#resultado_batalla)
   - [victoria](#victoria)
   - [resultado_misil](#resultado_misil)
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
- `id` (int): `userid` del usuario
- `r`, `g`, `b` (int): Componentes RGB del color asignado

**Formato JSON:**
```json
{
  "mensaje": "color_asignado",
  "id": 7,
  "r": 255,
  "g": 0,
  "b": 0
}
```

---

### user_id
Envía al cliente su ID único de usuario.

**Parámetros:**
- `user_id` (int): ID único del usuario (`userid`)

**Formato JSON:**
```json
{
  "mensaje": "user_id",
  "user_id": 7
}
```

---

### username
Confirma el nombre de usuario establecido.

**Parámetros:**
- `user_id` (int): `userid` del usuario
- `username` (str): Nombre de usuario confirmado

**Formato JSON:**
```json
{
  "mensaje": "username",
  "user_id": 7,
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
- `msg_type` (str): `normal` \| `error` \| `system`

**Formato JSON:**
```json
{
  "mensaje": "chat",
  "msg": "¡Hola a todos!",
  "msg_type": "normal"
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
- `user_id` (int): `userid` del jugador en turno
- `tiempo` (int): Tiempo restante en segundos

**Formato JSON:**
```json
{
  "mensaje": "tiempo",
  "user_id": 7,
  "tiempo": 60
}
```

---

### turno
Informa sobre el turno y ronda actual.

**Parámetros:**
- `num_turno` (int): Número del turno actual
- `num_ronda` (int): Número de la ronda actual
- `jugador_actual_id` (int, opcional): `userid` del jugador en turno
- `jugador_actual_nombre` (str, opcional): nombre para UI
- `jugador_actual_color` (str, opcional): color para UI

**Formato JSON:**
```json
{
  "mensaje": "turno",
  "num_turno": 1,
  "num_ronda": 1,
  "jugador_actual_id": 7,
  "jugador_actual_nombre": "Jugador1",
  "jugador_actual_color": "#ff0000"
}
```

---

## Jugadores

### actualizar_lista_jugadores
Actualiza la lista de jugadores conectados.

**Parámetros:**
- `jugadores` (array): Lista de objetos con información de jugadores
  - `userid` (int): `userid` del jugador
  - `color` (object): `{ "r": int, "g": int, "b": int }`

**Formato JSON:**
```json
{
  "mensaje": "actualizar_lista_jugadores",
  "jugadores": [
    {
      "userid": 7,
      "color": { "r": 255, "g": 0, "b": 0 }
    },
    {
      "userid": 8,
      "color": { "r": 0, "g": 0, "b": 255 }
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
- `userid` (int \| null): `userid` del jugador que controla el país; `null` si no hay dueño
- `unidades` (int): Cantidad de unidades en el país

**Formato JSON:**
```json
{
  "mensaje": "pais",
  "pais": "Argentina",
  "userid": 7,
  "unidades": 5
}
```

---

### resultado_batalla
Publica el resultado de un ataque (dados, bajas, conquista).

**Parámetros (entre otros):**
- `origen` / `destino` (str): países
- `atacante_id` / `defensor_id` (int \| null): `userid` de cada bando
- `atacante` / `defensor` (str): nombres para UI/chat
- `dados_atacante` / `dados_defensor` (array): dados
- `resultado` (object): pérdidas por país
- `conquistado` (bool)

**Formato JSON (ejemplo):**
```json
{
  "mensaje": "resultado_batalla",
  "origen": "Argentina",
  "destino": "Brasil",
  "atacante_id": 7,
  "defensor_id": 8,
  "atacante": "Ana",
  "defensor": "Luis",
  "dados_atacante": [6, 5],
  "dados_defensor": [4],
  "resultado": { "restar": ["Brasil"] },
  "conquistado": true
}
```

---

### victoria
Notifica el fin de partida con un ganador.

**Parámetros:**
- `ganador_id` (int): `userid` del ganador
- `ganador_nombre` (str): nombre para UI/chat

**Formato JSON:**
```json
{
  "mensaje": "victoria",
  "ganador_id": 7,
  "ganador_nombre": "Ana"
}
```

---

### resultado_misil
Notifica el resultado de un lanzamiento de misil.

**Parámetros (entre otros):**
- `jugador_id` (int): `userid` de quien lanzó
- `jugador` (str, opcional): nombre para UI/chat
- `pais_origen` / `pais_destino` (str)
- `distancia` / `dano` / `unidades_restantes` (int)

**Formato JSON (ejemplo):**
```json
{
  "mensaje": "resultado_misil",
  "jugador_id": 7,
  "jugador": "Ana",
  "pais_origen": "Argentina",
  "pais_destino": "Brasil",
  "distancia": 2,
  "dano": 1,
  "unidades_restantes": 3
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
