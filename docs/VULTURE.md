# Auditoría de código no usado

PyTeg fija `vulture==2.14` en el grupo de dependencias de desarrollo. La
auditoría reproducible es:

```bash
uv run vulture pyteg tests scripts --min-confidence 80 --sort-by-size
```

Con la revisión de septiembre de 2026 no hay hallazgos con confianza 80 o
superior. Ruff, mypy, cobertura y el smoke de Nuitka siguen siendo controles
separados: Vulture sólo busca símbolos que parecen no tener referencias
estáticas.

La salida con confianza 60 contiene falsos positivos esperables:

- `paintEvent`, `wheelEvent`, `closeEvent` y `contextMenuEvent` son callbacks
  descubiertos por Qt, aunque no tengan llamadas Python explícitas.
- `ClientStateModel`, los adaptadores y las constantes de `event_types` forman
  contratos consumidos por reflexión, buses de eventos, protocolos o tests.
- Los atributos de dobles de test y las clases de compatibilidad estructural
  sólo existen para satisfacer interfaces durante una prueba.
- Los entry points, recursos del wheel y módulos referenciados por Nuitka no
  deben eliminarse por una advertencia de Vulture.

Por eso el umbral 80 es bloqueante en CI y el umbral 60 se usa sólo para
revisión manual. No se agrega una whitelist global: mantener el resultado
vacío en alta confianza evita ocultar código nuevo sin uso y deja las
exclusiones explicadas aquí junto a su motivo.
