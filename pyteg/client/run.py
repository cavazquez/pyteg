"""Módulo principal para ejecutar el cliente del juego."""

from __future__ import annotations

import argparse
import sys

from PySide6.QtWidgets import QApplication

from pyteg.client.app import Client
from pyteg.client.logging_setup import configure_client_logging
from pyteg.gui import Gui
from pyteg.log_cli import add_log_arguments
from pyteg.version import NAME, VERSION


def parse_arguments() -> tuple[argparse.Namespace, list[str]]:
    """Parsea argumentos CLI del cliente, dejando flags desconocidos para Qt.

    Returns:
        Par (argumentos PyTeg, argumentos restantes para ``QApplication``).

    """
    parser = argparse.ArgumentParser(description="Cliente del juego de estrategia TEG.")
    add_log_arguments(
        parser,
        verbose_help="Nivel DEBUG en consola (conexión, mensajes, tareas)",
    )
    return parser.parse_known_args()


def main() -> None:
    """Función principal que inicia el cliente del juego."""
    args, qt_argv = parse_arguments()
    logger = configure_client_logging(args)

    logger.info("%s v%s", NAME, VERSION)
    if args.verbose:
        logger.debug("Modo verboso: conexión y tareas del cliente en consola")
    elif args.quiet:
        logger.debug("Modo silencioso: solo errores en consola")

    client = Client()
    app = QApplication([sys.argv[0], *qt_argv])
    gui = Gui(client)

    gui.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
