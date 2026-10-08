# Licencia y procedencia de los assets

Los SVG de `countries/`, `cards/` y `geometry/` se generan para este
repositorio y se distribuyen bajo GPL-3.0-or-later (`LICENSE`). La composición
vectorial del mapa usa como guía la foto frontal del tablero compartida para
#227. Sus masas continentales y fronteras son aproximaciones vectoriales
realizadas para este repositorio.

`geometry/board-layout.toml` contiene los contornos y centros de referencia.
`geometry/generate_revancha_map.py` regenera los SVG, las posiciones de
`paises.toml` y las rutas visuales permanentes. Su partición de píxeles evita
solapes y abre una separación
visible cuando dos países cercanos no son adyacentes en las reglas. Los contornos
y la costa siguen siendo aproximados. La geometría de presentación se mantiene
separada del grafo ejecutable: las rutas y los resaltados solo representan
aristas auditadas y no habilitan movimientos. Las decisiones sobre las fuentes
del tablero están registradas en `docs/revancha-map-audit.md` y en el fixture;
no se incluyen fotografías, logotipos ni documentos comerciales como assets.
