"""Configuración de partida y objetivos secretos."""

from __future__ import annotations

import json

from pyteg.server.msg.base import IMsg


class MsgConfiguracionPartida(IMsg):
    """Mensaje para enviar la configuración de la partida."""

    def __init__(  # noqa: PLR0913
        self,
        segundos_por_turno: int,
        paises_para_victoria: int,
        *,
        objetivos_secretos: bool = False,
        misiles_habilitados: bool = False,
        rules_profile: str | None = None,
        objective_ids: list[str] | None = None,
        situations_enabled: bool | None = None,
        situation_effects: list[str] | None = None,
        situation_card_ids: list[str] | None = None,
        rule_modules: dict[str, bool] | None = None,
    ) -> None:
        """Inicializa un mensaje con la configuración de la partida.

        Args:
            segundos_por_turno (int): Duración de cada turno en segundos
            paises_para_victoria (int): Número de países necesarios para ganar
            objetivos_secretos (bool): Si los objetivos secretos están activados
            misiles_habilitados (bool): Si el sistema de misiles está habilitado
            rules_profile: Perfil de reglas elegido para la partida.
            objective_ids: IDs de objetivos secretos habilitados.
            situations_enabled: Si se usan cartas de situación.
            situation_effects: Efectos de situación habilitados.
            situation_card_ids: Cartas individuales seleccionadas.
            rule_modules: Módulos de reglas habilitados por nombre.

        """
        self._tipo = "configuracion_partida"
        self._segundos_por_turno = segundos_por_turno
        self._paises_para_victoria = paises_para_victoria
        self._objetivos_secretos = objetivos_secretos
        self._misiles_habilitados = misiles_habilitados
        self._rules_profile = rules_profile
        self._objective_ids = list(objective_ids) if objective_ids is not None else None
        self._situations_enabled = situations_enabled
        self._situation_effects = (
            list(situation_effects) if situation_effects is not None else None
        )
        self._situation_card_ids = (
            list(situation_card_ids) if situation_card_ids is not None else None
        )
        self._rule_modules = dict(rule_modules) if rule_modules is not None else None

    def to_json(self) -> str:
        """Convierte el mensaje a formato JSON.

        Returns:
            Representación JSON del mensaje como cadena.

        """
        data = {
            "mensaje": self._tipo,
            "segundos_por_turno": self._segundos_por_turno,
            "paises_para_victoria": self._paises_para_victoria,
            "objetivos_secretos": self._objetivos_secretos,
            "misiles_habilitados": self._misiles_habilitados,
        }
        if self._rules_profile is not None:
            data["rules_profile"] = self._rules_profile
        if self._objective_ids is not None:
            data["objective_ids"] = self._objective_ids
        if self._situations_enabled is not None:
            data["situations_enabled"] = self._situations_enabled
        if self._situation_effects is not None:
            data["situation_effects"] = self._situation_effects
        if self._situation_card_ids is not None:
            data["situation_card_ids"] = self._situation_card_ids
        if self._rule_modules is not None:
            data["rule_modules"] = self._rule_modules
        return json.dumps(data)


class MsgObjetivoSecreto(IMsg):
    """Mensaje para enviar el objetivo secreto asignado a un jugador."""

    def __init__(self, objetivo_id: str, descripcion: str) -> None:
        """Inicializa un mensaje con el objetivo secreto asignado al jugador.

        Args:
            objetivo_id (str): ID del objetivo secreto
            descripcion (str): Descripción del objetivo secreto

        """
        self._tipo = "objetivo_secreto"
        self._objetivo_id = objetivo_id
        self._descripcion = descripcion

    def to_json(self) -> str:
        """Convierte el mensaje a formato JSON.

        Returns:
            Representación JSON del mensaje como cadena.

        """
        data = {
            "mensaje": self._tipo,
            "objetivo_id": self._objetivo_id,
            "descripcion": self._descripcion,
        }
        return json.dumps(data)
