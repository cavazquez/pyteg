# Instrucciones para implementar un nuevo mensaje del servidor al cliente

## 1. Crear la clase del mensaje
Crear una nueva clase que herede de IMsg en el archivo `/src/server_msg.py`:

```python
class MsgMiNuevoMensaje(IMsg):
    def __init__(self, datos):
        self._tipo = "mi_nuevo_mensaje"
        self._datos = datos

    def to_json(self):
        data = {
            "mensaje": self._tipo,
            "datos": self._datos
        }
        return json.dumps(data)
```

## 2. Agregar el método en ServerTransmisor
Añadir el método en la clase ServerTransmisor en el archivo `/src/server_transmisor.py`:

```python
def enviar_mi_mensaje(self, datos):
    msg = MsgMiNuevoMensaje(datos)
    self._send_message(msg)
```

## 3. Usar el mensaje
Para enviar el mensaje desde cualquier parte del servidor:

```python
client.transmisor.enviar_mi_mensaje(datos)
```

## Notas importantes
- No es necesario crear un ServerTask para mensajes que van del servidor al cliente
- El cliente recibirá automáticamente el mensaje y lo procesará a través de su sistema de tareas
- Asegurarse de que el cliente tenga implementado el procesamiento del nuevo tipo de mensaje

## 4. Implementar la recepción de un mensaje del cliente

### 4.1 Crear la clase del mensaje
Crear una nueva clase que herede de IMsg en el archivo `/src/client_msg.py`:

```python
class MsgMiMensajeCliente(IMsg):
    def __init__(self, datos):
        self._tipo = "mi_mensaje_cliente"
        self._datos = datos

    def to_json(self):
        data = {
            "mensaje": self._tipo,
            "datos": self._datos
        }
        return json.dumps(data)
```

### 4.2 Crear el ServerTask
Crear una nueva clase que herede de IServerTask en el archivo `/src/server_tasks.py`:

```python
class ServerTaskMiMensajeCliente(IServerTask):
    def __init__(self, data):
        super().__init__(data)
        self._datos = data.get("datos")

    def run(self, server):
        # Implementar la lógica del mensaje
        pass
```

### 4.3 Registrar la tarea
Registrar la tarea en el diccionario de tareas en el archivo `/src/server_tasks_manager.py`:

```python
dict_task["mi_mensaje_cliente"] = ServerTaskMiMensajeCliente
```

### 4.4 Implementar el mensaje en el ClientTransmisor
Añadir el método en la clase ClientTransmisor en el archivo `/src/client_transmisor.py`:

```python
def enviar_mi_mensaje(self, datos):
    msg = MsgMiMensajeCliente(datos)
    self._send_message(msg)
```

### 4.5 Usar el mensaje
Para enviar el mensaje desde el cliente:

```python
client.transmisor.enviar_mi_mensaje(datos)
```

## 5. Enviar un mensaje desde el servidor al cliente

### 5.1 Crear la clase del mensaje
Crear una nueva clase que herede de IMsg en el archivo `/src/server_msg.py`:

```python
class MsgMiMensajeServidor(IMsg):
    def __init__(self, datos):
        self._tipo = "mi_mensaje_servidor"
        self._datos = datos

    def to_json(self):
        data = {
            "mensaje": self._tipo,
            "datos": self._datos
        }
        return json.dumps(data)
```

### 5.2 Implementar el mensaje en el ServerTransmisor
Añadir el método en la clase ServerTransmisor en el archivo `/src/server_transmisor.py`:

```python
def enviar_mi_mensaje_servidor(self, datos):
    msg = MsgMiMensajeServidor(datos)
    self._send_message(msg)
```

### 5.3 Usar el mensaje
Para enviar el mensaje desde el servidor:

```python
client.transmisor.enviar_mi_mensaje_servidor(datos)
```

### 5.4 Crear la tarea del cliente
Crear una nueva clase que herede de IClientTask en el archivo `/src/client_tasks.py`:

```python
class ClientTaskMiMensajeServidor(IClientTask):
    def __init__(self, data):
        super().__init__(data)
        self._datos = data.get("datos")

    def run(self, client):
        # Implementar la lógica del mensaje
        pass
```

### 5.5 Registrar la tarea
Registrar la tarea en el diccionario de tareas en el archivo `/src/client_tasks_manager.py`:

```python
dict_task["mi_mensaje_servidor"] = ClientTaskMiMensajeServidor
```


