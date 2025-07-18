import socket
import threading

from src.logger import get_logger
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
    logger = get_logger("server.registrar_jugadores")
    logger.info("Iniciando servidor de jugadores en %s:%s", host, port)

    server_build_client = ServerBuildClient()
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    try:
        server_socket.bind((host, port))
        server_socket.listen()

        while True:
            try:
                logger.debug("Esperando conexiones en %s:%s...", host, port)
                conn, addr = server_socket.accept()
                logger.info("Nueva conexión aceptada desde %s", addr)

                # Verificar si el juego ya está en progreso
                if server.estado.es_jugando() or server.estado.es_finalizado():
                    estado_actual = server.estado.estado_actual()
                    logger.warning(
                        "Rechazando conexión de %s: "
                        "El juego ya está en progreso (estado: %s)",
                        addr,
                        estado_actual,
                    )
                    # Enviar mensaje de rechazo y cerrar conexión
                    try:
                        mensaje_rechazo = (
                            "El juego ya está en progreso. "
                            "No se pueden conectar nuevos jugadores."
                        )
                        conn.send(mensaje_rechazo.encode("utf-8"))
                    except Exception:
                        logger.exception("Error al enviar mensaje de rechazo")
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
                logger.info("Cliente %s conectado y en ejecución", user_id)

            except KeyboardInterrupt:
                logger.info("Deteniendo el servidor por interrupción del usuario")
                break
            except Exception:
                logger.exception("Error al manejar la conexión")

    except Exception as e:
        logger.critical("Error crítico en el servidor: %s", e, exc_info=True)
    finally:
        logger.info("Cerrando el servidor...")
        server_socket.close()
