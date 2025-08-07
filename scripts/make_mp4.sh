#!/usr/bin/env bash
set -euo pipefail

# make_mp4.sh: Convierte una captura a MP4 optimizado para README
# Requisitos: ffmpeg
# Uso: ./scripts/make_mp4.sh input.mp4 demo.mp4 [ancho]
# Ejemplo: ./scripts/make_mp4.sh input.mp4 docs/media/dice_animation.mp4 1280

IN=${1:-}
OUT=${2:-}
WIDTH=${3:-1280}

if [[ -z "$IN" || -z "$OUT" ]]; then
  echo "Uso: $0 input.mp4 output.mp4 [ancho]" >&2
  exit 1
fi

mkdir -p "$(dirname "$OUT")"

ffmpeg -y -i "$IN" \
  -vf "scale=${WIDTH}:-1:flags=lanczos,fps=30" \
  -c:v libx264 -crf 28 -preset veryslow -movflags +faststart -an \
  "$OUT"

echo "Listo: $OUT"
