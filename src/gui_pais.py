import pathlib

from PySide6.QtCore import QEasingCurve, QPropertyAnimation, Qt, QTimer
from PySide6.QtGui import (
    QColor,
    QFont,
    QPixmap,
)
from PySide6.QtWidgets import (
    QGraphicsColorizeEffect,
    QGraphicsOpacityEffect,
    QGraphicsPixmapItem,
    QGraphicsTextItem,
)

from src.exception import ImagenNoEncontradaError
from src.gui_circulo import Circulo


class Pais(QGraphicsPixmapItem):
    def __init__(self, path, pais, pos):
        # Validar que el archivo de imagen existe
        if not pathlib.Path(path).exists():
            raise ImagenNoEncontradaError(
                path, f"imagen del país {pais[0]} en continente {pais[1]}"
            )

        # Intentar cargar la imagen
        pixmap = QPixmap(path)
        if pixmap.isNull():
            raise ImagenNoEncontradaError(
                path,
                f"la imagen del país {pais[0]} no se pudo cargar (formato inválido)",
            )

        super().__init__(pixmap)
        self._nombre, self._continente = pais
        self._x, self._y, self._army_x, self._army_y = pos
        self.setPos(self._x, self._y)
        self._circle = None
        self._center_text = None
        self._main_window = None

        # Variables para efectos de batalla
        self._titilacion_timer = None
        self._titilacion_effect = None
        self._perdida_flotante = None

        self.cargar_circulo()

    def cargar_circulo(self):
        pos_x_abs = self._army_x
        pos_y_abs = self._army_y
        # (x, y)
        self._circle = Circulo(pos_x_abs, pos_y_abs)
        self._circle.setParentItem(self)

    def nombre(self):
        return self._nombre

    def set_color(self, color):
        if color:
            self._circle.set_color(color)

    def set_unidades(self, cant):
        self._circle.set_unidades(cant)

    def get_unidades(self):
        """Retorna la cantidad de unidades como entero."""
        return self._circle.get_unidades()

    def set_main_window(self, main_window):
        """Establece la referencia a la ventana principal"""
        self._main_window = main_window

    def mousePressEvent(self, event):  # noqa: N802
        """Maneja los clics del mouse en el país"""
        if event.button() == Qt.LeftButton:
            # Clic izquierdo: seleccionar país usando el selection_manager
            if (
                self._main_window
                and hasattr(self._main_window, "scene")
                and hasattr(self._main_window.scene, "selection_manager")
            ):
                self._main_window.scene.selection_manager.seleccionar_pais(self._nombre)
        else:
            # Otros clics (como clic derecho) se manejan normalmente
            super().mousePressEvent(event)

    def set_seleccion_visual(self, tipo):
        """Establece el indicador visual de selección usando oscurecimiento"""
        # Limpiar efecto anterior si existe
        self.limpiar_seleccion_visual()

        # Aplicar efecto de oscurecimiento según el tipo
        if tipo == "origen":
            # Origen: ligeramente más oscuro (opacidad 0.7)
            effect = QGraphicsOpacityEffect()
            effect.setOpacity(0.7)
            self.setGraphicsEffect(effect)
        elif tipo == "destino":
            # Destino: más oscuro (opacidad 0.5)
            effect = QGraphicsOpacityEffect()
            effect.setOpacity(0.5)
            self.setGraphicsEffect(effect)

    def limpiar_seleccion_visual(self):
        """Elimina el indicador visual de selección"""
        if self.graphicsEffect():
            self.setGraphicsEffect(None)

    def iniciar_titilacion_batalla(self):
        """Inicia el efecto de titilación durante una batalla."""
        try:
            # Detener titilación previa si existe
            self.detener_titilacion_batalla()

            # Crear efecto de colorización roja/naranja
            self._titilacion_effect = QGraphicsColorizeEffect()
            self._titilacion_effect.setColor(QColor(255, 100, 100))  # Rojo claro
            self._titilacion_effect.setStrength(0.0)
            self.setGraphicsEffect(self._titilacion_effect)

            # Crear timer para alternar la intensidad
            self._titilacion_timer = QTimer()
            self._titilacion_timer.timeout.connect(self._alternar_titilacion)
            self._titilacion_timer.start(500)  # Cambiar cada 500ms

            # Variable para controlar la dirección del efecto
            self._titilacion_intensidad = 0.0
            self._titilacion_direccion = 1

        except (AttributeError, RuntimeError) as e:
            print(f"Error iniciando titilación en {self._nombre}: {e}")

    def _alternar_titilacion(self):
        """Alterna la intensidad de la titilación."""
        try:
            if self._titilacion_effect:
                # Cambiar intensidad entre 0.0 y 0.7
                self._titilacion_intensidad += 0.35 * self._titilacion_direccion

                if self._titilacion_intensidad >= 0.7:
                    self._titilacion_intensidad = 0.7
                    self._titilacion_direccion = -1
                elif self._titilacion_intensidad <= 0.0:
                    self._titilacion_intensidad = 0.0
                    self._titilacion_direccion = 1

                self._titilacion_effect.setStrength(self._titilacion_intensidad)

        except (AttributeError, RuntimeError) as e:
            print(f"Error en titilación de {self._nombre}: {e}")

    def detener_titilacion_batalla(self):
        """Detiene el efecto de titilación."""
        try:
            if self._titilacion_timer:
                self._titilacion_timer.stop()
                self._titilacion_timer = None

            if self._titilacion_effect:
                self.setGraphicsEffect(None)
                self._titilacion_effect = None

        except (AttributeError, RuntimeError) as e:
            print(f"Error deteniendo titilación en {self._nombre}: {e}")

    def mostrar_perdida_flotante(self, perdidas):
        """Muestra una animación de pérdidas flotantes en rojo."""
        try:
            # Limpiar pérdida flotante anterior si existe
            if self._perdida_flotante:
                if self._perdida_flotante.scene():
                    self._perdida_flotante.scene().removeItem(self._perdida_flotante)
                self._perdida_flotante = None

            # Crear texto flotante
            texto = f"-{perdidas}"
            self._perdida_flotante = QGraphicsTextItem(texto)
            self._perdida_flotante.setParentItem(self)

            # Configurar fuente y color
            font = QFont("Arial", 16, QFont.Bold)
            self._perdida_flotante.setFont(font)
            self._perdida_flotante.setDefaultTextColor(QColor(255, 0, 0))  # Rojo

            # Posicionar sobre el círculo de unidades
            pos_x = self._army_x - 10  # Centrar sobre el círculo
            pos_y = self._army_y - 30  # Arriba del círculo
            self._perdida_flotante.setPos(pos_x, pos_y)

            # Crear animación de desvanecimiento y movimiento hacia arriba
            self._animar_perdida_flotante()

        except (AttributeError, RuntimeError) as e:
            print(f"Error mostrando pérdida flotante en {self._nombre}: {e}")

    def _animar_perdida_flotante(self):
        """Anima la pérdida flotante (movimiento hacia arriba y desvanecimiento)."""
        try:
            if not self._perdida_flotante:
                return

            # Crear efecto de opacidad
            opacity_effect = QGraphicsOpacityEffect()
            self._perdida_flotante.setGraphicsEffect(opacity_effect)

            # Animación de opacidad (desvanecimiento)
            self._opacity_animation = QPropertyAnimation(opacity_effect, b"opacity")
            self._opacity_animation.setDuration(2000)  # 2 segundos
            self._opacity_animation.setStartValue(1.0)
            self._opacity_animation.setEndValue(0.0)
            self._opacity_animation.setEasingCurve(QEasingCurve.OutQuad)

            # Cuando termine la animación, limpiar el texto
            self._opacity_animation.finished.connect(self._limpiar_perdida_flotante)

            # Iniciar animación
            self._opacity_animation.start()

            # Timer para mover hacia arriba gradualmente
            self._movimiento_timer = QTimer()
            self._movimiento_timer.timeout.connect(self._mover_perdida_arriba)
            self._movimiento_timer.start(50)  # Cada 50ms

            # Detener movimiento después de 2 segundos
            QTimer.singleShot(2000, self._detener_movimiento)

        except (AttributeError, RuntimeError) as e:
            print(f"Error animando pérdida flotante en {self._nombre}: {e}")

    def _mover_perdida_arriba(self):
        """Mueve la pérdida flotante hacia arriba gradualmente."""
        try:
            if self._perdida_flotante:
                pos_actual = self._perdida_flotante.pos()
                # Mover 1 pixel arriba
                nueva_pos = pos_actual + self.mapFromScene(0, -1)
                self._perdida_flotante.setPos(nueva_pos.x(), nueva_pos.y())

        except (AttributeError, RuntimeError) as e:
            print(f"Error moviendo pérdida flotante: {e}")

    def _detener_movimiento(self):
        """Detiene el timer de movimiento."""
        try:
            if hasattr(self, "_movimiento_timer") and self._movimiento_timer:
                self._movimiento_timer.stop()
                self._movimiento_timer = None
        except (AttributeError, RuntimeError) as e:
            print(f"Error deteniendo movimiento: {e}")

    def _limpiar_perdida_flotante(self):
        """Limpia la pérdida flotante después de la animación."""
        try:
            if self._perdida_flotante:
                if self._perdida_flotante.scene():
                    self._perdida_flotante.scene().removeItem(self._perdida_flotante)
                self._perdida_flotante = None

        except (AttributeError, RuntimeError) as e:
            print(f"Error limpiando pérdida flotante: {e}")
