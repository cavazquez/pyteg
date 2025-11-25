"""Wrapper simple sobre sockets para el servidor."""

from __future__ import annotations

import socket

from src.codecs_utils import Utf8


class ConnectionServer:
    def __init__(self, connection: socket.socket, addr: tuple[str, int]) -> None:
        self._conn = connection
        self._addr = addr

    def receiver(self) -> list[str] | None:
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
        print(f"Enviando {data}")
        encode_data = Utf8.encode(data + "\0")
        try:
            self._conn.sendall(encode_data)
        except BrokenPipeError as ex:
            print("BrokenPipeError:", ex)
        except (ConnectionError, OSError) as ex:
            print("Exception:", ex)

    def close(self) -> None:
        try:
            self._conn.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass
        finally:
            try:
                self._conn.close()
            except OSError as ex:
                print("Exception:", ex)
