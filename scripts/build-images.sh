#!/bin/sh
# Convert source screenshots in assets/shots/ into the AVIF and WebP files the
# site serves from static/shots/. Run after adding or replacing a screenshot.
#
# Each source becomes <name>-<width>.avif and <name>-<width>.webp for every
# width in WIDTHS that is smaller than the source; the source width itself is
# always included. It also writes data/shots.json with each image's widths and
# its size at the largest width, so templates can set width and height.
# Requires ImageMagick (magick), avifenc and cwebp.
set -eu

ROOT=$(cd "$(dirname "$0")/.." && pwd)
SRC="$ROOT/assets/shots"
OUT="$ROOT/static/shots"
MANIFEST="$ROOT/data/shots.json"
WIDTHS="640 1280 1600"

for tool in magick avifenc cwebp; do
  command -v "$tool" >/dev/null || { echo "error: $tool not found" >&2; exit 1; }
done

rm -rf "$OUT"
mkdir -p "$OUT"
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
printf '{' > "$tmp/manifest"
sep=""

for src in "$SRC"/*.png "$SRC"/*.webp; do
  [ -e "$src" ] || continue
  name=$(basename "${src%.*}")
  read -r width height <<EOF
$(magick identify -format '%w %h' "$src" 2>/dev/null)
EOF
  sizes=""
  for w in $WIDTHS; do
    [ "$w" -lt "$width" ] && sizes="$sizes $w"
  done
  [ "$width" -le 1600 ] && sizes="$sizes $width"
  for w in $sizes; do
    magick "$src" -resize "${w}x" -strip "$tmp/$name.png" 2>/dev/null
    avifenc --speed 4 --qcolor 62 --yuv 444 "$tmp/$name.png" "$OUT/$name-$w.avif" >/dev/null
    cwebp -quiet -q 82 -m 6 "$tmp/$name.png" -o "$OUT/$name-$w.webp"
  done
  max=${sizes##* }
  printf '%s\n  "%s": {"widths": [%s], "width": %s, "height": %s}' "$sep" "$name" \
    "$(echo $sizes | sed 's/ /, /g')" "$max" "$(( (height * max + width / 2) / width ))" >> "$tmp/manifest"
  sep=","
  echo "$name:$sizes"
done
printf '\n}\n' >> "$tmp/manifest"
mv "$tmp/manifest" "$MANIFEST"
