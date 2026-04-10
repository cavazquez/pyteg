# Implementar la recepción de un mensaje del cliente

## 1. Crear la clase del mensaje
Crear una nueva clase que herede de IMsg en el archivo `/pyteg/client_msg.py`:

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

## 2. Crear el ServerTask
Crear una nueva clase que herede de IServerTask en el archivo `/pyteg/server_tasks.py`:

```python
class ServerTaskMiMensajeCliente(IServerTask):
    def __init__(self, data):
        super().__init__(data)
        self._datos = data.get("datos")

    def run(self, server):
        # Implementar la lógica del mensaje
        pass
```

## 3. Registrar la tarea
Registrar la tarea en el diccionario de tareas en el archivo `/pyteg/server_tasks_manager.py`:

```python
dict_task["mi_mensaje_cliente"] = ServerTaskMiMensajeCliente
```

## 4. Implementar el mensaje en el ClientTransmisor
Añadir el método en la clase ClientTransmisor en el archivo `/pyteg/client_transmisor.py`:

```python
def enviar_mi_mensaje(self, datos):
    msg = MsgMiMensajeCliente(datos)
    self._send_message(msg)
```

## 5. Usar el mensaje
Para enviar el mensaje desde el cliente:

```python
client.transmisor.enviar_mi_mensaje(datos)
```
