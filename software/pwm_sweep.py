"""Sweep PWM di banco, con ruote sollevate e stop tra i gradini.

Questo script muove davvero i motori. Richiede il flag esplicito
``--confirm-wheels-raised`` e usa ``OPERATIONAL_CONFIG`` (pwm_max=255,
watchdog 1.0 s). Non e' un test di missione: serve a trovare il PWM minimo che
muove il robot, a misurare la risposta e a ripetere una coppia di valori.

I valori positivi comandano avanti, quelli negativi indietro: per ripetere il
test a coppia a 255 tre volte usare ``--pwms=255,-255,255,-255,255,-255``.
"""

from __future__ import annotations

import argparse
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from rcj2027.logger import JsonlLogger
from rcj2027.safety import OPERATIONAL_CONFIG, SafetyError
from rcj2027.session import RobotSession, SessionError
from rcj2027.transport import SerialTransport

DEFAULT_PWMS = "150,160,170,180,190,200,210,220,230,240,255"


def _parse_pwms(text: str) -> list[int]:
    values: list[int] = []
    for part in text.split(","):
        part = part.strip()
        if not part:
            continue
        value = int(part)
        if not -255 <= value <= 255:
            raise ValueError(f"PWM fuori range: {value}")
        if value == 0:
            raise ValueError("PWM 0 non e' un gradino; lo stop e' automatico")
        values.append(value)
    if not values:
        raise ValueError("lista PWM vuota")
    return values


def _default_run_id() -> str:
    return datetime.now(timezone.utc).strftime("pwm-sweep-%Y%m%dT%H%M%SZ")


def _hold(session: RobotSession, seconds: float) -> None:
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        session.step(read_timeout_s=0.05)


def run_sweep(
    *,
    port: str,
    baud: int,
    pwms: list[int],
    hold_s: float,
    pause_s: float,
    countdown_s: float,
    logger: JsonlLogger,
) -> None:
    transport = SerialTransport(port=port, baudrate=baud)
    session = RobotSession(transport, logger, config=OPERATIONAL_CONFIG)
    logger.log(
        "session_start",
        mode="pwm-sweep",
        port=port,
        baud=baud,
        pwms=pwms,
        hold_s=hold_s,
        pause_s=pause_s,
        safety=OPERATIONAL_CONFIG.snapshot(),
    )
    try:
        info = session.handshake(boot_delay_s=2.0)
        print(
            f"handshake: protocollo {info.protocol}, scheda {info.board}, "
            f"firmware {info.firmware}"
        )
        if countdown_s:
            print(f"avvio tra {countdown_s:g} s; ruote sollevate")
            _hold(session, countdown_s)
        for pwm in pwms:
            direction = "avanti" if pwm > 0 else "indietro"
            print(
                f"PWM {pwm} ({direction}): {hold_s:g} s",
                flush=True,
            )
            logger.log(
                "pwm_step_start",
                pwm=pwm,
                direction=direction,
                hold_s=hold_s,
            )
            session.drive(pwm, pwm)
            _hold(session, hold_s)
            session.stop()
            logger.log("pwm_step_stop", pwm=pwm, direction=direction)
            if pause_s:
                _hold(session, pause_s)
    finally:
        session.close(reason="pwm_sweep_end")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Sweep PWM a ruote sollevate, con stop tra i gradini."
    )
    parser.add_argument("--port", default="/dev/ttyACM0")
    parser.add_argument("--baud", type=int, default=115200)
    parser.add_argument("--pwms", default=DEFAULT_PWMS)
    parser.add_argument("--hold", type=float, default=4.0)
    parser.add_argument("--pause", type=float, default=2.0)
    parser.add_argument("--countdown", type=float, default=3.0)
    parser.add_argument("--run-id", default=None)
    parser.add_argument("--log-dir", type=Path, default=Path("logs"))
    parser.add_argument(
        "--confirm-wheels-raised",
        action="store_true",
        help="conferma esplicita che le ruote sono sollevate e il robot e' fissato",
    )
    args = parser.parse_args(argv)

    if not args.confirm_wheels_raised:
        print(
            "ERR: richiesto --confirm-wheels-raised; il test muove i motori",
            file=sys.stderr,
        )
        return 2
    if args.hold <= 0 or args.pause < 0 or args.countdown < 0:
        parser.error("hold deve essere positivo; pause/countdown non negativi")
    try:
        pwms = _parse_pwms(args.pwms)
    except ValueError as exc:
        parser.error(str(exc))

    run_id = args.run_id or _default_run_id()
    log_path = args.log_dir / f"{run_id}.jsonl"
    try:
        with JsonlLogger(log_path, run_id) as logger:
            run_sweep(
                port=args.port,
                baud=args.baud,
                pwms=pwms,
                hold_s=args.hold,
                pause_s=args.pause,
                countdown_s=args.countdown,
                logger=logger,
            )
    except (SafetyError, SessionError, RuntimeError, OSError) as exc:
        print(f"ERR {exc}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\ninterrotto", file=sys.stderr)
        return 130

    print(f"log: {log_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
