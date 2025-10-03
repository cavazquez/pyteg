# Sistema de Sonidos de PyTeg

## Resumen

Se ha implementado un sistema completo de efectos de sonido para PyTeg que proporciona retroalimentación auditiva para eventos clave del juego.

## Arquitectura

### Componentes principales

1. **SoundManager** (`src/sound_manager.py`)
   - Gestor centralizado de reproducción de sonidos
   - Usa `QMediaPlayer` y `QAudioOutput` de PySide6
   - Control de volumen (0.0 - 1.0)
   - Sistema de mute/unmute
   - Cache de reproductores para mejor rendimiento

2. **SoundControlWidget** (`src/gui_sound_control.py`)
   - Widget de control en la barra de estado
   - Botón de mute/unmute con iconos dinámicos (🔊/🔉/🔇)
   - Slider de volumen (0-100%)
   - Indicador de porcentaje

3. **Integración en GUI** (`src/gui.py`)
   - Instancia de `SoundManager` creada al inicializar
   - Widget de control agregado a la barra de estado
   - Limpieza de recursos al cerrar la aplicación

## Eventos con sonido

### Implementados

| Evento | Sonido | Ubicación |
|--------|--------|-----------|
| **Ataque/Batalla** | `attack.wav` | `client_tasks.py` - `ClientTaskResultadoBatalla` |
| **Movimiento de unidades** | `move.wav` | `client_transmisor.py` - `mover_unidad()` |
| **Cambio de turno** | `turn.wav` | `client_tasks.py` - `ClientTaskTurno` |
| **Victoria** | `victory.wav` | `client_tasks.py` - `ClientTaskVictoria` |
| **Conexión** | `connect.wav` | `client_connection.py` - `on_connected()` |
| **Desconexión** | `disconnect.wav` | `client_connection.py` - `on_state_changed()` |

### Preparados (sin archivos de audio aún)

- `defeat.wav` - Derrota
- `card.wav` - Canje de tarjetas
- `dice.wav` - Lanzamiento de dados
- `button.wav` - Clic en botones
- `error.wav` - Errores

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

## Archivos modificados/creados

### Nuevos archivos
- `src/sound_manager.py` - Gestor de sonidos
- `src/gui_sound_control.py` - Widget de control
- `sounds/README.md` - Documentación de sonidos
- `docs/SOUND_SYSTEM.md` - Esta documentación

### Archivos modificados
- `src/gui.py` - Integración del SoundManager
- `src/client_tasks.py` - Sonidos en eventos (ataque, turno, victoria)
- `src/client_transmisor.py` - Sonido de movimiento
- `src/client_connection.py` - Sonidos de conexión/desconexión
- `README.md` - Actualizada lista de características

## Testing

- ✅ **161 tests pasan** sin errores
- ✅ **Linting limpio** (ruff)
- ✅ **Formato correcto** (ruff format)
- ✅ **Sin regresiones** en funcionalidad existente

## Próximos pasos

1. **Agregar archivos de audio reales** al directorio `sounds/`
2. **Ajustar volúmenes** de cada sonido individualmente si es necesario
3. **Agregar más eventos** (canje de tarjetas, lanzamiento de misiles, etc.)
4. **Configuración persistente** (guardar preferencias de volumen)
5. **Efectos de sonido adicionales** (hover, selección, etc.)

## Notas

- El sistema funciona sin archivos de audio (modo silencioso)
- Los controles están siempre visibles en la barra de estado
- El volumen por defecto es 50%
- Los sonidos están habilitados por defecto
