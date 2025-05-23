# Enviar un mensaje desde el servidor al cliente

## 1. Crear la clase del mensaje
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

## 2. Implementar el mensaje en el ServerTransmisor
Añadir el método en la clase ServerTransmisor en el archivo `/src/server_transmisor.py`:

```python
def enviar_mi_mensaje_servidor(self, datos):
    msg = MsgMiMensajeServidor(datos)
    self._send_message(msg)
```

## 3. Usar el mensaje
Para enviar el mensaje desde el servidor:

```python
client.transmisor.enviar_mi_mensaje_servidor(datos)
```

## 4. Crear la tarea del cliente
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

## 5. Registrar la tarea
Registrar la tarea en el diccionario de tareas en el archivo `/src/client_tasks_manager.py`:

```python
dict_task["mi_mensaje_servidor"] = ClientTaskMiMensajeServidor
```
