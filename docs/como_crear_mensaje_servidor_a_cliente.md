# Instrucciones para implementar un nuevo mensaje del servidor al cliente

## 1. Crear la clase del mensaje
Crear una nueva clase que herede de `IMsg` dentro del paquete `pyteg/server/msg/`
(elegí el módulo de dominio adecuado: `connection.py`, `map_turn.py`,
`battle.py`, `cards_missiles.py`, etc., o creá uno nuevo y reexportalo en
`pyteg/server/msg/__init__.py`):

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
Añadir el método en la clase `ServerTransmisor` en
`pyteg/server/conexion/transmisor.py`:

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
