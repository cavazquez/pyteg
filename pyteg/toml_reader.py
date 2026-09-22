"""Módulo para leer y validar archivos TOML del juego."""

from __future__ import annotations

import tomllib
from math import isfinite
from pathlib import Path
from typing import Any

from pyteg.core.mapa.theme_layout import (
    ThemeContinentLayout,
    ThemeCountryLayout,
    ThemeVisualConnection,
)
from pyteg.utils import get_resource_path

_ASSET_EXTENSIONS = {".png", ".svg", ".jpg", ".jpeg"}
_COUNTRY_REQUIRED_FIELDS = ("file", "pos_x", "pos_y", "army_x", "army_y")
_VISUAL_POINT_COORDINATES = 2
_VISUAL_WRAP_POINT_COUNT = 2


class TomlReaderError(Exception):
    """Excepción personalizada para errores de TomlReader."""


class TomlReader:
    """Lector y validador de archivos TOML del juego.

    Raises:
        TomlReaderError: Si el TOML no se puede parsear o la estructura no es válida.

    """

    def __init__(  # noqa: PLR0913
        self,
        paises_toml_string: str,
        cartas_toml_string: str | None = None,
        adyacencias_toml_string: str | None = None,
        objetivos_secretos_toml_string: str | None = None,
        *,
        strict: bool = False,
        theme: str | None = None,
    ) -> None:
        """Inicializa el TomlReader con validación completa de estructura.

        Args:
            paises_toml_string: String con contenido TOML de países y continentes
            cartas_toml_string: String con contenido TOML de cartas (opcional)
            adyacencias_toml_string: String con contenido TOML de adyacencias (opcional)
            objetivos_secretos_toml_string: String con contenido TOML de objetivos
                secretos (opcional)
            strict: Si True, valida campos completos, simetría y assets
            theme: Nombre del tema (para validación de assets en modo strict)

        """
        self.strict = strict
        self.theme = theme
        self.cartas_distribucion: dict[str, dict[str, str]] = {
            "paises": {},
            "continentes": {},
            "especiales": {},
        }
        self._init_load_paises(paises_toml_string)
        self._init_merge_cartas(cartas_toml_string)
        self.adyacencias: dict[str, list[str]] = {}
        self._conexiones_visuales_raw: object = []
        self.conexiones_visuales: list[ThemeVisualConnection] = []
        self._init_merge_adyacencias(adyacencias_toml_string)
        self.objetivos_secretos: dict[str, dict[str, Any]] = {}
        self.objetivos_metadata: dict[str, Any] = {}
        self._init_merge_objetivos_secretos(objetivos_secretos_toml_string)
        self._init_validate_and_build()

    @classmethod
    def from_theme(
        cls,
        theme: str,
        *,
        strict: bool = False,
    ) -> TomlReader:
        """Carga un tema completo desde ``themes/{theme}/``.

        Returns:
            Instancia de TomlReader con los archivos del tema.

        Raises:
            TomlReaderError: Si el tema no existe o los archivos son inválidos.

        """
        theme_dir = get_resource_path(f"themes/{theme}")
        paises_path = theme_dir / "paises.toml"
        if not paises_path.is_file():
            msg = f"Tema '{theme}' no encontrado: falta themes/{theme}/paises.toml"
            raise TomlReaderError(msg)

        paises_content = paises_path.read_text(encoding="utf-8")
        cartas_content = _read_optional_toml(theme_dir / "cartas.toml")
        adyacencias_content = _read_optional_toml(theme_dir / "adyacencias.toml")
        objetivos_content = _read_optional_toml(theme_dir / "objetivos_secretos.toml")

        return cls(
            paises_content,
            cartas_content,
            adyacencias_content,
            objetivos_content,
            strict=strict,
            theme=theme,
        )

    def _init_load_paises(self, paises_toml_string: str) -> None:
        try:
            self.parsed_toml = tomllib.loads(paises_toml_string)
        except tomllib.TOMLDecodeError as e:
            msg = f"Error al parsear TOML de países: {e}"
            raise TomlReaderError(msg) from e

    def _init_merge_cartas(self, cartas_toml_string: str | None) -> None:
        if cartas_toml_string is not None:
            try:
                cartas_parsed = tomllib.loads(cartas_toml_string)
                if "Cartas" not in cartas_parsed:
                    msg = "Archivo de cartas debe contener sección 'Cartas'"
                    raise TomlReaderError(msg)
                self.cartas = cartas_parsed["Cartas"]
                self._cargar_distribucion_cartas(cartas_parsed.get("Distribucion"))
            except tomllib.TOMLDecodeError as e:
                msg = f"Error al parsear TOML de cartas: {e}"
                raise TomlReaderError(msg) from e
        elif "Cartas" in self.parsed_toml:
            self.cartas = self.parsed_toml["Cartas"]
            self._cargar_distribucion_cartas(self.parsed_toml.get("Distribucion"))
        else:
            msg = "No se encontró sección 'Cartas' en ningún archivo"
            raise TomlReaderError(msg)

    def _init_merge_adyacencias(self, adyacencias_toml_string: str | None) -> None:
        if adyacencias_toml_string is not None:
            try:
                adyacencias_parsed = tomllib.loads(adyacencias_toml_string)
                if "Adyacencias" not in adyacencias_parsed:
                    msg = "Archivo de adyacencias debe contener sección 'Adyacencias'"
                    raise TomlReaderError(msg)
                self.adyacencias = adyacencias_parsed["Adyacencias"]
                self._conexiones_visuales_raw = adyacencias_parsed.get(
                    "ConexionesVisuales", []
                )
                self._validar_adyacencias()
            except tomllib.TOMLDecodeError as e:
                msg = f"Error al parsear TOML de adyacencias: {e}"
                raise TomlReaderError(msg) from e
        elif "Adyacencias" in self.parsed_toml:
            self.adyacencias = self.parsed_toml["Adyacencias"]
            self._conexiones_visuales_raw = self.parsed_toml.get(
                "ConexionesVisuales", []
            )
            self._validar_adyacencias()
        elif "ConexionesVisuales" in self.parsed_toml:
            self._conexiones_visuales_raw = self.parsed_toml["ConexionesVisuales"]

    def _init_merge_objetivos_secretos(
        self, objetivos_secretos_toml_string: str | None
    ) -> None:
        if objetivos_secretos_toml_string is None:
            return
        try:
            objetivos_parsed = tomllib.loads(objetivos_secretos_toml_string)
            if "Objetivos" not in objetivos_parsed:
                msg = "Archivo de objetivos secretos debe contener sección 'Objetivos'"
                raise TomlReaderError(msg)
            self.objetivos_secretos = objetivos_parsed["Objetivos"]
            metadata = objetivos_parsed.get("Meta", {})
            if not isinstance(metadata, dict):
                msg = "La sección 'Meta' de objetivos debe ser un diccionario"
                raise TomlReaderError(msg)
            self.objetivos_metadata = metadata
            self._validar_objetivos_secretos()
        except tomllib.TOMLDecodeError as e:
            msg = f"Error al parsear TOML de objetivos secretos: {e}"
            raise TomlReaderError(msg) from e

    def _init_validate_and_build(self) -> None:
        self._validar_estructura_basica()
        self._continentes: dict[str, ThemeContinentLayout] = {}
        self._pais_a_continente: dict[str, str] = {}
        self._validar_cartas()
        self._procesar_continentes_y_paises()
        self._validar_objetivos_metadata_paises()
        self._validar_distribucion_cartas()
        self._validar_nombres_unicos()
        self._validar_consistencia_datos()
        self._validar_conexiones_visuales()
        self._validar_cobertura_adyacencias()
        if self.strict:
            self._validar_campos_pais_completos()
            self._validar_simetria_adyacencias()
            self._validar_assets()

    def _validar_estructura_basica(self) -> None:
        """Valida que existan las secciones básicas requeridas.

        Raises:
            TomlReaderError: Si la estructura básica no es válida

        """
        if not isinstance(self.parsed_toml, dict):
            msg = "El TOML debe ser un diccionario en el nivel raíz"
            raise TomlReaderError(msg)

        continentes_encontrados = [
            key
            for key in self.parsed_toml
            if key
            not in {"Cartas", "Adyacencias", "ConexionesVisuales", "Distribucion"}
            and isinstance(self.parsed_toml[key], dict)
        ]

        if not continentes_encontrados and len(self.parsed_toml) > 1:
            msg = "No se encontraron continentes válidos"
            raise TomlReaderError(msg)

    def _validar_cartas(self) -> None:
        """Valida la estructura de la sección Cartas.

        Raises:
            TomlReaderError: Si la sección Cartas no es válida

        """
        if not isinstance(self.cartas, dict):
            msg = "La sección 'Cartas' debe ser un diccionario"
            raise TomlReaderError(msg)

        for carta, valor in self.cartas.items():
            if not isinstance(valor, str):
                msg = f"La carta '{carta}' debe ser una cadena"
                raise TomlReaderError(msg)

    def _cargar_distribucion_cartas(self, raw: object) -> None:
        """Carga la distribución explícita opcional de cartas del tema.

        Raises:
            TomlReaderError: Si la tabla no tiene la estructura esperada.

        """
        if raw is None:
            return
        if not isinstance(raw, dict):
            msg = "La sección 'Distribucion' debe ser una tabla"
            raise TomlReaderError(msg)
        for categoria in self.cartas_distribucion:
            value = raw.get(categoria, {})
            if not isinstance(value, dict):
                msg = f"Distribucion.{categoria} debe ser una tabla"
                raise TomlReaderError(msg)
            self.cartas_distribucion[categoria] = {
                str(key): str(symbol) for key, symbol in value.items()
            }

    def _validar_distribucion_cartas(self) -> None:  # noqa: C901
        """Valida países, continentes y símbolos de la distribución.

        Raises:
            TomlReaderError: Si falta una carta o se usa un símbolo desconocido.

        """
        distribution = self.cartas_distribucion
        symbols = set(self.cartas)
        for category, entries in distribution.items():
            for card_id, symbol in entries.items():
                if symbol not in symbols:
                    msg = (
                        f"Distribucion.{category}.{card_id} usa símbolo desconocido "
                        f"'{symbol}'"
                    )
                    raise TomlReaderError(msg)
        country_entries = distribution["paises"]
        if country_entries:
            countries = set(self.todos_los_paises())
            missing = countries - set(country_entries)
            unknown = set(country_entries) - countries
            if missing or unknown:
                details = []
                if missing:
                    details.append(f"faltan: {', '.join(sorted(missing))}")
                if unknown:
                    details.append(f"sobran: {', '.join(sorted(unknown))}")
                msg = "Distribución de países incompleta (" + "; ".join(details) + ")"
                raise TomlReaderError(msg)
        continent_entries = distribution["continentes"]
        if continent_entries:
            continents = set(self.get_continentes())
            missing = continents - set(continent_entries)
            unknown = set(continent_entries) - continents
            if missing or unknown:
                details = []
                if missing:
                    details.append(f"faltan: {', '.join(sorted(missing))}")
                if unknown:
                    details.append(f"sobran: {', '.join(sorted(unknown))}")
                msg = (
                    "Distribución de continentes incompleta ("
                    + "; ".join(details)
                    + ")"
                )
                raise TomlReaderError(msg)

    def _validar_adyacencias(self) -> None:
        """Valida la estructura de adyacencias si existe.

        Raises:
            TomlReaderError: Si la estructura de adyacencias no es válida

        """
        if not isinstance(self.adyacencias, dict):
            msg = "La sección 'Adyacencias' debe ser un diccionario"
            raise TomlReaderError(msg)

        for pais, adyacentes in self.adyacencias.items():
            if not isinstance(pais, str):
                msg = f"El nombre del país en adyacencias debe ser string: {pais}"
                raise TomlReaderError(msg)
            if not isinstance(adyacentes, list):
                msg = f"Las adyacencias de '{pais}' deben ser una lista"
                raise TomlReaderError(msg)
            for adyacente in adyacentes:
                if not isinstance(adyacente, str):
                    msg = f"País adyacente debe ser string: {adyacente}"
                    raise TomlReaderError(msg)

    def _validar_objetivos_secretos(  # noqa: C901, PLR0912, PLR0915
        self,
    ) -> None:
        """Valida la estructura de objetivos secretos si existe.

        Raises:
            TomlReaderError: Si la estructura de objetivos secretos no es válida

        """
        if not isinstance(self.objetivos_secretos, dict):
            msg = "La sección 'Objetivos' debe ser un diccionario"
            raise TomlReaderError(msg)

        for objetivo_id, objetivo_data in self.objetivos_secretos.items():
            if not isinstance(objetivo_id, str):
                msg = f"El ID del objetivo debe ser string: {objetivo_id}"
                raise TomlReaderError(msg)

            if not isinstance(objetivo_data, dict):
                msg = f"Los datos del objetivo '{objetivo_id}' deben ser un diccionario"
                raise TomlReaderError(msg)

            if "id" not in objetivo_data:
                msg = f"Objetivo '{objetivo_id}' debe tener campo 'id'"
                raise TomlReaderError(msg)

            if "descripcion" not in objetivo_data:
                msg = f"Objetivo '{objetivo_id}' debe tener campo 'descripcion'"
                raise TomlReaderError(msg)

            if "tipo" not in objetivo_data:
                msg = f"Objetivo '{objetivo_id}' debe tener campo 'tipo'"
                raise TomlReaderError(msg)

            tipos_validos = [
                "destruir_jugador",
                "conquistar_continentes",
                "conquistar_paises",
                "conquistar_paises_con_tropas",
            ]
            if objetivo_data["tipo"] not in tipos_validos:
                msg = (
                    f"Tipo de objetivo '{objetivo_data['tipo']}' no es válido. "
                    f"Tipos válidos: {tipos_validos}"
                )
                raise TomlReaderError(msg)

            if objetivo_data.get("id") != objetivo_id:
                msg = (
                    f"El campo 'id' del objetivo '{objetivo_id}' no coincide "
                    "con su clave"
                )
                raise TomlReaderError(msg)

            descripcion = objetivo_data["descripcion"]
            if not isinstance(descripcion, str) or not descripcion.strip():
                msg = f"La descripción del objetivo '{objetivo_id}' debe ser texto"
                raise TomlReaderError(msg)

            tipo = objetivo_data["tipo"]
            listas = ("continentes",)
            for campo in listas:
                if campo in objetivo_data and not isinstance(
                    objetivo_data[campo], list
                ):
                    msg = (
                        f"El campo '{campo}' del objetivo '{objetivo_id}' debe ser "
                        "una lista"
                    )
                    raise TomlReaderError(msg)
                if campo in objetivo_data and not all(
                    isinstance(valor, str) for valor in objetivo_data[campo]
                ):
                    msg = (
                        f"Los valores de '{campo}' del objetivo '{objetivo_id}' "
                        "deben ser texto"
                    )
                    raise TomlReaderError(msg)

            cuotas = objetivo_data.get("cuotas_continentes")
            if cuotas is not None and (
                not isinstance(cuotas, dict)
                or any(
                    not isinstance(continente, str)
                    or not isinstance(cuota, int)
                    or cuota <= 0
                    for continente, cuota in cuotas.items()
                )
            ):
                msg = (
                    f"'cuotas_continentes' del objetivo '{objetivo_id}' debe "
                    "mapear continentes a enteros positivos"
                )
                raise TomlReaderError(msg)

            for campo in (
                "cantidad_paises",
                "paises_alternativos",
                "tropas_minimas",
                "islas",
                "continentes_minimos_islas",
            ):
                if campo in objetivo_data and (
                    not isinstance(objetivo_data[campo], int)
                    or objetivo_data[campo] <= 0
                ):
                    msg = (
                        f"El campo '{campo}' del objetivo '{objetivo_id}' debe "
                        "ser un entero positivo"
                    )
                    raise TomlReaderError(msg)

            if tipo == "destruir_jugador":
                for campo in ("jugador_alternativo", "objetivo_relativo"):
                    if campo in objetivo_data and objetivo_data[campo] not in {
                        "derecha",
                        "izquierda",
                    }:
                        msg = (
                            f"'{campo}' del objetivo '{objetivo_id}' debe ser "
                            "'derecha' o 'izquierda'"
                        )
                        raise TomlReaderError(msg)

            if "objetivo_comun" in objetivo_data and not isinstance(
                objetivo_data["objetivo_comun"], bool
            ):
                msg = f"'objetivo_comun' del objetivo '{objetivo_id}' debe ser booleano"
                raise TomlReaderError(msg)
            if "publico" in objetivo_data and not isinstance(
                objetivo_data["publico"], bool
            ):
                msg = f"'publico' del objetivo '{objetivo_id}' debe ser booleano"
                raise TomlReaderError(msg)

            if objetivo_data.get("objetivo_comun", False):
                if not objetivo_data.get("publico", False):
                    msg = f"El objetivo común '{objetivo_id}' debe ser público"
                    raise TomlReaderError(msg)
                if tipo != "conquistar_paises":
                    msg = f"El objetivo común '{objetivo_id}' debe conquistar países"
                    raise TomlReaderError(msg)

        objetivos_comunes = [
            objetivo
            for objetivo in self.objetivos_secretos.values()
            if objetivo.get("objetivo_comun", False)
        ]
        if len(objetivos_comunes) > 1:
            msg = "Sólo puede existir un objetivo común por tema"
            raise TomlReaderError(msg)

        if not isinstance(self.objetivos_metadata, dict):
            msg = "La metadata de objetivos debe ser un diccionario"
            raise TomlReaderError(msg)
        islas = self.objetivos_metadata.get("islas", [])
        if not isinstance(islas, list) or not all(
            isinstance(pais, str) for pais in islas
        ):
            msg = "La metadata 'islas' debe ser una lista de nombres de países"
            raise TomlReaderError(msg)

    def _procesar_continentes_y_paises(self) -> None:
        """Procesa continentes y países con validación.

        Raises:
            TomlReaderError: Si hay errores en la estructura de continentes/países

        """
        for continente in self.parsed_toml:
            if continente in {
                "Cartas",
                "Adyacencias",
                "ConexionesVisuales",
                "Distribucion",
            }:
                continue

            if not isinstance(self.parsed_toml[continente], dict):
                continue

            datos = self.parsed_toml[continente].copy()

            if "pos_x" not in datos or "pos_y" not in datos:
                msg = f"Continente '{continente}' debe tener pos_x y pos_y"
                raise TomlReaderError(msg)

            try:
                pos_x = int(datos["pos_x"])
                pos_y = int(datos["pos_y"])
            except (ValueError, TypeError) as e:
                msg = f"Coordenadas del continente '{continente}' deben ser enteros"
                raise TomlReaderError(msg) from e

            paises_continente: dict[str, ThemeCountryLayout] = {}
            for key, value in datos.items():
                if key in {"pos_x", "pos_y"}:
                    continue
                if isinstance(value, dict):
                    self._validar_pais(continente, key, value)
                    if key in self._pais_a_continente:
                        prev = self._pais_a_continente[key]
                        msg = (
                            f"País '{key}' duplicado en continentes "
                            f"'{prev}' y '{continente}'"
                        )
                        raise TomlReaderError(msg)
                    layout = self._build_country_layout(continente, key, value)
                    paises_continente[key] = layout
                    self._pais_a_continente[key] = continente

            self._continentes[continente] = ThemeContinentLayout(
                nombre=continente,
                pos_x=pos_x,
                pos_y=pos_y,
                paises=paises_continente,
            )

    def _validar_objetivos_metadata_paises(self) -> None:
        """Comprueba que la metadata insular sólo mencione países del mapa.

        Raises:
            TomlReaderError: Si una isla no existe en el mapa.

        """
        islas = self.objetivos_metadata.get("islas", [])
        desconocidas = sorted(set(islas) - set(self._pais_a_continente))
        if desconocidas:
            msg = "Países insulares desconocidos en metadata: " + ", ".join(
                desconocidas
            )
            raise TomlReaderError(msg)

    def _build_country_layout(
        self, continente: str, pais: str, datos: dict[str, Any]
    ) -> ThemeCountryLayout:
        declared = datos.get("continente", continente)
        return ThemeCountryLayout(
            nombre=pais,
            continente=str(declared),
            file=str(datos.get("file", "")),
            pos_x=int(datos.get("pos_x", 0)),
            pos_y=int(datos.get("pos_y", 0)),
            army_x=int(datos.get("army_x", 0)),
            army_y=int(datos.get("army_y", 0)),
        )

    def _validar_pais(self, continente: str, pais: str, datos: dict[str, Any]) -> None:
        """Valida la estructura de un país.

        Raises:
            TomlReaderError: Si la estructura del país no es válida

        """
        if "continente" in datos and datos["continente"] != continente:
            msg = (
                f"País '{pais}' declara continente '{datos['continente']}' "
                f"pero está en '{continente}'"
            )
            raise TomlReaderError(msg)

        if "file" in datos and not isinstance(datos["file"], str):
            msg = f"Campo 'file' del país '{pais}' debe ser string"
            raise TomlReaderError(msg)

        campos_numericos = ["pos_x", "pos_y", "army_x", "army_y"]
        for campo in campos_numericos:
            if campo in datos:
                try:
                    int(datos[campo])
                except (ValueError, TypeError) as e:
                    msg = f"Campo '{campo}' del país '{pais}' debe ser entero"
                    raise TomlReaderError(msg) from e

    def _validar_nombres_unicos(self) -> None:
        """Confirma que no hay países duplicados (ya detectados al procesar).

        Raises:
            TomlReaderError: Si hay nombres de país duplicados.

        """
        todos = self.todos_los_paises()
        if len(todos) != len(set(todos)):
            msg = "Hay nombres de país duplicados en el mapa"
            raise TomlReaderError(msg)

    def _validar_consistencia_datos(self) -> None:
        """Valida consistencia entre adyacencias y países existentes.

        Raises:
            TomlReaderError: Si hay inconsistencias en los datos

        """
        todos_paises = set(self.todos_los_paises())

        for pais, adyacentes in self.adyacencias.items():
            if pais not in todos_paises:
                msg = f"País '{pais}' en adyacencias no existe en el mapa"
                raise TomlReaderError(msg)

            for adyacente in adyacentes:
                if adyacente not in todos_paises:
                    msg = (
                        f"País adyacente '{adyacente}' de '{pais}' no existe en el mapa"
                    )
                    raise TomlReaderError(msg)

    def _validar_conexiones_visuales(self) -> None:
        """Valida y construye las conexiones visuales opcionales del tema.

        Las conexiones deben apuntar a países existentes y a una adyacencia
        real. Esto evita que una línea decorativa sugiera una jugada que el
        servidor no permite. La lista no participa en el mapa del dominio.

        Raises:
            TomlReaderError: Si una conexión visual no respeta el esquema.

        """
        raw_connections = self._conexiones_visuales_raw
        if raw_connections is None or raw_connections == []:
            self.conexiones_visuales = []
            return
        if not isinstance(raw_connections, list):
            msg = "La sección 'ConexionesVisuales' debe ser una lista de tablas"
            raise TomlReaderError(msg)

        countries = set(self.todos_los_paises())
        seen: set[frozenset[str]] = set()
        visual_connections: list[ThemeVisualConnection] = []
        for index, raw in enumerate(raw_connections, start=1):
            if not isinstance(raw, dict):
                msg = f"Conexión visual #{index} debe ser una tabla"
                raise TomlReaderError(msg)
            visual_connections.append(
                self._construir_conexion_visual(raw, index, countries, seen)
            )

        self.conexiones_visuales = visual_connections

    def _construir_conexion_visual(
        self,
        raw: dict[str, Any],
        index: int,
        countries: set[str],
        seen: set[frozenset[str]],
    ) -> ThemeVisualConnection:
        origen = raw.get("origen")
        destino = raw.get("destino")
        if not isinstance(origen, str) or not origen:
            msg = f"Conexión visual #{index} debe tener 'origen' string"
            raise TomlReaderError(msg)
        if not isinstance(destino, str) or not destino:
            msg = f"Conexión visual #{index} debe tener 'destino' string"
            raise TomlReaderError(msg)
        if origen == destino:
            msg = f"Conexión visual #{index} no puede unir un país consigo mismo"
            raise TomlReaderError(msg)
        missing = [pais for pais in (origen, destino) if pais not in countries]
        if missing:
            msg = (
                f"Conexión visual #{index} referencia países inexistentes: "
                f"{', '.join(missing)}"
            )
            raise TomlReaderError(msg)

        if self.adyacencias and not (
            destino in self.adyacencias.get(origen, [])
            or origen in self.adyacencias.get(destino, [])
        ):
            msg = (
                f"Conexión visual #{index} no corresponde a una adyacencia: "
                f"'{origen}' - '{destino}'"
            )
            raise TomlReaderError(msg)

        pair = frozenset((origen, destino))
        if pair in seen:
            msg = f"Conexión visual duplicada: '{origen}' - '{destino}'"
            raise TomlReaderError(msg)
        seen.add(pair)

        points = self._validar_puntos_visuales(raw.get("puntos", []), index)
        wrap_mode = self._validar_envolvimiento_visual(
            raw.get("envolver"), points, index
        )
        return ThemeVisualConnection(origen, destino, points, wrap_mode)

    @staticmethod
    def _validar_envolvimiento_visual(
        raw_mode: object,
        points: tuple[tuple[float, float], ...],
        connection_index: int,
    ) -> str | None:
        if raw_mode is None:
            return None
        if not isinstance(raw_mode, str) or raw_mode != "horizontal":
            msg = (
                f"'envolver' en conexión visual #{connection_index} debe ser "
                "'horizontal'"
            )
            raise TomlReaderError(msg)
        if len(points) != _VISUAL_WRAP_POINT_COUNT:
            msg = (
                f"Conexión visual #{connection_index} con envolver horizontal "
                "debe tener dos puntos: salida y reentrada"
            )
            raise TomlReaderError(msg)
        if points[0][0] >= points[1][0]:
            msg = (
                f"Conexión visual #{connection_index} debe declarar primero "
                "el borde izquierdo y luego el derecho"
            )
            raise TomlReaderError(msg)
        return raw_mode

    def _validar_puntos_visuales(
        self, raw_points: object, connection_index: int
    ) -> tuple[tuple[float, float], ...]:
        if not isinstance(raw_points, list):
            msg = f"Puntos de conexión visual #{connection_index} deben ser una lista"
            raise TomlReaderError(msg)

        points: list[tuple[float, float]] = []
        for point_index, point in enumerate(raw_points, start=1):
            if (
                not isinstance(point, list)
                or len(point) != _VISUAL_POINT_COORDINATES
                or any(
                    isinstance(value, bool) or not isinstance(value, int | float)
                    for value in point
                )
            ):
                msg = (
                    f"Punto #{point_index} de conexión visual #{connection_index} "
                    "debe ser [x, y] numérico"
                )
                raise TomlReaderError(msg)
            x, y = float(point[0]), float(point[1])
            if not isfinite(x) or not isfinite(y):
                msg = (
                    f"Punto #{point_index} de conexión visual #{connection_index} "
                    "debe contener coordenadas finitas"
                )
                raise TomlReaderError(msg)
            points.append((x, y))
        return tuple(points)

    def _validar_cobertura_adyacencias(self) -> None:
        """Exige entrada de adyacencias para cada país si la sección existe.

        Raises:
            TomlReaderError: Si falta la entrada de algún país.

        """
        if not self.adyacencias:
            return
        todos_paises = self.todos_los_paises()
        faltantes = [p for p in todos_paises if p not in self.adyacencias]
        if faltantes:
            msg = f"Países sin entrada en adyacencias: {', '.join(sorted(faltantes))}"
            raise TomlReaderError(msg)

    def _validar_simetria_adyacencias(self) -> None:
        """Valida que las adyacencias sean bidireccionales.

        Raises:
            TomlReaderError: Si hay adyacencias asimétricas.

        """
        for pais, adyacentes in self.adyacencias.items():
            for adyacente in adyacentes:
                inversas = self.adyacencias.get(adyacente, [])
                if pais not in inversas:
                    msg = (
                        f"Adyacencia asimétrica: '{pais}' lista '{adyacente}' "
                        f"pero '{adyacente}' no lista '{pais}'"
                    )
                    raise TomlReaderError(msg)

    def _validar_campos_pais_completos(self) -> None:
        """Exige campos obligatorios en cada país.

        Raises:
            TomlReaderError: Si falta algún campo obligatorio.

        """
        for continente in self._continentes.values():
            for pais, layout in continente.paises.items():
                datos_raw = self._country_raw_data(continente.nombre, pais)
                for campo in _COUNTRY_REQUIRED_FIELDS:
                    if campo not in datos_raw:
                        msg = (
                            f"País '{pais}' en '{continente.nombre}' "
                            f"debe tener campo '{campo}'"
                        )
                        raise TomlReaderError(msg)
                if not layout.file:
                    msg = f"País '{pais}' debe tener un archivo de imagen válido"
                    raise TomlReaderError(msg)

    def _country_raw_data(self, continente: str, pais: str) -> dict[str, Any]:
        section = self.parsed_toml.get(continente, {})
        if not isinstance(section, dict):
            return {}
        raw = section.get(pais, {})
        return raw if isinstance(raw, dict) else {}

    def _validar_assets(self) -> None:
        """Valida que los archivos de imagen referenciados existan.

        Raises:
            TomlReaderError: Si falta un asset o la extensión no es válida.

        """
        for layout in self._iter_country_layouts():
            if not layout.file:
                continue
            suffix = Path(layout.file).suffix.lower()
            if suffix not in _ASSET_EXTENSIONS:
                msg = (
                    f"País '{layout.nombre}': extensión '{suffix}' no permitida "
                    f"en '{layout.file}'"
                )
                raise TomlReaderError(msg)
            asset_path = get_resource_path(f"themes/{layout.file}")
            if not asset_path.is_file():
                msg = f"Asset no encontrado para país '{layout.nombre}': {asset_path}"
                raise TomlReaderError(msg)

        for simbolo, rel_path in self.cartas.items():
            asset_path = get_resource_path(f"themes/{rel_path}")
            if not asset_path.is_file():
                msg = f"Asset de carta '{simbolo}' no encontrado: {asset_path}"
                raise TomlReaderError(msg)

    def _iter_country_layouts(self) -> list[ThemeCountryLayout]:
        layouts: list[ThemeCountryLayout] = []
        for continente in self._continentes.values():
            layouts.extend(continente.paises.values())
        return layouts

    def todos_los_paises(self) -> list[str]:
        """Obtiene lista de todos los países en el mapa.

        Returns:
            Lista con nombres de todos los países

        """
        res: list[str] = []
        for continente in self.get_continentes():
            res.extend(self.get_paises(continente))
        return res

    def get_paises(self, continente: str) -> dict[str, ThemeCountryLayout]:
        """Obtiene diccionario de países de un continente.

        Args:
            continente: Nombre del continente

        Returns:
            Diccionario con layouts de países del continente

        """
        return dict(self._continentes[continente].paises)

    def get_pais_layout(self, pais: str) -> ThemeCountryLayout | None:
        """Obtiene el layout de un país.

        Returns:
            Layout del país o None si no existe.

        """
        continente = self.continente(pais)
        if continente is None:
            return None
        return self._continentes[continente].paises.get(pais)

    def get_continentes(self) -> list[str]:
        """Obtiene lista de nombres de continentes.

        Returns:
            Lista con nombres de todos los continentes

        """
        return list(self._continentes)

    def coordenadas_continente(self, continente: str) -> tuple[int, int]:
        """Obtiene coordenadas de posición de un continente.

        Args:
            continente: Nombre del continente

        Returns:
            Tupla (pos_x, pos_y) con coordenadas del continente

        """
        layout = self._continentes[continente]
        return layout.pos_x, layout.pos_y

    def coordenadas(self, pais: str) -> tuple[int, int, int, int]:
        """Obtiene coordenadas completas de un país.

        Args:
            pais: Nombre del país

        Returns:
            Tupla (pos_x, pos_y, army_x, army_y) con coordenadas del país

        Raises:
            TomlReaderError: Si el país no existe o faltan campos con strict=True
            KeyError: Si el país no existe (modo no estricto)

        """
        layout = self.get_pais_layout(pais)
        if layout is None:
            msg = f"País '{pais}' no encontrado"
            if self.strict:
                raise TomlReaderError(msg)
            raise KeyError(msg)
        if self.strict:
            for campo, _valor in (
                ("pos_x", layout.pos_x),
                ("pos_y", layout.pos_y),
                ("army_x", layout.army_x),
                ("army_y", layout.army_y),
            ):
                datos_raw = self._country_raw_data(layout.continente, pais)
                if campo not in datos_raw:
                    msg = f"País '{pais}' no tiene campo '{campo}'"
                    raise TomlReaderError(msg)
        return layout.pos_x, layout.pos_y, layout.army_x, layout.army_y

    def get_cartas(self) -> dict[str, str]:
        """Obtiene diccionario de cartas del juego.

        Returns:
            Diccionario con nombres y archivos de cartas

        """
        return dict(self.cartas)

    def get_simbolos(self) -> list[str]:
        """Obtiene símbolos de cartas en el orden definido en TOML.

        Returns:
            Lista de símbolos de cartas.

        """
        return list(self.cartas.keys())

    def get_cartas_distribucion(self) -> dict[str, dict[str, str]]:
        """Obtiene la distribución explícita de cartas del tema.

        Returns:
            Copia de la distribución por categoría.

        """
        return {
            categoria: dict(entries)
            for categoria, entries in self.cartas_distribucion.items()
        }

    def img_path(self, pais: str) -> str:
        """Obtiene ruta del archivo de imagen de un país.

        Args:
            pais: Nombre del país

        Returns:
            Ruta del archivo de imagen

        Raises:
            TomlReaderError: Si el país no existe o no tiene archivo (strict)
            KeyError: Si el país no existe o no tiene archivo

        """
        layout = self.get_pais_layout(pais)
        if layout is None:
            msg = f"País '{pais}' no encontrado"
            if self.strict:
                raise TomlReaderError(msg)
            raise KeyError(msg)
        if not layout.file:
            msg = f"Ruta de archivo inválida para país '{pais}'"
            if self.strict:
                raise TomlReaderError(msg)
            raise KeyError(msg)
        return layout.file

    def continente(self, pais: str) -> str | None:
        """Obtiene el continente al que pertenece un país.

        Args:
            pais: Nombre del país

        Returns:
            Nombre del continente o None si el país no existe

        """
        return self._pais_a_continente.get(pais)

    def obtener_paises_adyacentes(self, pais: str) -> list[str]:
        """Devuelve la lista de países adyacentes al país especificado.

        Args:
            pais: Nombre del país del que se quieren obtener los adyacentes

        Returns:
            Lista de nombres de países adyacentes,
            o lista vacía si no hay adyacentes definidos

        """
        return list(self.adyacencias.get(pais, []))

    def get_conexiones_visuales(self) -> list[ThemeVisualConnection]:
        """Obtiene las conexiones visuales opcionales definidas por el tema.

        Returns:
            Copia de las conexiones declaradas por el tema.

        """
        return list(self.conexiones_visuales)

    def get_objetivos_secretos(self) -> dict[str, dict[str, Any]]:
        """Obtiene diccionario de objetivos secretos del juego.

        Returns:
            Diccionario con objetivos secretos y sus datos

        """
        return self.objetivos_secretos

    def get_objetivo_secreto(self, objetivo_id: str) -> dict[str, Any] | None:
        """Obtiene los datos de un objetivo secreto específico.

        Args:
            objetivo_id: ID del objetivo secreto

        Returns:
            Diccionario con datos del objetivo o None si no existe

        """
        return self.objetivos_secretos.get(objetivo_id)

    def get_lista_objetivos_secretos(self) -> list[str]:
        """Obtiene lista de IDs de todos los objetivos secretos disponibles.

        Returns:
            Lista con IDs de objetivos secretos

        """
        return list(self.objetivos_secretos.keys())

    def get_objetivos_metadata(self) -> dict[str, Any]:
        """Obtiene metadata pública auxiliar de los objetivos del tema.

        Returns:
            Copia de la metadata declarada en el archivo de objetivos.

        """
        return dict(self.objetivos_metadata)


def _read_optional_toml(path: Path) -> str | None:
    if path.is_file():
        return path.read_text(encoding="utf-8")
    return None
