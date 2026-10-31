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
  (cd software && python3 -m unittest discover -s tests -t . -v)
else
  echo "test: nessun test Python in software/"
fi
