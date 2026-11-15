"""Avvio rapido del line following a bassa velocita' da Thonny.

Apri questo file in Thonny, imposta `CONFIRM_MOTION = True` solo quando il robot
e' sulla linea, le ruote sono libere di muoversi e un operatore puo' fermarlo,
poi premi Run.

La configurazione predefinita e' quella provvisoria di `LOW_SPEED_CONFIG`:
cruise 100, correzione massima 30, limite 130. Non e' tarata sul campo.
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
CONDITION = "linea-bassa-velocita"
DURATION_S = 0.0             # 0 = fino a q/ESC (consigliato)
PREVIEW = True               # finestra locale
HTTP_PORT = 8080             # 0 = stream browser disattivato
DEBUG_OVERLAY = False
SAVE_EVERY = 30
WARMUP_S = 2.0
CAMERA_NUM = 0
SIZE = "1280x720"

DRIVE = True                 # invia i comandi ai motori
CONFIRM_MOTION = False       # metti True solo con robot pronto e operatore presente
PORT = "/dev/ttyACM0"
CRUISE = 100
MAX_CORRECTION = 30
PWM_LIMIT = 130
CONTROL_INTERVAL = 0.1
COUNTDOWN_S = 5.0
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
if DRIVE:
    args.extend(
        [
            "--drive",
            "--confirm-motion",
            "--port",
            PORT,
            "--cruise",
            str(CRUISE),
            "--max-correction",
            str(MAX_CORRECTION),
            "--pwm-limit",
            str(PWM_LIMIT),
            "--control-interval",
            str(CONTROL_INTERVAL),
            "--countdown",
            str(COUNTDOWN_S),
        ]
    )

print(f"prova: {CONDITION}")
print(f"run:   {run_id}")
print(f"log:   {logs_dir}")
print(f"report:{report_path}")
print(f"motori: cruise={CRUISE}, max_correction={MAX_CORRECTION}, pwm_limit={PWM_LIMIT}")
if DRIVE and not CONFIRM_MOTION:
    print(
        "ERR: CONFIRM_MOTION e' False; mettilo a True solo con robot pronto",
        file=sys.stderr,
    )
    raise SystemExit(2)
if DURATION_S <= 0:
    print("premi q o ESC nella finestra per fermare e salvare il report")
if HTTP_PORT:
    print(f"stream: http://<ip-del-raspberry>:{HTTP_PORT}/")

if __name__ == "__main__":
    raise SystemExit(main(args))
