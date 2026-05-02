"""Módulo de internacionalización (i18n) para PyTeg.

Este módulo proporciona soporte para múltiples idiomas usando gettext.
"""

from __future__ import annotations

import gettext
import locale
import logging
from pathlib import Path
from typing import Protocol

# Directorio base del proyecto
BASE_DIR = Path(__file__).parent.parent
LOCALES_DIR = BASE_DIR / "locales"

# Usamos `logging.getLogger` directamente (no `pyteg.logger.get_logger`) porque
# `i18n` se importa muy temprano y queremos evitar arrastrar la configuración
# completa del logger del proyecto durante la inicialización del módulo.
_LOG = logging.getLogger("i18n")


class _TranslationsProtocol(Protocol):
    def gettext(self, message: str) -> str: ...

    def ngettext(self, singular: str, plural: str, n: int) -> str: ...


_TranslationType = (
    gettext.NullTranslations | gettext.GNUTranslations | _TranslationsProtocol
)


class I18nManager:
    """Gestor de internacionalización usando gettext."""

    def __init__(self) -> None:
        """Inicializa el gestor de internacionalización."""
        self.current_language: str | None = None
        self._translation: _TranslationType | None = None

    def set_language(self, language: str) -> bool:
        """Establece el idioma de la aplicación.

        Returns:
            True si el idioma se estableció correctamente, False en caso contrario.

        """
        try:
            if language not in get_available_languages():
                _LOG.warning(
                    "Idioma '%s' no disponible. Usando español por defecto.",
                    language,
                )
                language = "es"

            # Configurar gettext
            if language == "es":
                # Para español, usar gettext nulo (sin traducción)
                self._translation = gettext.NullTranslations()
            else:
                # Cargar archivo .mo para otros idiomas
                try:
                    self._translation = gettext.translation(
                        "pyteg",
                        localedir=str(LOCALES_DIR),
                        languages=[language],
                        fallback=True,
                    )
                except FileNotFoundError:
                    _LOG.warning(
                        "Archivo de traducción no encontrado para '%s', "
                        "usando fallback",
                        language,
                    )
                    self._translation = gettext.NullTranslations()

            self.current_language = language
            _LOG.info("Idioma establecido: %s", language)

        except (OSError, ValueError):
            _LOG.exception("Error al establecer idioma '%s'", language)
            # Fallback a español
            self._translation = gettext.NullTranslations()
            self.current_language = "es"
            return False
        else:
            return True

    def get_current_language(self) -> str:
        """Retorna el idioma actual.

        Returns:
            Código del idioma actual.

        """
        return self.current_language or "es"

    def translate(self, text: str) -> str:
        """Traduce un texto usando gettext.

        Returns:
            Texto traducido.

        """
        if self._translation is None:
            return text
        return self._translation.gettext(text)

    def ngettext(self, singular: str, plural: str, n: int) -> str:
        """Traduce plurales usando gettext.

        Returns:
            Texto traducido en singular o plural según corresponda.

        """
        if self._translation is None:
            return singular if n == 1 else plural
        return self._translation.ngettext(singular, plural, n)


# Instancia global del gestor
_i18n_manager = I18nManager()


def get_available_languages() -> list[str]:
    """Retorna la lista de idiomas disponibles.

    Returns:
        Lista de códigos de idioma disponibles (ej: ['es', 'en'])

    """
    return ["es", "en"]


def get_system_language() -> str:
    """Detecta el idioma del sistema.

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
    """Establece el idioma de la aplicación.

    Args:
        language: Código de idioma (ej: 'es', 'en')

    Returns:
        True si el idioma se estableció correctamente, False en caso contrario

    """
    return _i18n_manager.set_language(language)


def get_current_language() -> str:
    """Retorna el idioma actual.

    Returns:
        Código del idioma actual

    """
    return _i18n_manager.get_current_language()


def _(text: str) -> str:
    """Función de traducción principal.

    Args:
        text: Texto a traducir

    Returns:
        Texto traducido

    """
    return _i18n_manager.translate(text)


# Alias público para evitar warnings de linting
translate = _


def ngettext(singular: str, plural: str, n: int) -> str:
    """Función de traducción para plurales usando gettext.

    Args:
        singular: Forma singular
        plural: Forma plural
        n: Número para determinar la forma

    Returns:
        Texto traducido en la forma apropiada

    """
    return _i18n_manager.ngettext(singular, plural, n)


# Inicializar con el idioma del sistema
def initialize() -> None:
    """Inicializa el sistema de i18n con el idioma del sistema."""
    system_lang = get_system_language()
    set_language(system_lang)


# Auto-inicializar al importar el módulo
initialize()
