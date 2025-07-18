import socket
import threading

from src.server_build_client import ServerBuildClient
from src.server_client_connection import ConnectionServer


def registrar_jugadores(server, host: str = "127.0.0.1", port: int = 65432):
    """
    Inicia el servidor para aceptar conexiones de jugadores.

    Args:
        server: Instancia del servidor que manejará las conexiones
        host: Dirección IP donde escuchar (predeterminado: 127.0.0.1)
        port: Puerto donde escuchar (predeterminado: 65432)
    """
    print(f"Esperando jugadores en {host}:{port}...")

    server_build_client = ServerBuildClient()
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    try:
        server_socket.bind((host, port))
        server_socket.listen()

        while True:
            try:
                print(f"Esperando conexiones en {host}:{port}...")
                conn, addr = server_socket.accept()
                print(f"Conexión aceptada desde {addr}")

                # Verificar si el juego ya está en progreso
                if server.estado.es_jugando() or server.estado.es_finalizado():
                    estado_actual = server.estado.estado_actual()
                    print(
                        f"Rechazando conexión de {addr}: "
                        f"El juego ya está en progreso (estado: {estado_actual})"
                    )
                    # Enviar mensaje de rechazo y cerrar conexión
                    try:
                        mensaje_rechazo = (
                            "El juego ya está en progreso. "
                            "No se pueden conectar nuevos jugadores."
                        )
                        conn.send(mensaje_rechazo.encode("utf-8"))
                    except Exception as e:
                        print(f"Error al enviar mensaje de rechazo: {e}")
                    finally:
                        conn.close()
                    continue

                connection = ConnectionServer(conn, addr)
                user_id, client = server_build_client.build(connection, server)
                server.registrar_cliente(user_id, client)

                # Iniciar el cliente en un nuevo hilo
                client_thread = threading.Thread(
                    target=client.run,
                    daemon=True,  # El hilo terminará cuando
                    # el programa principal termine
                )
                client_thread.start()
                print(f"Cliente {user_id} conectado y en ejecución")

            except KeyboardInterrupt:
                print("\nDeteniendo el servidor...")
                break
            except Exception as e:
                print(f"Error al manejar la conexión: {e}")

    except Exception as e:
        print(f"Error en el servidor: {e}")
    finally:
        print("Cerrando el servidor...")
        server_socket.close()
