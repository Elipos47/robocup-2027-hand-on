"""Demo del livello di comunicazione e logging, senza movimento reale."""

from __future__ import annotations

import argparse
import time
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

from . import protocol
from .logger import JsonlLogger
from .safety import DEFAULT_CONFIG, SafetyError
from .transport import FakeTransport, SerialTransport


def _default_run_id() -> str:
    return datetime.now(timezone.utc).strftime("run-%Y%m%dT%H%M%SZ")


def _read_reply(transport, timeout: float = 1.0) -> protocol.Frame:
    line = transport.read_line(timeout)
    if line is None:
        raise RuntimeError("nessuna risposta dal trasporto")
    return protocol.parse_frame(line)


def _log_version(logger: JsonlLogger, frame: protocol.Frame) -> protocol.VersionInfo:
    info = protocol.parse_incoming(frame)
    if not isinstance(info, protocol.VersionInfo):
        raise RuntimeError("risposta di versione inattesa")
    logger.log("version", **asdict(info))
    return info


def run_fake(logger: JsonlLogger) -> None:
    transport = FakeTransport()
    logger.log(
        "session_start",
        mode="fake",
        protocol=protocol.PROTOCOL_VERSION,
        safety=DEFAULT_CONFIG.snapshot(),
    )

    request = protocol.version_request()
    transport.write(request)
    transport.feed_line(protocol.version_response())
    _log_version(logger, _read_reply(transport))

    heartbeat = protocol.heartbeat(1)
    transport.write(heartbeat)
    logger.log("heartbeat", sequence=1)

    sensor_frame = protocol.sensor_status(
        sequence=1,
        distance_mm=250,
        yaw_mdeg=-100,
        pitch_mdeg=20,
        roll_mdeg=0,
        status=0b11,
    )
    transport.feed_line(sensor_frame)
    reading = protocol.parse_incoming(_read_reply(transport))
    if not isinstance(reading, protocol.SensorReading):
        raise RuntimeError("risposta sensori inattesa")
    logger.log("sensors", **asdict(reading), flags=reading.flags)

    try:
        DEFAULT_CONFIG.require_motion()
    except SafetyError as exc:
        logger.log("motion_blocked", missing=exc.missing)
        print("movimento disabilitato:", ", ".join(exc.missing))

    print(f"log: {logger.path}")
    print("frame inviati:")
    for line in transport.sent_text():
        print("  " + line.rstrip("\n"))
    transport.close()


def run_real(logger: JsonlLogger, port: str, baud: int) -> None:
    transport = SerialTransport(port=port, baudrate=baud)
    logger.log(
        "session_start",
        mode="real",
        port=port,
        baud=baud,
        protocol=protocol.PROTOCOL_VERSION,
        safety=DEFAULT_CONFIG.snapshot(),
    )
    try:
        # L'apertura della porta resetta il Mega: lascia finire il bootloader.
        time.sleep(2.0)
        transport.write(protocol.version_request())
        _log_version(logger, _read_reply(transport, timeout=2.0))
        transport.write(protocol.heartbeat(1))
        logger.log("heartbeat", sequence=1)
        print(f"handshake con {port} completato; log: {logger.path}")
    finally:
        transport.close()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Livello comunicazione e logger del robot (movimento disabilitato)."
    )
    parser.add_argument("--port", help="porta seriale reale; se assente usa il trasporto finto")
    parser.add_argument("--baud", type=int, default=115200)
    parser.add_argument("--run-id", default=None)
    parser.add_argument("--log-dir", type=Path, default=Path("logs"))
    args = parser.parse_args(argv)

    run_id = args.run_id or _default_run_id()
    log_path = args.log_dir / f"{run_id}.jsonl"

    with JsonlLogger(log_path, run_id) as logger:
        if args.port:
            run_real(logger, args.port, args.baud)
        else:
            run_fake(logger)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
