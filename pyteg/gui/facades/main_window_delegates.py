"""Mixin con delegaciones públicas de `Gui` hacia managers especializados."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

    from PySide6.QtGui import QCloseEvent, QColor, QKeyEvent

    from pyteg.client.tasks.types import TarjetaItem
    from pyteg.gui.managers.cards import CardManager
    from pyteg.gui.managers.config import ConfigManager
    from pyteg.gui.managers.game_actions import GameActionsManager
    from pyteg.gui.managers.players import PlayersManager
    from pyteg.gui.managers.status import StatusManager
    from pyteg.gui.managers.units import UnitsManager
    from pyteg.gui.managers.window import WindowManager
    from pyteg.gui.mapa.scene import QCustomGraphicsScene
    from pyteg.gui.widgets.chat import Chat
    from pyteg.sound_manager import SoundManager


class MainWindowDelegatesMixin:
    """Delega la API pública de la ventana principal a managers."""

    players_manager: PlayersManager
    status_manager: StatusManager
    units_manager: UnitsManager
    game_actions_manager: GameActionsManager
    config_manager: ConfigManager
    card_manager: CardManager
    window_manager: WindowManager
    sound_manager: SoundManager
    scene: QCustomGraphicsScene | None
    chat: Chat | None
    misiles_habilitados: bool
    tarjetas_jugador: list[TarjetaItem]
    _vivo: bool

    def update_player_list(self, players: Sequence[tuple[str, QColor]]) -> None:
        """Actualiza la lista de jugadores en el panel lateral."""
        self.players_manager.update_player_list(players)

    def abrir_ventana_conectar(self) -> None:
        """Abre la ventana de conexión al servidor."""
        self.window_manager.abrir_ventana_conectar()

    def ventana_admin(self) -> None:
        """Abre la ventana de administración."""
        self.window_manager.ventana_admin()

    def ventana_esperar_jugadores(self) -> None:
        """Abre la ventana de espera de jugadores."""
        self.window_manager.ventana_esperar_jugadores()

    def update_turno(
        self,
        num_turno: int,
        num_ronda: int,
        jugador_actual_id: int | None = None,
        jugador_actual_nombre: str | None = None,
        jugador_actual_color: str | None = None,
    ) -> None:
        """Actualiza turno, ronda y jugador activo en la barra de estado."""
        self.status_manager.update_turno(
            num_turno,
            num_ronda,
            jugador_actual_id,
            jugador_actual_nombre,
            jugador_actual_color,
        )

    def update_status_bar(self, text: str, color: str | None = None) -> None:
        """Muestra un mensaje en la barra de estado."""
        self.status_manager.update_status_bar(text, color)

    def update_timer_display(self, text: str, color: str | None = None) -> None:
        """Actualiza el temporizador en la barra de estado."""
        self.status_manager.update_timer_display(text, color)

    def clear_status_bar(self) -> None:
        """Limpia el mensaje temporal de la barra de estado."""
        self.status_manager.clear_status_bar()

    def update_game_state(self, estado: str) -> None:
        """Actualiza el estado del juego en la barra de estado."""
        self.status_manager.update_game_state(estado)

    def update_mi_jugador_info(self) -> None:
        """Refresca nombre y color del jugador local."""
        self.status_manager.update_mi_jugador_info()

    def update_unidades_disponibles(self, unidades: dict[str, int]) -> None:
        """Actualiza el panel de unidades disponibles."""
        self.units_manager.update_unidades_disponibles(unidades)

    def finalizar_turno(self) -> None:
        """Finaliza el turno actual vía transmisor."""
        self.game_actions_manager.finalizar_turno()

    def atacar(self) -> None:
        """Inicia flujo de ataque desde la toolbar."""
        self.game_actions_manager.atacar()

    def mover(self) -> None:
        """Inicia flujo de movimiento desde toolbar o menú contextual."""
        self.game_actions_manager.mover()

    def get_max_attack_units(self, pais: str) -> int:
        """Máximo de unidades atacantes desde un país.

        Returns:
            Cantidad máxima de unidades que pueden atacar (1-3).

        """
        return self.game_actions_manager.get_max_attack_units(pais)

    def canjear_misil(self, pais: str) -> None:
        """Canjea unidades por un misil en el país indicado."""
        self.game_actions_manager.canjear_misil(pais)

    def colocar_unidad_en_pais(self, pais: str, continente_mapa: str) -> None:
        """Coloca unidades en un país del mapa."""
        self.game_actions_manager.colocar_unidad_en_pais(pais, continente_mapa)

    def lanzar_misil(self, pais_origen: str, pais_destino: str) -> None:
        """Lanza un misil entre dos países."""
        self.game_actions_manager.lanzar_misil(pais_origen, pais_destino)

    def set_configuracion_partida(
        self,
        segundos_por_turno: int,
        paises_para_victoria: int,
        *,
        objetivos_secretos: bool = False,
        misiles_habilitados: bool = False,
    ) -> None:
        """Guarda la configuración de partida recibida del servidor."""
        self.config_manager.set_configuracion_partida(
            segundos_por_turno,
            paises_para_victoria,
            objetivos_secretos=objetivos_secretos,
            misiles_habilitados=misiles_habilitados,
        )
        self.misiles_habilitados = misiles_habilitados

    def mostrar_configuracion_partida(self) -> None:
        """Abre el diálogo de configuración de partida."""
        self.config_manager.mostrar_configuracion_partida()

    def set_objetivo_secreto(
        self, objetivo_id: str | None, descripcion: str | None
    ) -> None:
        """Almacena el objetivo secreto del jugador local."""
        self.config_manager.set_objetivo_secreto(objetivo_id, descripcion)

    def mostrar_tarjetas(self) -> None:
        """Abre el diálogo de tarjetas del jugador."""
        self.card_manager.mostrar_tarjetas()

    def show_battle_result_dialog(
        self,
        batalla_data: dict[str, Any],
        on_finished: Callable[[], None],
    ) -> None:
        """Muestra la animación de resultado de batalla."""
        self.window_manager.show_battle_result_dialog(batalla_data, on_finished)

    def refresh_open_tarjetas_dialogs(self, tarjetas: list[Any]) -> None:
        """Actualiza diálogos de tarjetas abiertos."""
        self.card_manager.refresh_open_tarjetas_dialogs(tarjetas)

    def keyPressEvent(self, event: QKeyEvent) -> None:  # noqa: N802
        """Atajos de teclado: Enter en chat, Escape cancela selección."""
        from PySide6.QtCore import Qt  # noqa: PLC0415

        if event.key() in {Qt.Key.Key_Enter, Qt.Key.Key_Return} and self.chat:
            self.chat.send_message()
        elif (
            event.key() == Qt.Key.Key_Escape
            and self.scene
            and hasattr(self.scene, "selection_manager")
        ):
            self.scene.selection_manager.cancelar_seleccion()

    def closeEvent(self, _: QCloseEvent) -> None:  # noqa: N802
        """Libera recursos al cerrar la ventana."""
        self._vivo = False
        self.sound_manager.cleanup()
