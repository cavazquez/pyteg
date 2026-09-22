# ruff: noqa: DOC201, DOC501, D107, TRY003, EM101, PLR0911, PLR0913, PLR0916, PLR2004, FURB171, PLR6201

"""Pactos públicos y bloqueos de TEG La Revancha.

El reglamento deja los pactos a la vista de toda la mesa.  Este módulo guarda
ese estado en el servidor para que las tareas de red no tengan que interpretar
reglas distintas entre sí.  El objeto también sirve como *null object*: en
Classic el gestor existe, pero no hay pactos y todas las consultas son
permisivas.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import TYPE_CHECKING, Literal

from pyteg.exceptions import InvalidActionError

if TYPE_CHECKING:
    from pyteg.server.juego.mapa import Mapa

PactKind = Literal["no_agresion", "agresion"]
PactState = Literal["pendiente", "activo", "ruptura_anunciada", "expirado"]


@dataclass(frozen=True, slots=True)
class Pact:
    """Pacto público entre dos jugadores."""

    id: str
    tipo: PactKind
    jugadores: tuple[int, int]
    ronda_inicio: int
    ronda_hasta: int | None
    paises: tuple[str, ...] = ()
    continentes: tuple[str, ...] = ()
    pais_objetivo: str | None = None
    jugador_objetivo: int | None = None
    estado: PactState = "pendiente"
    roto_por: int | None = None
    automatico: bool = False

    def vigente(self, ronda: int) -> bool:
        """Indica si el pacto está activo en una ronda dada."""
        if self.estado not in {"activo", "ruptura_anunciada"}:
            return False
        return self.ronda_hasta is None or ronda <= self.ronda_hasta

    def public_dict(self) -> dict[str, object]:
        """Serializa únicamente información que conoce toda la mesa."""
        return {
            "id": self.id,
            "tipo": self.tipo,
            "jugadores": list(self.jugadores),
            "ronda_inicio": self.ronda_inicio,
            "ronda_hasta": self.ronda_hasta,
            "paises": list(self.paises),
            "continentes": list(self.continentes),
            "pais_objetivo": self.pais_objetivo,
            "jugador_objetivo": self.jugador_objetivo,
            "estado": self.estado,
            "roto_por": self.roto_por,
            "automatico": self.automatico,
        }


class PactManager:
    """Autoridad única para pactos, rupturas y bloqueos."""

    def __init__(self, mapa: Mapa) -> None:
        self._mapa = mapa
        self._pactos: dict[str, Pact] = {}
        self._next_id = 1

    def reiniciar(self) -> None:
        """Descarta los pactos y bloqueos de una partida anterior."""
        self._pactos.clear()
        self._next_id = 1

    def _new_id(self) -> str:
        pacto_id = f"pacto-{self._next_id}"
        self._next_id += 1
        return pacto_id

    @staticmethod
    def _players(first: int, second: int) -> tuple[int, int]:
        first = int(first)
        second = int(second)
        if first <= 0 or second <= 0 or first == second:
            raise InvalidActionError("Un pacto necesita dos jugadores distintos")
        return first, second

    def proponer(
        self,
        *,
        proponente: int,
        jugador_objetivo: int,
        tipo: str,
        ronda: int,
        paises: tuple[str, ...] = (),
        continentes: tuple[str, ...] = (),
        pais_objetivo: str | None = None,
        duracion: int | None = 1,
    ) -> Pact:
        """Crea una propuesta pendiente, sin activarla unilateralmente."""
        jugadores = self._players(proponente, jugador_objetivo)
        if tipo not in {"no_agresion", "agresion"}:
            raise InvalidActionError("Tipo de pacto no válido")
        paises = tuple(dict.fromkeys(str(pais) for pais in paises if pais))
        continentes = tuple(
            dict.fromkeys(str(continente) for continente in continentes if continente)
        )
        if any(not self._mapa.pais_existe(pais) for pais in paises):
            raise InvalidActionError("El pacto referencia un país inexistente")
        if tipo == "no_agresion" and not paises and not continentes:
            raise InvalidActionError(
                "Un pacto de no agresión debe indicar países o continentes"
            )
        if tipo == "agresion":
            if not pais_objetivo or not self._mapa.pais_existe(pais_objetivo):
                raise InvalidActionError(
                    "Un pacto de agresión debe indicar un país objetivo válido"
                )
            objetivo = self._mapa.ocupado_por(pais_objetivo)
            if objetivo is None or objetivo in jugadores:
                raise InvalidActionError(
                    "El país objetivo debe pertenecer a un tercer jugador"
                )
            if not paises:
                raise InvalidActionError(
                    "El pacto de agresión debe indicar al menos un país agresor"
                )
        if duracion is not None and int(duracion) <= 0:
            raise InvalidActionError("La duración del pacto debe ser positiva")
        hasta = None if duracion is None else int(ronda) + int(duracion) - 1
        pacto = Pact(
            id=self._new_id(),
            tipo=tipo,  # type: ignore[arg-type]
            jugadores=jugadores,
            ronda_inicio=int(ronda),
            ronda_hasta=hasta,
            paises=paises,
            continentes=continentes,
            pais_objetivo=pais_objetivo,
            jugador_objetivo=(
                self._mapa.ocupado_por(pais_objetivo)
                if pais_objetivo is not None
                else None
            ),
        )
        self._pactos[pacto.id] = pacto
        return pacto

    def aceptar(self, pacto_id: str, jugador: int, ronda: int | None = None) -> Pact:
        """Activa una propuesta; sólo el segundo jugador puede aceptarla."""
        pacto = self._get(pacto_id)
        jugador = int(jugador)
        if pacto.estado != "pendiente":
            raise InvalidActionError("El pacto ya no está pendiente")
        if (
            ronda is not None
            and pacto.ronda_hasta is not None
            and int(ronda) > pacto.ronda_hasta
        ):
            raise InvalidActionError("La propuesta de pacto ya expiró")
        if jugador != pacto.jugadores[1]:
            raise InvalidActionError("Sólo el jugador invitado puede aceptar el pacto")
        activo = replace(pacto, estado="activo")
        self._pactos[pacto.id] = activo
        return activo

    def romper(self, pacto_id: str, jugador: int, ronda: int) -> Pact:
        """Anuncia una ruptura que conserva el bloqueo hasta la ronda siguiente."""
        pacto = self._get(pacto_id)
        jugador = int(jugador)
        if jugador not in pacto.jugadores:
            raise InvalidActionError("No participas de este pacto")
        if pacto.estado not in {"activo", "ruptura_anunciada"}:
            raise InvalidActionError("El pacto no está activo")
        hasta = max(int(ronda) + 1, pacto.ronda_hasta or 0)
        roto = replace(
            pacto,
            estado="ruptura_anunciada",
            ronda_hasta=hasta,
            roto_por=jugador,
        )
        self._pactos[pacto.id] = roto
        return roto

    def invalidar_por_conquista(self, pais: str) -> None:
        """Rompe los pactos territoriales cuando un tercero ocupa el país."""
        for pacto_id, pacto in tuple(self._pactos.items()):
            if pais not in pacto.paises and pais != pacto.pais_objetivo:
                continue
            if pacto.automatico:
                del self._pactos[pacto_id]
                continue
            self._pactos[pacto_id] = replace(
                pacto,
                estado="expirado",
                ronda_hasta=pacto.ronda_inicio,
            )

    def expirar(self, ronda: int) -> None:
        """Elimina pacts cuyo plazo ya terminó."""
        ronda = int(ronda)
        for pacto_id, pacto in tuple(self._pactos.items()):
            if pacto.ronda_hasta is not None and ronda > pacto.ronda_hasta:
                del self._pactos[pacto_id]

    def _get(self, pacto_id: str) -> Pact:
        try:
            return self._pactos[str(pacto_id)]
        except KeyError as exc:
            raise InvalidActionError("El pacto no existe") from exc

    def get(self, pacto_id: str) -> Pact | None:
        """Obtiene un pacto para tareas y pruebas."""
        return self._pactos.get(str(pacto_id))

    def pactos(self, *, incluir_expirados: bool = False) -> tuple[Pact, ...]:
        """Devuelve los pactos en orden de creación."""
        values = tuple(self._pactos.values())
        if incluir_expirados:
            return values
        return tuple(pacto for pacto in values if pacto.estado != "expirado")

    def puede_atacar(
        self,
        atacante: int,
        defensor: int | None,
        origen: str,
        destino: str,
        ronda: int,
    ) -> bool:
        """Indica si un pacto público permite la hostilidad solicitada."""
        atacante = int(atacante)
        defensor = None if defensor is None else int(defensor)
        origen_continente = self._mapa.continente(origen)
        destino_continente = self._mapa.continente(destino)
        for pacto in self.pactos():
            if not pacto.vigente(ronda) or defensor is None:
                continue
            if {atacante, defensor} != set(pacto.jugadores):
                continue
            if pacto.tipo == "agresion":
                return False
            if (
                origen in pacto.paises
                or destino in pacto.paises
                or origen_continente in pacto.continentes
                or destino_continente in pacto.continentes
                or origen in (pacto.pais_objetivo,)
                or destino in (pacto.pais_objetivo,)
            ):
                return False
        return True

    def aggression_for_conquest(
        self, atacante: int, defensor: int | None, pais: str, ronda: int
    ) -> Pact | None:
        """Busca el pacto de agresión que habilita un condominio."""
        if defensor is None:
            return None
        for pacto in self.pactos():
            if pacto.tipo != "agresion" or not pacto.vigente(ronda):
                continue
            if pacto.pais_objetivo != pais or pacto.jugador_objetivo != int(defensor):
                continue
            if int(atacante) in pacto.jugadores:
                return pacto
        return None

    def registrar_condominio(
        self, pais: str, jugadores: tuple[int, int], ronda: int
    ) -> Pact:
        """Registra el pacto de no agresión implícito del condominio."""
        pacto = Pact(
            id=self._new_id(),
            tipo="no_agresion",
            jugadores=(int(jugadores[0]), int(jugadores[1])),
            ronda_inicio=int(ronda),
            ronda_hasta=None,
            paises=(pais,),
            estado="activo",
            automatico=True,
        )
        self._pactos[pacto.id] = pacto
        return pacto

    def esta_bloqueado(self, pais: str, jugador: int) -> bool:
        """Calcula el bloqueo de un país según sus países limítrofes."""
        jugador = int(jugador)
        if self._mapa.ocupado_por(pais) != jugador:
            return False
        if self._mapa.cantidad_de_paises_del_jugador(jugador) <= 1:
            return False
        adyacentes = self._mapa.obtener_paises_adyacentes(pais)
        if not adyacentes:
            return False
        bloqueadores = [self._mapa.ocupado_por(vecino) for vecino in adyacentes]
        if not bloqueadores or bloqueadores[0] is None:
            return False
        if any(bloqueador != bloqueadores[0] for bloqueador in bloqueadores):
            return False
        if bloqueadores[0] == jugador:
            return False
        return all(self._mapa.cantidad_unidades(vecino) >= 2 for vecino in adyacentes)

    def bloqueos_publicos(self) -> list[dict[str, int | str]]:
        """Serializa bloqueos vigentes para el snapshot público."""
        resultado: list[dict[str, int | str]] = []
        for pais in self._mapa.paises():
            jugador = self._mapa.ocupado_por(pais)
            if jugador is None or not self.esta_bloqueado(pais, jugador):
                continue
            bloqueador = next(
                (
                    self._mapa.ocupado_por(vecino)
                    for vecino in self._mapa.obtener_paises_adyacentes(pais)
                    if self._mapa.ocupado_por(vecino) is not None
                ),
                None,
            )
            if bloqueador is not None:
                resultado.append({
                    "pais": pais,
                    "jugador": jugador,
                    "bloqueador": bloqueador,
                })
        return resultado

    def public_snapshot(self) -> dict[str, object]:
        """Serializa pactos y bloqueos para todos los clientes."""
        return {
            "pactos": [pacto.public_dict() for pacto in self.pactos()],
            "bloqueos": self.bloqueos_publicos(),
        }
