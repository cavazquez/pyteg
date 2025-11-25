from __future__ import annotations

from typing import TYPE_CHECKING

from src.calculos import Calculos

if TYPE_CHECKING:
    from src.server_mapa import Mapa


class SiguientesTurnos:
    def __init__(self, jugador: str, mapa: Mapa) -> None:
        self._jugador = jugador
        self._unidades = Calculos.calcular_unidades_generales(mapa, jugador)
        self._unidades_europa = Calculos.calcular_unidades_europa(mapa, jugador)
        self._unidades_africa = Calculos.calcular_unidades_africa(mapa, jugador)
        self._unidades_sudamerica = Calculos.calcular_unidades_america_del_sur(
            mapa,
            jugador,
        )
        self._unidades_norteamerica = Calculos.calcular_unidades_america_del_norte(
            mapa,
            jugador,
        )
        self._unidades_asia = Calculos.calcular_unidades_asia(mapa, jugador)
        self._unidades_oceania = Calculos.calcular_unidades_oceania(mapa, jugador)

    def jugador_actual(self) -> str:
        return self._jugador

    def agregar_unidades_generales(self, num: int) -> None:
        self._unidades += num

    def usar_unidad(self) -> None:
        self._unidades -= 1

    def usar_unidad_africa(self) -> None:
        self._unidades_africa -= 1

    def usar_unidad_europa(self) -> None:
        self._unidades_europa -= 1

    def usar_unidad_oceania(self) -> None:
        self._unidades_oceania -= 1

    def usar_unidad_asia(self) -> None:
        self._unidades_asia -= 1

    def usar_unidad_sudamerica(self) -> None:
        self._unidades_sudamerica -= 1

    def usar_unidad_norteamerica(self) -> None:
        self._unidades_norteamerica -= 1

    def cant_unidades(self) -> int:
        return self._unidades

    def cant_unidades_africa(self) -> int:
        return self._unidades_africa

    def cant_unidades_europa(self) -> int:
        return self._unidades_europa

    def cant_unidades_oceania(self) -> int:
        return self._unidades_oceania

    def cant_unidades_asia(self) -> int:
        return self._unidades_asia

    def cant_unidades_sudamerica(self) -> int:
        return self._unidades_sudamerica

    def cant_unidades_norteamerica(self) -> int:
        return self._unidades_norteamerica


class SegundoTurno:
    def __init__(self, jugador: str) -> None:
        self._jugador = jugador
        self._unidades = 3

    def jugador_actual(self) -> str:
        return self._jugador

    def usar_unidad(self) -> None:
        self._unidades -= 1

    def cant_unidades(self) -> int:
        return self._unidades

    def agregar_unidades_generales(self, num: int) -> None:
        self._unidades += num


class PrimerTurno:
    def __init__(self, jugador: str) -> None:
        self._jugador = jugador
        self._unidades = 6

    def jugador_actual(self) -> str:
        return self._jugador

    def usar_unidad(self) -> None:
        self._unidades -= 1

    def cant_unidades(self) -> int:
        return self._unidades

    def agregar_unidades_generales(self, num: int) -> None:
        self._unidades += num
