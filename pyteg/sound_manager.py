"""Gestor de sonidos para PyTeg.

Este módulo proporciona una clase para gestionar la reproducción de efectos
de sonido en el juego, incluyendo control de volumen y mute.
"""

from pathlib import Path

from PySide6.QtCore import QUrl
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer

from pyteg.utils import get_resource_path


class SoundManager:
    """Gestor centralizado de efectos de sonido del juego."""

    def __init__(self) -> None:
        """Inicializa el gestor de sonidos."""
        self._enabled = True
        self._volume = 0.5  # Volumen por defecto (0.0 a 1.0)
        self._players: dict[
            str, QMediaPlayer
        ] = {}  # Cache de reproductores por tipo de sonido
        self._audio_outputs: dict[str, QAudioOutput] = {}  # Cache de salidas de audio

        # Mapeo de eventos a archivos de sonido
        self._sound_files = {
            "attack": "attack.wav",
            "move": "move.wav",
            "turn": "turn.wav",
            "victory": "victory.wav",
            "defeat": "defeat.wav",
            "card": "card.wav",
            "dice": "dice.wav",
            "button": "button.wav",
            "error": "error.wav",
            "connect": "connect.wav",
            "disconnect": "disconnect.wav",
        }

    def _get_sound_path(self, sound_name: str) -> Path | None:
        """Obtiene la ruta completa de un archivo de sonido.

        Args:
            sound_name: Nombre del sonido (sin extensión)

        Returns:
            Path al archivo de sonido o None si no existe

        """
        if sound_name not in self._sound_files:
            return None

        filename = self._sound_files[sound_name]
        sound_path = get_resource_path(f"sounds/{filename}")

        if not sound_path.exists():
            print(f"Advertencia: Archivo de sonido no encontrado: {sound_path}")
            return None

        return sound_path

    def _get_or_create_player(self, sound_name: str) -> QMediaPlayer | None:
        """Obtiene o crea un reproductor para un sonido específico.

        Args:
            sound_name: Nombre del sonido

        Returns:
            QMediaPlayer configurado o None si el archivo no existe

        """
        # Si ya existe el reproductor, reutilizarlo
        if sound_name in self._players:
            return self._players[sound_name]

        # Obtener ruta del archivo
        sound_path = self._get_sound_path(sound_name)
        if not sound_path:
            return None

        # Crear nuevo reproductor y salida de audio
        player = QMediaPlayer()
        audio_output = QAudioOutput()
        audio_output.setVolume(self._volume)

        player.setAudioOutput(audio_output)
        player.setSource(QUrl.fromLocalFile(str(sound_path)))

        # Guardar en cache
        self._players[sound_name] = player
        self._audio_outputs[sound_name] = audio_output

        return player

    def play(self, sound_name: str) -> None:
        """Reproduce un efecto de sonido.

        Args:
            sound_name: Nombre del sonido a reproducir

        """
        if not self._enabled:
            return

        player = self._get_or_create_player(sound_name)
        if not player:
            return

        # Si está reproduciendo, reiniciar
        if player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            player.stop()

        player.play()

    def set_volume(self, volume: float) -> None:
        """Establece el volumen global de los sonidos.

        Args:
            volume: Volumen entre 0.0 (silencio) y 1.0 (máximo)

        """
        self._volume = max(0.0, min(1.0, volume))

        # Actualizar volumen de todos los reproductores existentes
        for audio_output in self._audio_outputs.values():
            audio_output.setVolume(self._volume)

    def get_volume(self) -> float:
        """Obtiene el volumen actual.

        Returns:
            Volumen actual (0.0 a 1.0)

        """
        return self._volume

    def set_enabled(self, enabled: bool) -> None:  # noqa: FBT001
        """Habilita o deshabilita la reproducción de sonidos.

        Args:
            enabled: True para habilitar, False para deshabilitar

        """
        self._enabled = enabled

        # Si se deshabilita, detener todos los sonidos en reproducción
        if not enabled:
            self.stop_all()

    def is_enabled(self) -> bool:
        """Verifica si los sonidos están habilitados.

        Returns:
            True si están habilitados, False en caso contrario

        """
        return self._enabled

    def stop_all(self) -> None:
        """Detiene todos los sonidos en reproducción."""
        for player in self._players.values():
            if player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
                player.stop()

    def cleanup(self) -> None:
        """Libera recursos de todos los reproductores."""
        self.stop_all()
        self._players.clear()
        self._audio_outputs.clear()

    # Métodos de conveniencia para eventos comunes
    def play_attack(self) -> None:
        """Reproduce sonido de ataque."""
        self.play("attack")

    def play_move(self) -> None:
        """Reproduce sonido de movimiento."""
        self.play("move")

    def play_turn(self) -> None:
        """Reproduce sonido de cambio de turno."""
        self.play("turn")

    def play_victory(self) -> None:
        """Reproduce sonido de victoria."""
        self.play("victory")

    def play_defeat(self) -> None:
        """Reproduce sonido de derrota."""
        self.play("defeat")

    def play_card(self) -> None:
        """Reproduce sonido de carta."""
        self.play("card")

    def play_dice(self) -> None:
        """Reproduce sonido de dados."""
        self.play("dice")

    def play_button(self) -> None:
        """Reproduce sonido de botón."""
        self.play("button")

    def play_error(self) -> None:
        """Reproduce sonido de error."""
        self.play("error")

    def play_connect(self) -> None:
        """Reproduce sonido de conexión."""
        self.play("connect")

    def play_disconnect(self) -> None:
        """Reproduce sonido de desconexión."""
        self.play("disconnect")
