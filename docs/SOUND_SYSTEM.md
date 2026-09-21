# Sistema de Sonidos de PyTeg

## Resumen

Se ha implementado un sistema completo de efectos de sonido para PyTeg que proporciona retroalimentación auditiva para eventos clave del juego.

## Arquitectura

### Componentes principales

1. **SoundManager** (`pyteg/sound_manager.py`)
   - Gestor centralizado de reproducción de sonidos
   - Usa `QMediaPlayer` y `QAudioOutput` de PySide6
   - Control de volumen (0.0 - 1.0)
   - Sistema de mute/unmute
   - Cache de reproductores para mejor rendimiento

2. **SoundControlWidget** (`pyteg/gui/widgets/sound_control.py`)
   - Widget de control en la barra de estado
   - Botón de mute/unmute con iconos dinámicos (🔊/🔉/🔇)
   - Slider de volumen (0-100%)
   - Indicador de porcentaje

3. **Integración en GUI** (`pyteg/gui/main_window.py`)
   - Instancia de `SoundManager` creada al inicializar
   - Widget de control agregado a la barra de estado
   - Limpieza de recursos al cerrar la aplicación

## Eventos con sonido

Todos los eventos relevantes tienen un WAV registrado y se reproducen desde el
flujo que recibe o confirma el evento. La reproducción es local: el servidor
nunca envía audio por TCP.

| Evento | Sonido | Integración |
|--------|--------|-------------|
| **Ataque/Batalla** | `attack.wav` | `ClientTaskResultadoBatalla` |
| **Dados de batalla** | `dice.wav` | `ClientTaskResultadoBatalla`, cuando el resultado trae dados |
| **Movimiento de unidades** | `move.wav` | `ClientTransmisor.mover_unidad()` |
| **Cambio de turno** | `turn.wav` | `ClientTaskTurno` |
| **Victoria / derrota** | `victory.wav` / `defeat.wav` | `ClientTaskVictoria` |
| **Conexión / desconexión** | `connect.wav` / `disconnect.wav` | `ConnectionClient` |
| **Tarjetas** | `card.wav` | `ClientTaskTarjetasJugador`, solo cuando cambia la mano |
| **Error de servidor o socket** | `error.wav` | `ClientTaskError` y `ConnectionClient.display_error()` |
| **Control de sonido** | `button.wav` | Confirmación al reactivar el audio |

El sonido de botón no se conecta globalmente a cada `QPushButton`: hacerlo
produciría clics para controles de navegación y diálogos que no representan una
acción de juego. Las acciones de tarjetas se confirman con `card.wav` cuando el
servidor devuelve la mano actualizada.

## Archivos de sonido

### Ubicación
Los archivos de sonido deben colocarse en el directorio `sounds/` en la raíz del proyecto.

### Formato recomendado
- **Formato**: WAV (sin compresión)
- **Frecuencia**: 44100 Hz
- **Canales**: Mono o Estéreo
- **Duración**: 0.5 - 2 segundos

### Obtener sonidos
Ver `sounds/README.md` para fuentes de sonidos gratuitos:
- Freesound.org
- Zapsplat.com
- Mixkit.co
- OpenGameArt.org

## Uso

### Control de volumen

```python
# Obtener instancia del sound manager
sound_manager = main_window.sound_manager

# Ajustar volumen (0.0 - 1.0)
sound_manager.set_volume(0.7)

# Obtener volumen actual
volume = sound_manager.get_volume()

# Silenciar/activar
sound_manager.set_enabled(False)  # Silenciar
sound_manager.set_enabled(True)   # Activar

# Verificar estado
is_enabled = sound_manager.is_enabled()
```

### Reproducir sonidos

```python
# Métodos de conveniencia
sound_manager.play_attack()
sound_manager.play_move()
sound_manager.play_turn()
sound_manager.play_victory()
sound_manager.play_defeat()
sound_manager.play_card()
sound_manager.play_dice()
sound_manager.play_button()
sound_manager.play_error()
sound_manager.play_connect()
sound_manager.play_disconnect()

# Método genérico
sound_manager.play("attack")
```

### Agregar nuevos sonidos

1. **Agregar archivo de sonido** en `sounds/`
2. **Registrar en SoundManager** (`sound_manager.py`):
   ```python
   self._sound_files = {
       # ... existentes ...
       "nuevo_evento": "nuevo_sonido.wav",
   }
   ```
3. **Agregar método de conveniencia** (opcional):
   ```python
   def play_nuevo_evento(self) -> None:
       """Reproduce sonido de nuevo evento."""
       self.play("nuevo_evento")
   ```
4. **Integrar en el evento** correspondiente del juego

## Características técnicas

### Ventajas

- **Sin bloqueo**: Los sonidos se reproducen de forma asíncrona
- **Cache**: Los reproductores se reutilizan para mejor rendimiento
- **Fallback gracioso**: Si falta un archivo, el juego continúa sin errores
- **Control granular**: Volumen y mute independientes
- **Interfaz integrada**: Controles accesibles en la barra de estado

### Manejo de errores

- Si un archivo de sonido no existe, se imprime una advertencia pero el juego continúa
- Los reproductores se crean bajo demanda
- Limpieza automática de recursos al cerrar

## Archivos relevantes

- `pyteg/sound_manager.py` - Gestor, cache, volumen, mute y fallback.
- `pyteg/gui/widgets/sound_control.py` - Control de sesión y sonido de botón.
- `pyteg/client/tasks/battle.py` - Ataque y dados.
- `pyteg/client/tasks/cards_missiles.py` - Cambios de mano.
- `pyteg/client/tasks/lobby/chat.py` - Errores del servidor.
- `pyteg/client/tasks/game_flow/turno.py` y `partida.py` - Turno y victoria/derrota.
- `pyteg/client/conexion/transmisor/transmisor.py` y `connection.py` - Movimiento,
  conexión, desconexión y errores de socket.
- `tests/test_sound_manager.py` y `tests/test_client_task_sound_events.py` -
  Recursos e integración de eventos sin hardware de audio.

## Recursos y ejecución sin audio

`pyproject.toml` incluye `sounds/` en `force-include`, por lo que los WAV se
copian al wheel y a los artefactos de Nuitka junto con `themes/`, `locales/` e
`icons/`. `SoundManager` resuelve la ruta con `get_resource_path`, crea los
reproductores bajo demanda y continúa en silencio si un archivo falta. La
prueba `test_todos_los_eventos_tienen_recurso_empaquetado` verifica el inventario
completo sin abrir un dispositivo de audio; también se prueba el fallback para
un recurso ausente.

El volumen y el mute son preferencias de la sesión actual (por defecto 50% y
activos); todavía no se persisten entre ejecuciones. La interfaz funciona en
modo `QT_QPA_PLATFORM=offscreen` porque la reproducción no se inicializa hasta
que se dispara un evento.

## Próximos pasos

1. Persistir volumen y mute con la configuración de usuario si se necesita
   conservarlos entre ejecuciones.
2. Añadir un sonido específico para misiles si la interfaz requiere una
   diferencia audible respecto de una batalla.

## Notas

- El sistema funciona sin archivos de audio (modo silencioso)
- Los controles están siempre visibles en la barra de estado
- El volumen por defecto es 50%
- Los sonidos están habilitados por defecto
