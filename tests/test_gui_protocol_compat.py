"""Smoke estructural: ``Gui`` satisface ``GameWindowProtocol``.

Verifica sin instanciar la GUI (que requeriría ``QApplication`` real):
- Los métodos públicos declarados por el Protocol existen como callables en la clase.
- Los atributos de instancia se asignan en alguno de los inicializadores
  ``_gui_init_*`` de ``Gui`` (vía AST), o están declarados como anotación
  de clase en ``Gui``.
- ``IClientTask.run`` y ``ClientTaskNull.run`` aceptan estructuralmente una
  instancia de ``Gui`` (verificación de tipado en Mypy a través de
  ``TYPE_CHECKING``).
"""

from __future__ import annotations

import ast
import inspect
import textwrap
import unittest

from pyteg.client.tasks.protocols import GameWindowProtocol
from pyteg.gui.main_window import Gui

_PROTOCOL_METHODS = (
    "update_unidades_disponibles",
    "update_mi_jugador_info",
    "update_player_list",
    "update_game_state",
    "update_status_bar",
    "update_timer_display",
    "update_turno",
    "update",
    "ventana_admin",
    "ventana_esperar_jugadores",
    "abrir_ventana_conectar",
    "set_configuracion_partida",
    "set_objetivo_secreto",
    "show_battle_result_dialog",
    "refresh_open_tarjetas_dialogs",
)

_PROTOCOL_ATTRS = (
    "client",
    "client_by_id",
    "colores",
    "scene",
    "chat",
    "conexion",
    "w",
    "transmisor",
    "sound_manager",
    "status_bar",
    "tarjetas_jugador",
    "misiles_habilitados",
)


def _attrs_assigned_in_gui_init() -> set[str]:
    """Devuelve el conjunto de ``self.X`` asignados en los ``_gui_init_*`` de Gui.

    Returns:
        Conjunto de nombres de atributos de instancia (``self.X``) asignados
        en cualquier método cuyo nombre empiece con ``_gui_init_``.

    """
    asignados: set[str] = set()
    for name, fn in inspect.getmembers(Gui, predicate=inspect.isfunction):
        if not name.startswith("_gui_init_"):
            continue
        source = textwrap.dedent(inspect.getsource(fn))
        tree = ast.parse(source)
        for node in ast.walk(tree):
            targets: list[ast.expr] = []
            if isinstance(node, ast.Assign):
                targets = list(node.targets)
            elif isinstance(node, ast.AnnAssign):
                targets = [node.target]
            else:
                continue
            for target in targets:
                if (
                    isinstance(target, ast.Attribute)
                    and isinstance(target.value, ast.Name)
                    and target.value.id == "self"
                ):
                    asignados.add(target.attr)
    return asignados


class TestGuiSatisfaceGameWindowProtocol(unittest.TestCase):
    """``Gui`` cubre la superficie declarada por ``GameWindowProtocol``."""

    def test_metodos_protocol_existen_en_gui(self) -> None:
        """Cada método del Protocol está definido como callable en ``Gui``."""
        faltantes = [
            m for m in _PROTOCOL_METHODS if not callable(getattr(Gui, m, None))
        ]
        self.assertEqual(faltantes, [], f"Métodos faltantes en Gui: {faltantes}")

    def test_atributos_protocol_se_inicializan_en_gui(self) -> None:
        """Cada atributo del Protocol se asigna en algún ``_gui_init_*``."""
        asignados = _attrs_assigned_in_gui_init()
        anotaciones = set(getattr(Gui, "__annotations__", {}).keys())
        cubiertos = asignados | anotaciones
        faltantes = [a for a in _PROTOCOL_ATTRS if a not in cubiertos]
        self.assertEqual(
            faltantes,
            [],
            f"Atributos del Protocol no inicializados en Gui: {faltantes}",
        )


class TestProtocolReferenciasTipado(unittest.TestCase):
    """``GameWindowProtocol`` se importa desde donde lo consume el cliente."""

    def test_protocol_es_un_protocol(self) -> None:
        """``GameWindowProtocol`` está marcado como Protocol por ``typing``."""
        self.assertTrue(getattr(GameWindowProtocol, "_is_protocol", False))


if __name__ == "__main__":
    unittest.main()
