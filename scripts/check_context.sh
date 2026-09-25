#!/usr/bin/env bash
# Valida la sola struttura documentale del progetto.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

required=(
  AGENTS.md
  README.md
  SPEC.md
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
  docs/MEASUREMENT_LOG.md
  docs/DECISIONS.md
  docs/SOURCE_MAP.md
)

for path in "${required[@]}"; do
  [[ -f "$path" ]] || { echo "missing: $path" >&2; exit 1; }
done

for forbidden_dir in src simulation; do
  [[ ! -d "$forbidden_dir" ]] || {
    echo "legacy directory present: $forbidden_dir" >&2
    exit 1
  }
done

if find . -type f \( -name '*.py' -o -name '*.cpp' -o -name '*.ino' \) -not -path './scripts/*' -print -quit | rg -q .; then
  echo "unexpected application source file in documentation baseline" >&2
  exit 1
fi

printf 'context validation: OK (%d required files)\n' "${#required[@]}"
