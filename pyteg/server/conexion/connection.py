"""Wrapper simple sobre sockets para el servidor."""

from __future__ import annotations

import socket

from pyteg.codecs_utils import Utf8


class ConnectionServer:
    """Wrapper para manejar la conexión de socket del servidor con un cliente."""

    def __init__(self, connection: socket.socket, addr: tuple[str, int]) -> None:
        """Inicializa la conexión del servidor.

        Args:
            connection: Socket de conexión.
            addr: Tupla con (host, puerto) de la dirección del cliente.

        """
        self._conn = connection
        self._addr = addr

    def receiver(self) -> list[str] | None:
        r"""Recibe datos del cliente.

        Returns:
            Lista de mensajes recibidos (separados por \0) o None si hay error.

        """
        data = ""
        try:
            encode_data = self._conn.recv(1024)
            if not encode_data:
                return None
            data = Utf8.decode(encode_data)
            print(f"Recibiendo {data}")
        except ConnectionResetError:
            return None
        except BrokenPipeError as ex:
            print("BrokenPipeError:", ex)
            return None
        except (ConnectionError, OSError) as ex:
            print("Exception:", ex)
            return None
        return data.split("\0")

    def send(self, data: str) -> None:
        """Envía datos al cliente.

        Args:
            data: Datos a enviar.

        """
        print(f"Enviando {data}")
        encode_data = Utf8.encode(data + "\0")
        try:
            self._conn.sendall(encode_data)
        except BrokenPipeError as ex:
            print("BrokenPipeError:", ex)
        except (ConnectionError, OSError) as ex:
            print("Exception:", ex)

    def close(self) -> None:
        """Cierra la conexión con el cliente."""
        try:
            self._conn.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass
        finally:
            try:
                self._conn.close()
            except OSError as ex:
                print("Exception:", ex)
