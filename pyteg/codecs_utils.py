"""Utilidades simples para codificación UTF-8."""

from __future__ import annotations

import codecs

DEFAULT_MAX_FRAME_BYTES = 1_000_000


class Utf8:
    """Utilidades para codificación y decodificación UTF-8."""

    @staticmethod
    def encode(data: str) -> bytes:
        """Codifica una cadena de texto a bytes UTF-8.

        Args:
            data: Cadena de texto a codificar.

        Returns:
            Bytes codificados en UTF-8.

        """
        return codecs.encode(data, encoding="utf-8")

    @staticmethod
    def decode(data: bytes) -> str:
        """Decodifica bytes UTF-8 a una cadena de texto.

        Args:
            data: Bytes a decodificar.

        Returns:
            Cadena de texto decodificada.

        """
        return codecs.decode(data, encoding="utf-8")


class FrameCodecError(ValueError):
    """Error de framing en el protocolo TCP delimitado por NUL."""


class FrameTooLargeError(FrameCodecError):
    """Una trama excedió el tamaño máximo permitido."""


class IncompleteFrameError(FrameCodecError):
    """La conexión terminó antes de recibir el delimitador de una trama."""


class InvalidFrameEncodingError(FrameCodecError):
    """Una trama completa no contiene UTF-8 válido."""


class NulDelimitedUtf8Codec:
    r"""Reconstruye mensajes UTF-8 delimitados por ``\0`` sobre un stream TCP.

    TCP entrega bytes sin límites de mensaje. Este codec acumula los bytes hasta
    observar el delimitador, de modo que un carácter UTF-8 o un JSON fragmentado
    nunca se decodifican parcialmente.
    """

    _DELIMITER = b"\0"

    def __init__(self, max_frame_bytes: int = DEFAULT_MAX_FRAME_BYTES) -> None:
        """Inicializa el buffer incremental con un límite por trama.

        Args:
            max_frame_bytes: Máximo de bytes de payload antes del delimitador.

        Raises:
            ValueError: Si el límite no es positivo.

        """
        if max_frame_bytes <= 0:
            msg = "max_frame_bytes debe ser positivo"
            raise ValueError(msg)
        self._max_frame_bytes = max_frame_bytes
        self._buffer = bytearray()

    @staticmethod
    def encode_frame(message: str) -> bytes:
        """Codifica una trama de salida usando el protocolo JSON + NUL.

        Args:
            message: Payload textual ya serializado.

        Returns:
            Bytes UTF-8 seguidos por un byte NUL.

        """
        return Utf8.encode(message) + NulDelimitedUtf8Codec._DELIMITER

    @property
    def pending_bytes(self) -> int:
        """Devuelve la cantidad de bytes aún sin delimitador."""
        return len(self._buffer)

    def feed(self, data: bytes) -> list[str]:
        """Incorpora bytes recibidos y devuelve sólo las tramas completas.

        Args:
            data: Bytes recién recibidos desde el socket.

        Returns:
            Mensajes completos, en el mismo orden que llegaron.

        Raises:
            FrameTooLargeError: Si una trama supera el límite configurado.
            InvalidFrameEncodingError: Si una trama completa no es UTF-8 válido.

        """
        self._buffer.extend(data)
        messages: list[str] = []

        while True:
            delimiter_index = self._buffer.find(self._DELIMITER)
            if delimiter_index < 0:
                if len(self._buffer) > self._max_frame_bytes:
                    msg = "La trama TCP sin terminar supera el tamaño máximo"
                    raise FrameTooLargeError(msg)
                return messages

            if delimiter_index > self._max_frame_bytes:
                msg = "La trama TCP supera el tamaño máximo"
                raise FrameTooLargeError(msg)

            raw_frame = bytes(self._buffer[:delimiter_index])
            del self._buffer[: delimiter_index + len(self._DELIMITER)]
            try:
                messages.append(Utf8.decode(raw_frame))
            except UnicodeDecodeError as error:
                msg = "La trama TCP no contiene UTF-8 válido"
                raise InvalidFrameEncodingError(msg) from error

    def finish(self) -> None:
        """Valida que no quede una trama parcial al recibir EOF.

        Raises:
            IncompleteFrameError: Si el peer cerró con bytes sin delimitador.

        """
        if self._buffer:
            msg = "El peer cerró la conexión con una trama TCP incompleta"
            raise IncompleteFrameError(msg)
