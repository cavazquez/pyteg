"""
Validador de tareas del servidor basado en estados.
"""

from src.exception import EstadoInvalidoError


class ServerStateValidator:
    """
    Clase encargada de validar si una acción puede ejecutarse según el estado
    actual del servidor.
    """

    def __init__(self):
        """Inicializa el validador con el mapeo de acciones válidas por estado."""
        self._acciones_validas = {}

    def _get_acciones_validas(self, estado) -> dict[str, list[str]]:
        """
        Obtiene el mapeo de acciones válidas para cada estado.

        Args:
            estado: Instancia del objeto Estado del servidor

        Returns:
            Dict con las acciones válidas para cada estado
        """
        return {
            "empezar": [estado.INICIAL],
            "empezar_partida": [estado.ESPERAR_JUGADORES],
            "seleccionar_color": [estado.INICIAL, estado.ESPERAR_JUGADORES],
            "set_username": [estado.INICIAL, estado.ESPERAR_JUGADORES],
            "chat": [estado.INICIAL, estado.ESPERAR_JUGADORES, estado.JUGANDO],
            "agregar_unidad": [estado.JUGANDO],
            "mover_unidad": [estado.JUGANDO],
            "atacar": [estado.JUGANDO],
            "finalizar_turno": [estado.JUGANDO],
            "solicitar_tarjetas": [estado.JUGANDO],
            "reclamar_tarjeta": [estado.JUGANDO],
        }

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
            acciones_validas = self._get_acciones_validas(server.estado)
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
