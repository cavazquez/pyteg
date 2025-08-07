#!/usr/bin/env bash
set -euo pipefail

# make_gif.sh: Convierte una captura a GIF optimizado para README
# Requisitos: ffmpeg (y opcional: gifsicle)
# Uso: ./scripts/make_gif.sh input.mp4 demo.gif [ancho]
# Ejemplo: ./scripts/make_gif.sh input.mp4 docs/media/dice_animation.gif 800

IN=${1:-}
OUT=${2:-}
WIDTH=${3:-800}

if [[ -z "$IN" || -z "$OUT" ]]; then
  echo "Uso: $0 input.mp4 output.gif [ancho]" >&2
  exit 1
fi

mkdir -p "$(dirname "$OUT")"

# Paleta para reducir tamaño con buena calidad
ffmpeg -y -i "$IN" \
  -vf "fps=12,scale=${WIDTH}:-1:flags=lanczos,palettegen=max_colors=64" \
  palette.png

ffmpeg -y -i "$IN" -i palette.png \
  -lavfi "fps=12,scale=${WIDTH}:-1:flags=lanczos[x];[x][1:v]paletteuse=dither=bayer:bayer_scale=5" \
  -loop 0 "$OUT"

# Compresión adicional si está gifsicle
if command -v gifsicle >/dev/null 2>&1; then
  gifsicle -O3 --lossy=80 -o "$OUT" "$OUT"
fi

rm -f palette.png

echo "Listo: $OUT"
