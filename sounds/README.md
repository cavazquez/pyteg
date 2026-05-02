# Archivos de Sonido para PyTeg

Este directorio contiene los efectos de sonido utilizados en el juego.

## Archivos requeridos

Los siguientes archivos de sonido son esperados por el sistema:

- **attack.wav**: Sonido de ataque/batalla
- **move.wav**: Sonido de movimiento de unidades
- **turn.wav**: Sonido de cambio de turno
- **victory.wav**: Sonido de victoria
- **defeat.wav**: Sonido de derrota
- **card.wav**: Sonido de carta (canje, reclamar)
- **dice.wav**: Sonido de lanzamiento de dados
- **button.wav**: Sonido de clic en botón
- **error.wav**: Sonido de error
- **connect.wav**: Sonido de conexión al servidor
- **disconnect.wav**: Sonido de desconexión

## Formato

- **Formato recomendado**: WAV (sin compresión)
- **Frecuencia de muestreo**: 44100 Hz
- **Canales**: Mono o Estéreo
- **Duración recomendada**: 0.5 - 2 segundos (efectos cortos)

## Fuentes de sonidos gratuitos

Puedes obtener efectos de sonido gratuitos de:

- [Freesound.org](https://freesound.org/) - Licencias Creative Commons
- [Zapsplat.com](https://www.zapsplat.com/) - Efectos gratuitos
- [Mixkit.co](https://mixkit.co/free-sound-effects/) - Efectos gratuitos
- [OpenGameArt.org](https://opengameart.org/) - Recursos para juegos

## Licencia y origen de los WAV incluidos

Los archivos `*.wav` del repositorio provienen del pack **The Essential Retro Video Game Sound Effects Collection [512 sounds]** de **Juhani Junkala**, publicado en [OpenGameArt.org](https://opengameart.org/) bajo licencia **CC0** (dominio público). Se eligieron clips del pack y se renombraron para coincidir con los nombres que usa `SoundManager`:

| Archivo PyTeg | Origen en el pack |
|----------------|-------------------|
| `attack.wav` | `General Sounds/Impacts/sfx_sounds_impact1.wav` |
| `move.wav` | `General Sounds/Menu Sounds/sfx_menu_move2.wav` |
| `turn.wav` | `General Sounds/Menu Sounds/sfx_menu_move1.wav` |
| `victory.wav` | `General Sounds/Positive Sounds/sfx_sounds_powerup1.wav` |
| `defeat.wav` | `General Sounds/Negative Sounds/sfx_sounds_damage1.wav` |
| `card.wav` | `General Sounds/Coins/sfx_coin_single1.wav` |
| `dice.wav` | `General Sounds/Impacts/sfx_sounds_impact3.wav` |
| `button.wav` | `General Sounds/Menu Sounds/sfx_menu_move3.wav` |
| `error.wav` | `General Sounds/Negative Sounds/sfx_sounds_error1.wav` |
| `connect.wav` | `General Sounds/Menu Sounds/sfx_menu_select1.wav` |
| `disconnect.wav` | `General Sounds/Negative Sounds/sfx_sounds_error4.wav` |

## Notas

- Si un archivo de sonido no está presente, el juego funcionará normalmente sin ese efecto
- Los archivos deben estar en formato WAV para compatibilidad óptima
- Mantén los archivos pequeños para un rendimiento óptimo
