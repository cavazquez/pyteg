"""
Validador de tareas del servidor basado en estados.
"""

from src.exception import EstadoInvalidoError
from src.server_estado import Estado


class ServerStateValidator:
    """
    Clase encargada de validar si una acción puede ejecutarse según el estado
    actual del servidor.
    """

    def __init__(self):
        """Inicializa el validador."""

    def validar_accion(self, action_name: str, server) -> None:
        """
        Valida si una acción puede ejecutarse en el estado actual del servidor.

        Args:
            action_name: Nombre de la acción a validar
            server: Instancia del servidor con el estado actual

        Raises:
            EstadoInvalidoError: Si la acción no es válida en el estado actual
        """
        if not action_name or not hasattr(server, "estado"):
            return  # No hay validación necesaria

        if not server.estado.puede_ejecutar_accion(action_name):
            acciones_validas = Estado.get_acciones_validas()
            estados_validos = acciones_validas.get(action_name, [])

            raise EstadoInvalidoError(
                action_name, server.estado.estado_actual(), estados_validos
            )

    def puede_ejecutar(self, action_name: str, server) -> bool:
        """
        Verifica si una acción puede ejecutarse sin lanzar excepción.

        Args:
            action_name: Nombre de la acción a verificar
            server: Instancia del servidor con el estado actual

        Returns:
            True si la acción puede ejecutarse, False en caso contrario
        """
        try:
            self.validar_accion(action_name, server)
        except EstadoInvalidoError:
            return False
        else:
            return True
