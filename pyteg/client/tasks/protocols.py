"""Protocolo estructural de la ventana del juego visto por las tareas del cliente.

Permite reemplazar `main_window: Any` en `IClientTask.run` por un tipo
explícito que documenta el API que las tasks consumen del `Gui`. Sub-objetos
cuyos tipos requieren imports cruzados con el paquete GUI (scene, chat,
transmisor, client, colores, sound_manager, status_bar, w, conexion) se
exponen como `Any` para evitar dependencias pesadas; `Gui` mantiene los
tipos concretos en su declaración de clase y satisface estructuralmente
este protocolo por duck typing.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

    from PySide6.QtGui import QColor


class GameWindowProtocol(Protocol):
    """Interfaz mínima del `Gui` requerida por las tareas del cliente."""

    client: Any
    client_by_id: dict[int, Any]
    colores: Any
    scene: Any
    chat: Any
    conexion: Any
    w: Any
    transmisor: Any
    sound_manager: Any
    status_bar: Any
    tarjetas_jugador: list[Any]
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

    def refresh_open_tarjetas_dialogs(self, tarjetas: list[Any]) -> None:
        """Actualiza los diálogos de tarjetas abiertos."""
        ...
