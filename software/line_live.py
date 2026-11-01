"""Avvio rapido di `line-live` da Thonny.

Apri questo file in Thonny, modifica le costanti qui sotto e premi Run.
La finestra mostra il frame annotato: premi `q` o `ESC` per fermare e
salvare il report. Con `DURATION_S = 0` l'acquisizione dura fino a quel tasto.

Non invia comandi ai motori.
"""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from rcj2027.diagnostics import main

# ---------------------------------------------------------------------------
# Configurazione della prova
# ---------------------------------------------------------------------------
CONDITION = "curva"          # es. curva, ombra, gap-05, gap-10, gap-20
DURATION_S = 0.0             # 0 = fino a q/ESC (consigliato)
PREVIEW = True               # finestra locale
HTTP_PORT = 8080             # 0 = stream browser disattivato
DEBUG_OVERLAY = False        # True = mostra anche la maschera di segmentazione
SAVE_EVERY = 30              # salva un frame annotato ogni N frame
WARMUP_S = 2.0
CAMERA_NUM = 0
SIZE = "1280x720"
# ---------------------------------------------------------------------------

run_id = f"f0-{CONDITION}-{datetime.now().strftime('%Y%m%dT%H%M%S')}"
logs_dir = ROOT / "logs" / f"f0-{CONDITION}"
report_path = logs_dir / f"report-{run_id}.json"
annotated_dir = logs_dir / "annotated"

args = [
    "line-live",
    "--camera-num",
    str(CAMERA_NUM),
    "--size",
    SIZE,
    "--warmup",
    str(WARMUP_S),
    "--duration",
    str(DURATION_S),
    "--run-id",
    run_id,
    "--log-dir",
    str(logs_dir),
    "--annotated-dir",
    str(annotated_dir),
    "--save-every",
    str(SAVE_EVERY),
    "--json-out",
    str(report_path),
]
if PREVIEW:
    args.append("--preview")
if DEBUG_OVERLAY:
    args.append("--debug-overlay")
if HTTP_PORT:
    args.extend(["--http-port", str(HTTP_PORT)])

print(f"prova: {CONDITION}")
print(f"run:   {run_id}")
print(f"log:   {logs_dir}")
print(f"report:{report_path}")
if DURATION_S <= 0:
    print("premi q o ESC nella finestra per fermare e salvare il report")
if HTTP_PORT:
    print(f"stream: http://<ip-del-raspberry>:{HTTP_PORT}/")

if __name__ == "__main__":
    raise SystemExit(main(args))
