"""Protocolo estructural de la ventana del juego visto por las tareas del cliente.

Permite reemplazar `main_window: GameWindowProtocol` en `IClientTask.run` por
un tipo explícito que documenta el API que las tasks consumen del `Gui`.

Los sub-objetos relevantes (cliente local, paleta de colores, transmisor,
escena, chat, sound manager, etc.) se exponen con tipos concretos. Todos los
imports están en `TYPE_CHECKING` para evitar dependencias pesadas en runtime
y romper ciclos.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

    from PySide6.QtCore import SignalInstance
    from PySide6.QtGui import QColor
    from PySide6.QtWidgets import QStatusBar

    from pyteg.client.app import Client
    from pyteg.client.colores.paleta import Colores
    from pyteg.client.conexion.connection import ConnectionClient
    from pyteg.client.conexion.transmisor.protocol import IClientTransmisor
    from pyteg.client.tasks.types import TarjetaItem
    from pyteg.gui.mapa.scene import QCustomGraphicsScene
    from pyteg.gui.widgets.chat.widget import Chat
    from pyteg.sound_manager import SoundManager


class LobbyWindowProtocol(Protocol):
    """Interfaz mínima de la ventana secundaria (admin / esperar jugadores).

    Es lo que `Gui.w` referencia mientras la partida no comenzó.
    """

    destroyed: SignalInstance

    def cargar_colores_asignados(self) -> None:
        """Refresca la lista de colores en la ventana de lobby."""
        ...

    def close(self) -> bool:
        """Cierra la ventana (heredado de Qt)."""
        ...

    def show(self) -> None:
        """Muestra la ventana (heredado de Qt)."""
        ...

    def deleteLater(self) -> None:  # noqa: N802 (Qt naming)
        """Programa la eliminación diferida (heredado de Qt)."""
        ...


class GameWindowProtocol(Protocol):
    """Interfaz mínima del `Gui` requerida por las tareas del cliente."""

    client: Client
    client_by_id: dict[int, Client]
    colores: Colores
    scene: QCustomGraphicsScene | None
    chat: Chat | None
    conexion: ConnectionClient | None
    w: LobbyWindowProtocol | None
    transmisor: IClientTransmisor
    sound_manager: SoundManager
    status_bar: QStatusBar
    tarjetas_jugador: list[TarjetaItem]
    misiles_habilitados: bool

    def update_unidades_disponibles(self, unidades: dict[str, int]) -> None:
        """Actualiza el panel derecho con las unidades disponibles."""
        ...

    def update_mi_jugador_info(self) -> None:
        """Refresca la información del usuario actual en la barra de estado."""
        ...

    def update_player_list(self, players: Sequence[tuple[str, QColor]]) -> None:
        """Actualiza la lista de jugadores."""
        ...

    def update_game_state(self, estado: str) -> None:
        """Actualiza el estado del juego en la barra de estado."""
        ...

    def update_status_bar(self, text: str, color: str | None = None) -> None:
        """Actualiza la barra de estado con un mensaje (y color opcional)."""
        ...

    def update_timer_display(self, text: str, color: str | None = None) -> None:
        """Actualiza el display del temporizador."""
        ...

    def update_turno(
        self,
        num_turno: int,
        num_ronda: int,
        jugador_actual_id: int | None = None,
        jugador_actual_nombre: str | None = None,
        jugador_actual_color: str | None = None,
    ) -> None:
        """Actualiza el turno y ronda actuales en la interfaz."""
        ...

    def update(self) -> None:
        """Fuerza el repintado de la ventana (heredado de Qt)."""
        ...

    def ventana_admin(self) -> None:
        """Abre la ventana de administración."""
        ...

    def ventana_esperar_jugadores(self) -> None:
        """Abre la ventana de espera de jugadores."""
        ...

    def abrir_ventana_conectar(self) -> None:
        """Abre la ventana de conexión al servidor."""
        ...

    def set_configuracion_partida(
        self,
        segundos_por_turno: int,
        paises_para_victoria: int,
        *,
        objetivos_secretos: bool = False,
        misiles_habilitados: bool = False,
    ) -> None:
        """Establece la configuración de la partida."""
        ...

    def set_objetivo_secreto(
        self, objetivo_id: str | None, descripcion: str | None
    ) -> None:
        """Establece el objetivo secreto del jugador."""
        ...

    def show_battle_result_dialog(
        self,
        batalla_data: dict[str, Any],
        on_finished: Callable[[], None],
    ) -> None:
        """Muestra el diálogo modal con la animación de resultado de batalla."""
        ...

    def refresh_open_tarjetas_dialogs(self, tarjetas: list[TarjetaItem]) -> None:
        """Actualiza los diálogos de tarjetas abiertos."""
        ...
