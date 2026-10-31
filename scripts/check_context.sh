#!/usr/bin/env bash
# Valida struttura, layout del codice e assenza di simulatori.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

required=(
  AGENTS.md
  README.md
  SPEC.md
  docs/VALIDATION.md
  docs/hardware/INVENTORY.md
  docs/hardware/MINIMUM_HARDWARE_DATA.md
  docs/hardware/MINIMUM_HARDWARE_QUESTIONS.md
  docs/hardware/CAD_REFERENCE.md
  docs/hardware/CALIBRATION.md
  docs/hardware/BRINGUP_CHECKLIST.md
  docs/rules/RCJRescueLine2026-final.pdf
  docs/rules/general-rules.pdf
  docs/objectives/DEVELOPMENT_PLAN.md
  docs/architecture/SYSTEM_ARCHITECTURE.md
  docs/architecture/SERIAL_PROTOCOL.md
  docs/testing/FIELD_TEST_PLAN.md
  docs/testing/PROTOCOL_BENCH_TEST.md
  docs/MEASUREMENT_LOG.md
  docs/DECISIONS.md
  docs/SOURCE_MAP.md
  firmware/README.md
  firmware/test/motor_direction_test/motor_direction_test.ino
  firmware/test/motor_direction_test/README.md
  firmware/rcj2027/rcj2027.ino
  firmware/rcj2027/README.md
  software/README.md
  software/requirements.txt
  software/rcj2027/__init__.py
  software/rcj2027/__main__.py
  software/rcj2027/protocol.py
  software/rcj2027/transport.py
  software/rcj2027/logger.py
  software/rcj2027/safety.py
  software/tests/__init__.py
  software/tests/test_protocol.py
  software/tests/test_logger.py
  software/tests/test_safety.py
  software/tests/test_transport.py
  software/tests/test_main.py
  scripts/build.sh
  scripts/test.sh
)

for path in "${required[@]}"; do
  [[ -f "$path" ]] || { echo "missing: $path" >&2; exit 1; }
done

simulator_dir="$(
  find . -type d \
    \( -name simulation -o -name webots \) \
    -not -path './.git/*' -print -quit
)"
if [[ -n "$simulator_dir" ]]; then
  echo "simulator directory not allowed: $simulator_dir" >&2
  exit 1
fi

while IFS= read -r sketch; do
  case "$sketch" in
    ./firmware/*) ;;
    *)
      echo "sketch outside firmware/: $sketch" >&2
      exit 1
      ;;
  esac

  sketch_dir="${sketch%/*}"
  sketch_name="$(basename "$sketch" .ino)"
  if [[ "$(basename "$sketch_dir")" != "$sketch_name" ]]; then
    echo "sketch folder must match file name: $sketch" >&2
    exit 1
  fi
done < <(find . -type f -name '*.ino' -not -path './.git/*' -print)

printf 'context validation: OK (%d required files)\n' "${#required[@]}"
