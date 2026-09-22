"""Gestor de sonidos para PyTeg.

Este módulo proporciona una clase para gestionar la reproducción de efectos
de sonido en el juego, incluyendo control de volumen y mute.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

from PySide6.QtCore import QUrl
from PySide6.QtMultimedia import QAudioOutput as QQtAudioOutput
from PySide6.QtMultimedia import QMediaPlayer

from pyteg.logger import get_logger
from pyteg.utils import get_resource_path

if TYPE_CHECKING:
    from pathlib import Path

LOGGER = get_logger(__name__)


class AudioOutput(Protocol):
    """Salida de audio que puede utilizar ``SoundManager``."""

    def play(self, sound_name: str, sound_path: Path | None) -> None:
        """Reproduce un sonido disponible en ``sound_path``."""

    def set_volume(self, volume: float) -> None:
        """Actualiza el volumen de los sonidos activos y futuros."""

    def stop_all(self) -> None:
        """Detiene los sonidos que estén reproduciéndose."""

    def cleanup(self) -> None:
        """Libera los recursos de la salida."""


class NullAudioOutput:
    """Salida nula para clientes sin reproducción de audio."""

    def play(self, _sound_name: str, _sound_path: Path | None) -> None:
        """Ignora el sonido solicitado."""

    def set_volume(self, _volume: float) -> None:
        """Ignora el volumen solicitado."""

    def stop_all(self) -> None:
        """No tiene sonidos que detener."""

    def cleanup(self) -> None:
        """No tiene recursos que liberar."""


class QtAudioOutput:
    """Salida de audio basada en los reproductores multimedia de Qt."""

    def __init__(self, *, volume: float = 0.5) -> None:
        """Inicializa la salida multimedia con el volumen indicado."""
        self._volume = volume
        self._players: dict[str, QMediaPlayer] = {}
        self._audio_outputs: dict[str, QQtAudioOutput] = {}

    def play(self, sound_name: str, sound_path: Path | None) -> None:
        """Reproduce un sonido y reinicia su reproductor si ya estaba activo."""
        if sound_path is None:
            return

        player = self._get_or_create_player(sound_name, sound_path)
        if player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            player.stop()
        player.play()

    def _get_or_create_player(self, sound_name: str, sound_path: Path) -> QMediaPlayer:
        """Obtiene o crea un reproductor para un sonido.

        Returns:
            Reproductor multimedia asociado al nombre del sonido.

        """
        player = self._players.get(sound_name)
        if player is not None:
            return player

        player = QMediaPlayer()
        audio_output = QQtAudioOutput()
        audio_output.setVolume(self._volume)
        player.setAudioOutput(audio_output)
        player.setSource(QUrl.fromLocalFile(str(sound_path)))
        self._players[sound_name] = player
        self._audio_outputs[sound_name] = audio_output
        return player

    def set_volume(self, volume: float) -> None:
        """Actualiza el volumen de todos los reproductores."""
        self._volume = volume
        for audio_output in self._audio_outputs.values():
            audio_output.setVolume(volume)

    def stop_all(self) -> None:
        """Detiene todos los sonidos en reproducción."""
        for player in self._players.values():
            if player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
                player.stop()

    def cleanup(self) -> None:
        """Libera los recursos de los reproductores multimedia."""
        self.stop_all()
        self._players.clear()
        self._audio_outputs.clear()


class SoundManager:
    """Gestor centralizado de efectos de sonido del juego."""

    def __init__(self, output: AudioOutput | None = None) -> None:
        """Inicializa el gestor con una salida Qt o una salida inyectada.

        Args:
            output: Salida de audio. Si no se proporciona, se usa
                ``QtAudioOutput``; ``NullAudioOutput`` permite ejecutar el
                cliente sin crear reproductores multimedia.

        """
        self._enabled = True
        self._volume = 0.5  # Volumen por defecto (0.0 a 1.0)
        self._output: AudioOutput = (
            output if output is not None else QtAudioOutput(volume=self._volume)
        )

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
        self._output.set_volume(self._volume)

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
            LOGGER.warning("Archivo de sonido no encontrado: %s", sound_path)
            return None

        return sound_path

    def play(self, sound_name: str) -> None:
        """Reproduce un efecto de sonido.

        Args:
            sound_name: Nombre del sonido a reproducir

        """
        if not self._enabled:
            return

        self._output.play(sound_name, self._get_sound_path(sound_name))

    def set_volume(self, volume: float) -> None:
        """Establece el volumen global de los sonidos.

        Args:
            volume: Volumen entre 0.0 (silencio) y 1.0 (máximo)

        """
        self._volume = max(0.0, min(1.0, volume))

        self._output.set_volume(self._volume)

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
        self._output.stop_all()

    def cleanup(self) -> None:
        """Libera recursos de todos los reproductores."""
        self._output.cleanup()

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
