#!/usr/bin/env bash
# Compila tutti gli sketch Arduino del repository.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

FQBN="${FQBN:-arduino:avr:mega}"

if ! command -v arduino-cli >/dev/null 2>&1; then
  echo "arduino-cli non trovato: installa il toolchain Arduino AVR" >&2
  exit 1
fi

mapfile -t sketches < <(find firmware -type f -name '*.ino' -print | sort)
if [[ ${#sketches[@]} -eq 0 ]]; then
  echo "nessuno sketch in firmware/" >&2
  exit 1
fi

for sketch in "${sketches[@]}"; do
  sketch_dir="$(dirname "$sketch")"
  echo "== build: $sketch_dir (FQBN=$FQBN) =="
  arduino-cli compile --fqbn "$FQBN" "$sketch_dir"
done

printf 'build: OK (%d sketch)\n' "${#sketches[@]}"
