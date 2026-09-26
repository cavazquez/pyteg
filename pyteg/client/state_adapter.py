"""Adaptador de estado público del modelo compartido hacia la GUI Qt."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from PySide6.QtGui import QColor

from pyteg.gui.managers.players import PlayerStatus

if TYPE_CHECKING:
    from pyteg.client.state_model import ApplyEventResult, ClientStateModel
    from pyteg.gui.managers.protocols import MainWindowProtocol


_MODEL_OWNED_EVENTS = frozenset({
    "snapshot",
    "command_result",
    "hello",
    "hello_ack",
    "pais",
    "misil_agregado",
    "fase",
    "turno",
    "actualizar_lista_jugadores",
    "configuracion_partida",
})


class QtClientStateAdapter:
    """Proyecta ``ClientStateModel`` sobre las superficies visuales de Qt.

    El modelo conserva el estado autoritativo y este adaptador sólo actualiza
    widgets. Los eventos privados (tarjetas, objetivo y unidades propias) siguen
    pasando por sus tareas específicas porque no forman parte del snapshot
    público.
    """

    def __init__(
        self, main_window: MainWindowProtocol, model: ClientStateModel
    ) -> None:
        """Asocia la proyección con la ventana y el modelo compartido."""
        self._main_window = main_window
        self._model = model

    @classmethod
    def handles(cls, kind: object) -> bool:
        """Indica si el modelo ya consumió el estado público del evento.

        Returns:
            ``True`` si el evento se proyecta desde el modelo compartido.

        """
        return isinstance(kind, str) and kind in _MODEL_OWNED_EVENTS

    def apply(self, event: dict[str, Any], result: ApplyEventResult) -> None:
        """Actualiza la GUI después de aplicar un evento al modelo."""
        if not result.applied:
            return
        kind = event.get("mensaje")
        if not self.handles(kind):
            return

        self._main_window.client_state_model = self._model
        self._main_window.client_public_revision = self._model.revision
        self._main_window.client_command_results = self._model.command_results
        if kind == "command_result":
            self._notify_command_result(event)
            return
        if kind in {"hello", "hello_ack"}:
            return
        if not isinstance(kind, str):
            return
        self._apply_owned_event(kind, event)

    def _apply_owned_event(self, kind: str, event: dict[str, Any]) -> None:
        """Despacha la proyección específica sin duplicar estado público."""
        if kind == "snapshot":
            self._sync_public_state()
        elif kind in {"pais", "misil_agregado"}:
            country = event.get("pais")
            names = {country} if isinstance(country, str) else None
            self._sync_countries(self._model.snapshot, names)
        elif kind == "actualizar_lista_jugadores":
            self._sync_players(self._model.snapshot)
        elif kind == "configuracion_partida":
            self._sync_configuration(self._model.snapshot)
        elif kind == "turno":
            self._sync_turn(self._model.snapshot)
        elif kind == "fase":
            self._sync_phase(self._model.snapshot)

    def _notify_command_result(self, event: dict[str, Any]) -> None:
        """Expone confirmaciones correlacionadas sin convertirlas en tareas."""
        callback = getattr(self._main_window, "on_command_result", None)
        if callable(callback):
            callback(event)

    def _sync_public_state(self) -> None:
        """Proyecta el último snapshot completo sobre los widgets disponibles."""
        state = self._model.snapshot
        self._sync_game_state(state)
        self._sync_configuration(state)
        self._sync_players(state)
        self._sync_countries(state)
        self._sync_turn(state)
        self._sync_phase(state)

    def _sync_game_state(self, state: dict[str, Any]) -> None:
        estado = state.get("estado")
        if not isinstance(estado, str) or not estado:
            return
        update = getattr(self._main_window, "update_game_state", None)
        if callable(update):
            update(estado)
        if hasattr(self._main_window, "partida_finalizada"):
            self._main_window.partida_finalizada = estado == "Finalizado"

    def _sync_configuration(self, state: dict[str, Any]) -> None:
        config = state.get("configuracion")
        if not isinstance(config, dict):
            return
        setter = getattr(self._main_window, "set_configuracion_partida", None)
        if not callable(setter):
            return
        segundos = config.get("segundos_por_turno")
        victoria = config.get("paises_para_victoria")
        if not isinstance(segundos, int) or not isinstance(victoria, int):
            return
        setter(
            segundos,
            victoria,
            objetivos_secretos=bool(config.get("objetivos_secretos", False)),
            misiles_habilitados=bool(config.get("misiles_habilitados", False)),
        )
        refresh_actions = getattr(self._main_window, "refresh_gameplay_actions", None)
        if callable(refresh_actions):
            refresh_actions()

    def _sync_players(self, state: dict[str, Any]) -> None:
        players = state.get("players")
        if not isinstance(players, list):
            return
        visible: list[tuple[str, QColor]] = []
        statuses: list[PlayerStatus] = []
        for player in players:
            if not isinstance(player, dict):
                continue
            userid = player.get("userid")
            if not isinstance(userid, int):
                continue
            username = player.get("username") or f"Jugador {userid}"
            color = self._qcolor(player.get("color"))
            username_text = str(username)
            visible.append((username_text, color))
            statuses.append(
                PlayerStatus(
                    username=username_text,
                    connected=bool(player.get("connected", True)),
                    admin=bool(player.get("admin", False)),
                    eliminated=bool(player.get("eliminated", False)),
                )
            )
        update = getattr(self._main_window, "update_player_list", None)
        if callable(update):
            update(visible)
        update_statuses = getattr(self._main_window, "update_player_statuses", None)
        if callable(update_statuses):
            update_statuses(statuses)

    def _sync_countries(
        self, state: dict[str, Any], names: set[str] | None = None
    ) -> None:
        scene = getattr(self._main_window, "scene", None)
        countries = state.get("countries")
        if scene is None or not isinstance(countries, dict):
            return
        colors = {
            player.get("userid"): player.get("color")
            for player in state.get("players", [])
            if isinstance(player, dict)
        }
        names_by_userid = {
            player.get("userid"): str(player.get("username") or player.get("userid"))
            for player in state.get("players", [])
            if isinstance(player, dict)
        }
        for name, raw_country in countries.items():
            if names is not None and name not in names:
                continue
            if not isinstance(name, str) or not isinstance(raw_country, dict):
                continue
            country = getattr(scene, "paises", {}).get(name)
            if country is None:
                continue
            units = raw_country.get("unidades")
            if isinstance(units, int):
                country.set_unidades(units)
            self._sync_country_ownership(country, raw_country, colors, names_by_userid)
            missiles = raw_country.get("misiles")
            update_missiles = getattr(country, "actualizar_misiles", None)
            if isinstance(missiles, int) and callable(update_missiles):
                update_missiles(missiles)

        # Propiedad y unidades también determinan qué acción puede ofrecerse
        # para el par seleccionado; un evento de país puede cambiarlo sin que
        # cambien ni la selección ni el turno.
        selection = getattr(scene, "selection_manager", None)
        refresh_selection = getattr(selection, "refresh_labels", None)
        if callable(refresh_selection):
            refresh_selection()

    def _sync_country_ownership(
        self,
        country: Any,
        raw_country: dict[str, Any],
        colors: dict[Any, Any],
        names_by_userid: dict[Any, str],
    ) -> None:
        """Muestra propietario exclusivo o aportes de los ocupantes compartidos."""
        update_occupants = getattr(country, "actualizar_ocupantes", None)
        occupants = raw_country.get("ocupantes")
        if raw_country.get("compartido") is True and isinstance(occupants, list):
            shared = [
                (
                    names_by_userid.get(item["userid"], str(item["userid"])),
                    item["unidades"],
                    self._qcolor(colors.get(item["userid"])),
                )
                for item in occupants
                if isinstance(item, dict)
                and isinstance(item.get("userid"), int)
                and isinstance(item.get("unidades"), int)
                and item["unidades"] > 0
            ]
            if callable(update_occupants):
                update_occupants(shared)
            return

        if callable(update_occupants):
            update_occupants(None)
        color = colors.get(raw_country.get("userid"))
        country.set_color(
            self._qcolor(color) if color is not None else QColor("#888888")
        )

    def _sync_turn(self, state: dict[str, Any]) -> None:
        turn = state.get("turno")
        if not isinstance(turn, dict):
            return
        num_turno = turn.get("num_turno")
        num_ronda = turn.get("num_ronda")
        jugador_id = turn.get("jugador_id")
        if not isinstance(num_turno, int) or not isinstance(num_ronda, int):
            return
        player = next(
            (
                item
                for item in state.get("players", [])
                if isinstance(item, dict) and item.get("userid") == jugador_id
            ),
            {},
        )
        nombre = turn.get("jugador_nombre") or player.get("username")
        color_data = turn.get("jugador_color") or player.get("color")
        color: str | None = None
        if color_data is not None:
            color = self._qcolor(color_data).name()
        update = getattr(self._main_window, "update_turno", None)
        if callable(update):
            update(
                num_turno,
                num_ronda,
                jugador_id if isinstance(jugador_id, int) else None,
                str(nombre) if nombre is not None else None,
                color,
            )

    def _sync_phase(self, state: dict[str, Any]) -> None:
        fase = state.get("fase")
        if fase is not None and not isinstance(fase, str):
            return
        if hasattr(self._main_window, "fase_actual"):
            self._main_window.fase_actual = fase
        pendientes = state.get("refuerzos_pendientes", 0)
        if isinstance(pendientes, int) and hasattr(
            self._main_window, "unidades_pendientes_servidor"
        ):
            self._main_window.unidades_pendientes_servidor = pendientes
        refresh = getattr(self._main_window, "refresh_gameplay_actions", None)
        if callable(refresh):
            refresh()

    @staticmethod
    def _qcolor(value: object) -> QColor:
        """Convierte el RGB público en un color Qt seguro para la vista.

        Returns:
            Color Qt, o gris neutro cuando falta el RGB.

        """
        if isinstance(value, dict) and all(
            isinstance(value.get(component), int) for component in ("r", "g", "b")
        ):
            return QColor(value["r"], value["g"], value["b"])
        return QColor(200, 200, 200)


__all__ = ["QtClientStateAdapter"]
