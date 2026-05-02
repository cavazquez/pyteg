# Implementar la recepción de un mensaje del cliente

## 1. Crear la clase del mensaje
Crear una nueva clase que herede de `IMsg` dentro del paquete
`pyteg/client/msg/` (elegí el módulo de dominio adecuado: `lobby.py`,
`actions.py`, `cards.py`, `missiles.py`, etc., y reexportá la clase desde
`pyteg/client/msg/__init__.py`):

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
Crear una nueva clase que herede de `IServerTask` dentro del paquete
`pyteg/server/tasks/` (en el sub-paquete que corresponda al dominio:
`lobby/`, `game_actions/`, `cards_missiles/`, etc.):

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
Registrar la tarea en el diccionario de tareas en
`pyteg/server/tasks/manager.py`:

```python
dict_task["mi_mensaje_cliente"] = ServerTaskMiMensajeCliente
```

## 4. Implementar el mensaje en el ClientTransmisor
Añadir el método en la clase `ClientTransmisor` en
`pyteg/client/conexion/transmisor/transmisor.py`:

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
