"""Módulo para coordinar el inicio y configuración de partidas.

Este módulo encapsula la lógica de configuración e inicio de partidas,
separando esta responsabilidad del Server principal.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from src.config import DEFAULT_TURN_SECONDS, VICTORY_ALL_COUNTRIES
from src.server_game import Game
from src.turno_timer import TurnoTimer

if TYPE_CHECKING:
    from src.mazo import Mazo
    from src.objetivos_secretos import ObjetivosSecretos
    from src.server_client import Client
    from src.server_estado import Estado
    from src.server_mapa import Mapa


class ServerGameCoordinator:
    """Coordina la configuración e inicio de partidas.

    Esta clase se encarga de toda la lógica relacionada con la configuración
    de parámetros de partida y el inicio de la misma, separando esta
    responsabilidad del Server principal.
    """

    def __init__(  # noqa: PLR0913, PLR0917
        self,
        mapa: Mapa,
        mazo: Mazo,
        objetivos_secretos: ObjetivosSecretos,
        estado: Estado,
        get_clients: Any,
        broadcaster: Any,
        color_manager: Any,
    ) -> None:
        """Inicializa el coordinador de partidas.

        Args:
            mapa: Instancia del mapa del juego.
            mazo: Instancia del mazo de tarjetas.
            objetivos_secretos: Instancia del gestor de objetivos secretos.
            estado: Instancia del estado del servidor.
            get_clients: Función o método que retorna la lista de clientes.
            broadcaster: Instancia del broadcaster de mensajes.
            color_manager: Instancia del gestor de colores.

        """
        self._mapa = mapa
        self._mazo = mazo
        self._objetivos_secretos = objetivos_secretos
        self._estado = estado
        self._get_clients = get_clients
        self._broadcaster = broadcaster
        self._color_manager = color_manager

        # Configuración de partida
        self._segundos_por_turno: int = DEFAULT_TURN_SECONDS
        self._paises_para_victoria: int = VICTORY_ALL_COUNTRIES
        self._objetivos_secretos_activados: bool = False
        self._misiles_habilitados: bool = False

        # Referencia al juego (se crea al iniciar la partida)
        self._game: Game | None = None
        self._turno_timer: TurnoTimer | None = None

    def set_segundos_por_turno(self, segundos: int) -> None:
        """Configura la cantidad de segundos por turno.

        Args:
            segundos: Segundos por turno (> 0).

        """
        if isinstance(segundos, int) and segundos > 0:
            self._segundos_por_turno = segundos

    def set_paises_para_victoria(self, paises: int) -> None:
        """Configura la cantidad de países necesarios para ganar.

        Args:
            paises: Países necesarios para victoria (> 0).

        """
        if isinstance(paises, int) and paises > 0:
            self._paises_para_victoria = paises

    def set_objetivos_secretos(self, *, activados: bool) -> None:
        """Configura si los objetivos secretos están activados.

        Args:
            activados: True si los objetivos secretos están activados.

        """
        self._objetivos_secretos_activados = activados

    def set_misiles_habilitados(self, *, activados: bool) -> None:
        """Configura si los misiles están habilitados.

        Args:
            activados: True si los misiles están habilitados.

        """
        self._misiles_habilitados = activados

    def misiles_habilitados(self) -> bool:
        """Retorna si los misiles están habilitados en esta partida.

        Returns:
            True si los misiles están habilitados.

        """
        return self._misiles_habilitados

    def enviar_configuracion_partida(self) -> None:
        """Envía la configuración de la partida a todos los clientes.

        Este método puede ser llamado para reenviar la configuración
        después de que la partida haya comenzado.
        """
        self._broadcaster.enviar_configuracion_partida(
            self._segundos_por_turno,
            self._paises_para_victoria,
            objetivos_secretos=self._objetivos_secretos_activados,
            misiles_habilitados=self._misiles_habilitados,
        )

    def empezar_partida(self, server: Any) -> Game:
        """Inicia la partida con la configuración actual.

        Args:
            server: Referencia al servidor (para pasar al Game).

        Returns:
            Instancia del juego creado.

        """
        print("Iniciando partida...")

        # Obtener la lista de jugadores
        jugadores = self._get_clients()
        print(f"Jugadores conectados: {[j.userid() for j in jugadores]}")

        # Crear e iniciar el juego, pasando la referencia al servidor
        self._game = Game(
            self._mapa,
            self._mazo,
            jugadores,
            server,
            self._paises_para_victoria,
        )
        self._game.empezar()

        # Enviar información de los jugadores y sus colores a todos los clientes
        print("Enviando colores asignados a los jugadores...")
        self._enviar_colores_asignados()

        # Enviar el mapa con los países y sus propietarios
        print("Enviando mapa a los jugadores...")
        self._broadcaster.enviar_mapa(self._mapa, self._game)

        # Notificar a los clientes que la partida ha comenzado
        print("Notificando a los clientes que la partida ha comenzado...")
        # Cambiar el estado a EmpezarPartida
        self._estado.empezar_partida()
        self._broadcaster.enviar_estado(self._estado.estado_actual())

        # Enviar el número de turno inicial a todos los clientes
        print("Enviando número de turno inicial a los clientes...")
        self._enviar_turno_actual()

        # Enviar la configuración de la partida a todos los clientes
        print("Enviando configuración de la partida a los clientes...")
        self._broadcaster.enviar_configuracion_partida(
            self._segundos_por_turno,
            self._paises_para_victoria,
            objetivos_secretos=self._objetivos_secretos_activados,
            misiles_habilitados=self._misiles_habilitados,
        )

        # Asignar y enviar objetivos secretos si están activados
        if self._objetivos_secretos_activados:
            print("Asignando objetivos secretos a los jugadores...")
            self._objetivos_secretos.asignar_objetivos_aleatorios(jugadores)
            self._broadcaster.enviar_objetivos_secretos(
                self._objetivos_secretos.get_objetivo_jugador
            )

        # Iniciar el temporizador de turnos
        print("Iniciando temporizador de turnos...")
        self._turno_timer = TurnoTimer(
            server, segundos_por_turno=self._segundos_por_turno
        )
        self._turno_timer.start()

        return self._game

    def game(self) -> Game | None:
        """Obtiene la instancia del juego actual.

        Returns:
            Instancia del juego o None si no ha comenzado.

        """
        return self._game

    def turno_timer(self) -> TurnoTimer | None:
        """Obtiene el temporizador de turnos.

        Returns:
            Instancia del temporizador o None si no está iniciado.

        """
        return self._turno_timer

    def _enviar_colores_asignados(self) -> None:
        """Envía los colores asignados a todos los clientes.

        Los envía en el orden de los turnos.
        """
        # Obtener la lista de clientes en el orden de los turnos
        # si el juego ha comenzado
        if self._game is not None:
            # Usar el orden de los turnos del juego (devuelve nombres de jugadores)
            jugadores_orden_nombres = self._game.lista_jugadores_orden_turno()
            # Convertir nombres a objetos Client
            clientes_ordenados: list[Client] = []
            for nombre in jugadores_orden_nombres:
                for client in self._get_clients():
                    if client.username() == nombre:
                        clientes_ordenados.append(client)
                        break
            # Asegurarse de que todos los clientes estén incluidos,
            # incluso si no están en los turnos
            clientes_restantes = [
                c for c in self._get_clients() if c not in clientes_ordenados
            ]
            clientes_ordenados.extend(clientes_restantes)
        else:
            # Si no hay juego, usar el orden original
            clientes_ordenados = self._get_clients()

        # Enviar los colores asignados a todos los clientes
        for client in self._get_clients():
            for otro_client in clientes_ordenados:
                color = otro_client.color_actual()
                if color is not None:
                    client.transmisor.color_asignado(otro_client.userid(), color)

        # Actualizar la lista de jugadores en la interfaz de usuario
        if self._game is not None:
            self._actualizar_lista_jugadores_ui()

    def _actualizar_lista_jugadores_ui(self) -> None:
        """Actualiza la lista de jugadores en la interfaz de usuario.

        Actualiza la lista para todos los clientes.
        """
        if self._game is None:
            return

        # Obtener la lista de jugadores en el orden de los turnos
        jugadores_ordenados = self._game.lista_jugadores_orden_turno()

        # Enviar la lista actualizada a todos los clientes
        for client in self._get_clients():
            # Crear una lista de tuplas (userid, color) en el orden correcto
            jugadores_con_colores = [
                (jugador.userid(), jugador.color_actual())
                for jugador in jugadores_ordenados
                if hasattr(jugador, "userid") and hasattr(jugador, "color_actual")
            ]

            # Enviar la lista de jugadores al cliente
            client.transmisor.actualizar_lista_jugadores(jugadores_con_colores)

    def _enviar_turno_actual(self) -> None:
        """Envía el número de turno y ronda actuales a todos los clientes."""
        if not self._game:
            return

        turno_actual = self._game.id_turno_actual()

        # Obtener información del jugador actual
        jugador_actual_id = None
        jugador_actual_nombre = None
        jugador_actual_color = None

        try:
            turno_obj = self._game.turno_actual()
            if turno_obj and hasattr(turno_obj, "jugador_actual"):
                jugador_nombre = turno_obj.jugador_actual()

                if jugador_nombre:
                    # Buscar el cliente correspondiente al nombre
                    for client in self._get_clients():
                        if client.username() == jugador_nombre:
                            jugador_actual_id = client.userid()
                            jugador_actual_nombre = client.username()
                            color_obj = client.color_actual()
                            jugador_actual_color = (
                                color_obj.to_hex() if color_obj else None
                            )
                            break

        except (AttributeError, KeyError) as e:
            print(f"Error obteniendo información del jugador actual: {e}")

        for client in self._get_clients():
            client.transmisor.enviar_turno(
                turno_actual,
                self._game.num_ronda(),
                jugador_actual_id,
                jugador_actual_nombre,
                jugador_actual_color,
            )

        # Enviar las unidades disponibles al jugador del turno actual
        self._enviar_unidades_disponibles()

        # Enviar el mapa actualizado para actualizar las unidades disponibles
        self._broadcaster.enviar_mapa(self._mapa, self._game)

    def _enviar_unidades_disponibles(self) -> None:
        """Envía las unidades disponibles al jugador del turno actual."""
        if not self._game:
            return

        turno_actual = self._game.turno_actual()
        if not turno_actual:
            return

        jugador_actual = turno_actual.jugador_actual()

        # Crear diccionario con las unidades disponibles
        unidades = {"infanteria": turno_actual.cant_unidades()}

        # Agregar unidades de continentes si existen
        if (
            hasattr(turno_actual, "cant_unidades_africa")
            and turno_actual.cant_unidades_africa() > 0
        ):
            unidades["Africa"] = turno_actual.cant_unidades_africa()
        if (
            hasattr(turno_actual, "cant_unidades_europa")
            and turno_actual.cant_unidades_europa() > 0
        ):
            unidades["Europa"] = turno_actual.cant_unidades_europa()
        if (
            hasattr(turno_actual, "cant_unidades_asia")
            and turno_actual.cant_unidades_asia() > 0
        ):
            unidades["Asia"] = turno_actual.cant_unidades_asia()
        if (
            hasattr(turno_actual, "cant_unidades_sudamerica")
            and turno_actual.cant_unidades_sudamerica() > 0
        ):
            unidades["América del Sur"] = turno_actual.cant_unidades_sudamerica()
        if (
            hasattr(turno_actual, "cant_unidades_norteamerica")
            and turno_actual.cant_unidades_norteamerica() > 0
        ):
            unidades["América del Norte"] = turno_actual.cant_unidades_norteamerica()
        if (
            hasattr(turno_actual, "cant_unidades_oceania")
            and turno_actual.cant_unidades_oceania() > 0
        ):
            unidades["Oceanía"] = turno_actual.cant_unidades_oceania()

        # Enviar solo al jugador del turno actual
        # jugador_actual es un string (nombre),
        # necesitamos encontrar el Client correspondiente
        for client in self._get_clients():
            if client.username() == jugador_actual:
                client.transmisor.enviar_unidades_disponibles(unidades)
                break
