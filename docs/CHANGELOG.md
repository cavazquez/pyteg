# CHANGELOG – Pyteg

Todas las fechas en formato YYYY-MM-DD.

## Unreleased
- Documentación centralizada: ARCHITECTURE.md, DECISIONS.md (ADR), CONTRIBUTING.md, CHANGELOG.md.
- README.md actualizado con enlaces a documentación y comandos canon.
 - Diagrama de flujo de mensajes en `docs/diagrams/message_flow.md` y referencia en `docs/ARCHITECTURE.md`.

## 2025-08-07
- Sistema de mensajes de error en chat (tipos: normal, error, system). Ref: 2e82a38.
- Resultado de batalla difundido a clientes (MsgResultadoBatalla). Ref: e1d1709.
- Validación para impedir agregar unidades fuera de turno. Ref: 947060a.
- Envío de unidades disponibles al inicio de turno y tras agregar unidades.
- Toolbar: botones Atacar/Mover según selección y conexión; Finalizar Turno siempre habilitado.
- AttackDialog: tamaño aumentado a 400x280 para mejor UX. Ref: edfc535.
- run_test.sh: agregado mypy con foco en aridad de llamadas.
