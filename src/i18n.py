"""
Módulo de internacionalización (i18n) para PyTeg.

Este módulo proporciona soporte básico para múltiples idiomas.
"""

import locale
from pathlib import Path

# Directorio base del proyecto
BASE_DIR = Path(__file__).parent.parent


class I18nManager:
    """Gestor de internacionalización para evitar variables globales."""

    def __init__(self):
        self.current_language: str | None = None
        self.translations: dict[str, str] = {}

    def set_language(self, language: str) -> bool:
        """Establece el idioma de la aplicación."""
        try:
            if language not in get_available_languages():
                print(f"Idioma '{language}' no disponible. Usando español por defecto.")
                language = "es"

            # Cargar traducciones
            self.translations = (
                {} if language == "es" else TRANSLATIONS.get(language, {})
            )
            self.current_language = language
            print(f"Idioma establecido: {language}")
        except (KeyError, TypeError, ValueError) as e:
            print(f"Error al establecer idioma '{language}': {e}")
            # Fallback a español
            self.current_language = "es"
            self.translations = {}
            return False
        else:
            return True

    def get_current_language(self) -> str:
        """Retorna el idioma actual."""
        return self.current_language or "es"

    def translate(self, text: str) -> str:
        """Traduce un texto."""
        return self.translations.get(text, text)


# Instancia global del gestor
_i18n_manager = I18nManager()


# Traducciones hardcodeadas para evitar problemas de archivos
TRANSLATIONS = {
    "en": {
        "PyTeg": "PyTeg",
        "Mi jugador:": "My player:",
        "[No conectado]": "[Not connected]",
        "Estado: Desconectado": "Status: Disconnected",
        "Selección: Ninguna": "Selection: None",
        "Configuración de la Partida": "Game Configuration",
        "Duración del turno:": "Turn duration:",
        "{} segundos": "{} seconds",
        "Países para ganar:": "Countries to win:",
        "Todos los países": "All countries",
        "Cerrar": "Close",
        "Idioma:": "Language:",
        "Conectar": "Connect",
        "Atacar": "Attack",
        "Mover": "Move",
        "Finalizar Turno": "End Turn",
        "Admin": "Admin",
        "Configuración": "Configuration",
        "Error": "Error",
        "Ha ocurrido un error.": "An error has occurred.",
        "Nombre de usuario duplicado": "Duplicate username",
        "El nombre de usuario que elegiste ya está en uso.": (
            "The username you chose is already in use."
        ),
        "Por favor, elige un nombre de usuario diferente.": (
            "Please choose a different username."
        ),
        "¡Partida Terminada!": "Game Over!",
        "🏆 ¡Felicitaciones!": "🏆 Congratulations!",
        "Advertencia": "Warning",
        "conexión rehusada.": "connection refused.",
        "Esperando jugadores": "Waiting for players",
        "Estado: {}": "Status: {}",
        "[Error]": "[Error]",
        "Seleccionar Unidades de Ataque": "Select Attack Units",
        "Resultado de Batalla": "Battle Result",
        "Lanzando...": "Rolling...",
        "Generales": "Generals",
        "Misiles": "Missiles",
        "Ronda: {} - Turno: {}": "Round: {} - Turn: {}",
        "Turno {} iniciado": "Turn {} started",
        "Tiempo restante: {}s": "Time remaining: {}s",
        "Objetivo: {} | Turno: {}s": "Objective: {} | Turn: {}s",
        # Toolbar translations
        "Conectar al servidor": "Connect to server",
        "Abrir ventana de conexión": "Open connection window",
        "Atacar país seleccionado": "Attack selected country",
        "Ejecutar ataque entre países seleccionados": (
            "Execute attack between selected countries"
        ),
        "Mover unidades entre países": "Move units between countries",
        "Mover 1 unidad entre los países seleccionados": (
            "Move 1 unit between selected countries"
        ),
        "Finalizar tu turno actual": "End your current turn",
        "Pasar el turno al siguiente jugador": "Pass turn to next player",
        "Ver configuración de la partida": "View game configuration",
        "Mostrar duración de turno y objetivo de países": (
            "Show turn duration and country objective"
        ),
        "Pantalla Completa": "Full Screen",
        "Alternar pantalla completa": "Toggle full screen",
        "Entrar/salir de pantalla completa": "Enter/exit full screen",
        "Tamaños predefinidos": "Predefined sizes",
        "Tamaño personalizado": "Custom size",
        "Pequeño (800x600)": "Small (800x600)",
        "Mediano (1024x768)": "Medium (1024x768)",
        "Grande (1280x800)": "Large (1280x800)",
    }
}


def get_available_languages() -> list[str]:
    """
    Retorna la lista de idiomas disponibles.

    Returns:
        Lista de códigos de idioma disponibles (ej: ['es', 'en'])
    """
    return ["es", "en"]


def get_system_language() -> str:
    """
    Detecta el idioma del sistema.

    Returns:
        Código de idioma del sistema o 'es' por defecto
    """
    try:
        # Intentar obtener el idioma del sistema
        system_locale = locale.getdefaultlocale()[0]
        if system_locale:
            # Extraer solo el código de idioma (ej: 'es_ES' -> 'es')
            lang_code = system_locale.split("_")[0].lower()

            # Verificar si el idioma está disponible
            available_languages = get_available_languages()
            if lang_code in available_languages:
                return lang_code
    except (OSError, ValueError, TypeError):
        # Manejar errores específicos de locale
        pass

    # Idioma por defecto
    return "es"


def set_language(language: str) -> bool:
    """
    Establece el idioma de la aplicación.

    Args:
        language: Código de idioma (ej: 'es', 'en')

    Returns:
        True si el idioma se estableció correctamente, False en caso contrario
    """
    return _i18n_manager.set_language(language)


def get_current_language() -> str:
    """
    Retorna el idioma actual.

    Returns:
        Código del idioma actual
    """
    return _i18n_manager.get_current_language()


def _(text: str) -> str:
    """
    Función de traducción principal.

    Args:
        text: Texto a traducir

    Returns:
        Texto traducido
    """
    return _i18n_manager.translate(text)


# Alias público para evitar warnings de linting
translate = _


def ngettext(singular: str, plural: str, n: int) -> str:
    """
    Función de traducción para plurales.

    Args:
        singular: Forma singular
        plural: Forma plural
        n: Número para determinar la forma

    Returns:
        Texto traducido en la forma apropiada
    """
    base_text = singular if n == 1 else plural
    return _i18n_manager.translate(base_text)


# Inicializar con el idioma del sistema
def initialize():
    """Inicializa el sistema de i18n con el idioma del sistema."""
    system_lang = get_system_language()
    set_language(system_lang)


# Auto-inicializar al importar el módulo
initialize()
