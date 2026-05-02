"""Tarea del cliente: resultado de batalla (animación y espectadores)."""

from __future__ import annotations

from typing import Any

from PySide6.QtCore import QTimer

from pyteg.client_tasks.base import IClientTask
from pyteg.client_tasks.logging_helper import CLIENT_TASKS_LOG
from pyteg.gui_dice_animation import BattleResultDialog


class ClientTaskResultadoBatalla(IClientTask):
    """Tarea para mostrar el resultado de una batalla."""

    def __init__(self, data: dict[str, Any]) -> None:
        """Inicializa la tarea de resultado de batalla.

        Args:
            data: Diccionario con los datos de la batalla.

        """
        super().__init__(data)
        self._origen = data.get("origen")
        self._destino = data.get("destino")
        self._atacante = data.get("atacante")
        self._defensor = data.get("defensor")
        self._dados_atacante = data.get("dados_atacante", [])
        self._dados_defensor = data.get("dados_defensor", [])
        self._resultado = data.get("resultado", {})
        self._conquistado = data.get("conquistado", False)

    def run(self, main_window: Any) -> None:
        """Muestra el resultado de una batalla.

        Muestra el resultado de una batalla con comportamiento diferenciado:
        - Atacante: Ve animación completa de dados
        - Espectadores: Ven efectos visuales (titilación + pérdidas flotantes).
        """
        try:
            # Obtener nombre del jugador actual
            mi_nombre = None
            if hasattr(main_window, "client") and hasattr(
                main_window.client, "username"
            ):
                mi_nombre = main_window.client.username()

            # Verificar si soy el atacante
            soy_atacante = mi_nombre == self._atacante

            # Reproducir sonido de ataque
            if hasattr(main_window, "sound_manager"):
                main_window.sound_manager.play_attack()

            if soy_atacante:
                # SOY EL ATACANTE: Mostrar animación completa
                self._mostrar_animacion_completa(main_window)
            else:
                # SOY ESPECTADOR: Mostrar efectos visuales
                self._mostrar_efectos_batalla(main_window)

            # Debug info
            CLIENT_TASKS_LOG.debug(
                "Batalla %s -> %s atacante=%s defensor=%s yo=%s "
                "atacante=%s conquistado=%s",
                self._origen,
                self._destino,
                self._atacante,
                self._defensor,
                mi_nombre,
                soy_atacante,
                self._conquistado,
            )

        except (AttributeError, KeyError, ValueError) as e:
            CLIENT_TASKS_LOG.warning("Error al mostrar resultado de batalla: %s", e)
            # Fallback: mostrar mensaje simple en barra de estado
            if hasattr(main_window, "update_status_bar"):
                main_window.update_status_bar(
                    f"Error mostrando batalla: {self._atacante} vs {self._defensor}",
                    "red",
                )

    def _mostrar_animacion_completa(self, main_window: Any) -> None:
        """Muestra la animación completa de dados para el atacante."""
        # Preparar datos de la batalla para el diálogo
        batalla_data = {
            "origen": self._origen,
            "destino": self._destino,
            "atacante": self._atacante,
            "defensor": self._defensor,
            "dados_atacante": self._dados_atacante,
            "dados_defensor": self._dados_defensor,
            "resultado": self._resultado,
            "conquistado": self._conquistado,
        }

        # Mostrar diálogo de animación de dados
        dialog = BattleResultDialog(batalla_data, main_window)

        # Conectar señal para actualizar barra de estado cuando termine
        def on_animation_finished() -> None:
            if self._conquistado:
                mensaje = f"¡Has conquistado {self._destino}!"
                color = "green"
            else:
                mensaje = f"Tu ataque a {self._destino} fue repelido"
                color = "orange"

            if hasattr(main_window, "update_status_bar"):
                main_window.update_status_bar(mensaje, color)

        dialog.animation_finished.connect(on_animation_finished)
        dialog.exec()  # Mostrar diálogo modal

    def _mostrar_efectos_batalla(self, main_window: Any) -> None:
        """Muestra efectos visuales para espectadores (titilación + pérdidas)."""
        try:
            # 1. Iniciar titilación en países origen y destino
            self._iniciar_titilacion_paises(main_window)

            # 2. Mostrar mensaje en barra de estado
            mensaje = f"Batalla: {self._atacante} ataca {self._destino}"
            if hasattr(main_window, "update_status_bar"):
                main_window.update_status_bar(mensaje, "blue")

            # 3. Programar mostrar pérdidas flotantes después de 2.5 segundos
            QTimer.singleShot(
                2500, lambda: self._mostrar_perdidas_flotantes(main_window)
            )

        except (AttributeError, RuntimeError) as e:
            CLIENT_TASKS_LOG.warning("Error mostrando efectos de batalla: %s", e)

    def _iniciar_titilacion_paises(self, main_window: Any) -> None:
        """Inicia la titilación en los países origen y destino."""
        try:
            if hasattr(main_window, "scene") and hasattr(main_window.scene, "paises"):
                # Obtener países origen y destino
                pais_origen = main_window.scene.paises.get(self._origen)
                pais_destino = main_window.scene.paises.get(self._destino)

                # Iniciar titilación si los países existen
                if pais_origen and hasattr(pais_origen, "iniciar_titilacion_batalla"):
                    pais_origen.iniciar_titilacion_batalla()

                if pais_destino and hasattr(pais_destino, "iniciar_titilacion_batalla"):
                    pais_destino.iniciar_titilacion_batalla()

        except (AttributeError, RuntimeError) as e:
            CLIENT_TASKS_LOG.warning("Error iniciando titilación: %s", e)

    def _mostrar_perdidas_flotantes(self, main_window: Any) -> None:
        """Muestra las pérdidas flotantes y detiene la titilación."""
        try:
            # Detener titilación
            self._detener_titilacion_paises(main_window)

            # Calcular pérdidas
            perdedores = self._resultado.get("restar", [])
            perdidas_atacante = perdedores.count(self._atacante)
            perdidas_defensor = perdedores.count(self._defensor)

            # Mostrar pérdidas flotantes
            if perdidas_atacante > 0 and isinstance(self._origen, str):
                self._mostrar_perdida_flotante(
                    main_window, self._origen, perdidas_atacante
                )

            if perdidas_defensor > 0 and isinstance(self._destino, str):
                self._mostrar_perdida_flotante(
                    main_window, self._destino, perdidas_defensor
                )

            # Actualizar barra de estado con resultado final
            if self._conquistado:
                mensaje = f"¡{self._atacante} conquistó {self._destino}!"
                color = "green"
            else:
                mensaje = f"{self._defensor} defendió {self._destino}"
                color = "orange"

            if hasattr(main_window, "update_status_bar"):
                main_window.update_status_bar(mensaje, color)

        except (AttributeError, RuntimeError) as e:
            CLIENT_TASKS_LOG.warning("Error mostrando pérdidas flotantes: %s", e)

    def _detener_titilacion_paises(self, main_window: Any) -> None:
        """Detiene la titilación en los países origen y destino."""
        try:
            if hasattr(main_window, "scene") and hasattr(main_window.scene, "paises"):
                pais_origen = main_window.scene.paises.get(self._origen)
                pais_destino = main_window.scene.paises.get(self._destino)

                if pais_origen and hasattr(pais_origen, "detener_titilacion_batalla"):
                    pais_origen.detener_titilacion_batalla()

                if pais_destino and hasattr(pais_destino, "detener_titilacion_batalla"):
                    pais_destino.detener_titilacion_batalla()

        except (AttributeError, RuntimeError) as e:
            CLIENT_TASKS_LOG.warning("Error deteniendo titilación: %s", e)

    def _mostrar_perdida_flotante(
        self, main_window: Any, nombre_pais: str, perdidas: int
    ) -> None:
        """Muestra una pérdida flotante sobre un país específico."""
        try:
            if hasattr(main_window, "scene") and hasattr(main_window.scene, "paises"):
                pais = main_window.scene.paises.get(nombre_pais)
                if pais and hasattr(pais, "mostrar_perdida_flotante"):
                    pais.mostrar_perdida_flotante(perdidas)

        except (AttributeError, RuntimeError) as e:
            CLIENT_TASKS_LOG.warning("Error mostrando pérdida flotante: %s", e)
