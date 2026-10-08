# Revancha

Este directorio contiene los datos y recursos aislados de Revancha. El inventario
de 72 países y el grafo de 134 aristas parten de la auditoría en
`docs/revancha-map-audit.md`.

`paises.toml` coloca los territorios siguiendo la foto frontal del tablero
compartida para #227. Los SVG son originales del repositorio: las masas
continentales y las particiones de países son aproximaciones vectoriales. El
generador asigna cada píxel de tierra a un solo país, abre una separación entre
países sin adyacencia jugable y coloca el marcador de unidades dentro de la
silueta. Se pueden regenerar con
`python themes/revancha/geometry/generate_revancha_map.py`.

Los nombres tienen un halo claro y se guardan como trazos SVG, para conservar
la forma y el tamaño sin depender de las fuentes instaladas en el cliente.
El generador reserva el área de cada etiqueta y coloca la ficha completa,
incluido su borde, dentro de su país. Jamaica, El Salvador y Portugal usan
etiquetas externas con una línea de referencia. Las costas de Uruguay y Croacia
se ampliaron ligeramente en esta composición aproximada para alojar sus fichas.
Las rutas marítimas se dibujan en azul oscuro detrás de los países y son pasivas.

`tests/test_revancha_visual_layout.py` controla las 72 etiquetas, las fichas,
los clics y el contraste. Para generar capturas con cuatro colores de jugador,
cantidades de uno a tres dígitos, distintos tamaños, zoom y visión simulada:

```bash
QT_QPA_PLATFORM=offscreen python scripts/smoke_visual_map.py \
  --themes classic revancha --sizes 1024x600 1280x800 1920x1080 \
  --output-dir logs/map-visual
QT_QPA_PLATFORM=offscreen python scripts/smoke_visual_map.py \
  --themes revancha --sizes 1024x600 --zooms 0.8 1 1.5 \
  --color-vision normal protanopia deuteranopia tritanopia grayscale \
  --output-dir logs/map-visual/color-vision
```

CI conserva estas capturas como artefactos. La comprobación usa contraste
mínimo 3:1 para las rutas contra los tonos del mar y 4.5:1 para los nombres
contra su halo, también bajo las simulaciones. Las matrices de Machado,
Oliveira y Fernandes se aplican a RGB lineal con severidad 1.0; son una ayuda
de revisión, y la aproximación tritan no representa todos los casos de visión.
Fuentes: [criterio gráfico de W3C](https://www.w3.org/WAI/WCAG22/Understanding/non-text-contrast.html),
[criterio de texto](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html)
y [modelo de simulación](https://profs.ic.uff.br/~laffernandes/content/publications/journal/2009_tvcg_15(6)/machado_oliveira_fernandes-tvcg-15(6)-2009-corrected.pdf).

`adyacencias.toml` conserva el grafo auditado. Las rutas visuales muestran sus
puentes confirmados; no habilitan movimientos. Al seleccionar un país, el mapa
resalta todos sus vecinos jugables y dibuja rutas temporales entre ellos. Esto
permite descubrir también las conexiones que no comparten una frontera en la
composición aproximada. La auditoría de #225 fija Gran Bretaña–Portugal e
Irán–Ucrania; excluye Gran Bretaña–Francia e Irak–Ucrania. El puente atlántico
adoptado para este tema es Uruguay–Nigeria. El fixture registra los motivos y
las fuentes de estas decisiones, y las pruebas comparan todos los países,
continentes y vecinos del tema contra él.
