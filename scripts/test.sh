#!/usr/bin/env bash
# Esegue struttura, build degli sketch e test Python disponibili.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

bash scripts/check_context.sh
bash scripts/build.sh

python_tests="$(find software -type f -name 'test_*.py' -print -quit)"
if [[ -n "$python_tests" ]]; then
  echo "== test Python =="
  python3 -m pytest software
else
  echo "test: nessun test Python in software/"
fi
