"""Demo del livello di comunicazione e logging, senza movimento reale."""

from __future__ import annotations

import argparse
import sys
import threading
import time
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

from . import protocol
from .logger import JsonlLogger
from .safety import DEFAULT_CONFIG, SafetyError
from .session import RobotSession, SessionError
from .transport import FakeTransport, SerialTransport


def _default_run_id() -> str:
    return datetime.now(timezone.utc).strftime("run-%Y%m%dT%H%M%SZ")


def _normalize_payload(text: str) -> str:
    """Rende maiuscola la lettera del comando, per l'uso manuale."""
    text = text.strip()
    if not text:
        return text
    if text[0].isalpha():
        return text[0].upper() + text[1:]
    return text


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


def run_real(logger: JsonlLogger, port: str, baud: int, duration_s: float) -> None:
    """Apre il link reale, verifica handshake, heartbeat e status per un intervallo."""
    transport = SerialTransport(port=port, baudrate=baud)
    session = RobotSession(transport, logger)
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
        info = session.handshake(boot_delay_s=2.0)
        print(
            f"handshake con {port}: protocollo {info.protocol}, "
            f"scheda {info.board}, firmware {info.firmware}"
        )
        print(
            f"sessione {duration_s:g} s, heartbeat ogni "
            f"{session.heartbeat_interval_s:g} s"
        )
        session.run(duration_s)
    finally:
        session.close(reason="real_session_end")
    print(
        f"status {session.status_count}, heartbeat {session.heartbeat_count}, "
        f"errori {session.error_count}, frame invalidi {session.invalid_count}"
    )
    print(f"log: {logger.path}")


def run_interactive(logger: JsonlLogger, port: str, baud: int) -> None:
    """Console manuale: accetta payload minuscoli e aggiunge il checksum."""
    transport = SerialTransport(port=port, baudrate=baud)
    stop_event = threading.Event()
    reader_thread: threading.Thread | None = None

    def reader() -> None:
        status_count = 0
        while not stop_event.is_set():
            line = transport.read_line(timeout=0.2)
            if line is None:
                continue
            text = line.decode("ascii", errors="replace").rstrip()
            if text.startswith("A,"):
                status_count += 1
                if status_count % 10 != 0:
                    continue
            print(f"RX {text}")

    logger.log(
        "session_start",
        mode="interactive",
        port=port,
        baud=baud,
        protocol=protocol.PROTOCOL_VERSION,
        safety=DEFAULT_CONFIG.snapshot(),
    )

    try:
        time.sleep(2.0)
        transport.write(protocol.version_request())
        reader_thread = threading.Thread(target=reader, daemon=True)
        reader_thread.start()

        print("Handshake inviato. Scrivi il payload senza checksum, in maiuscolo o minuscolo.")
        print("Esempi: v,1   h,1   x,2   d,1,100,100   z,3,90")
        print("Scrivi 'quit' per uscire.")
        print("I frame A (status) vengono mostrati circa una volta al secondo.")

        while True:
            try:
                text = input("TX> ")
            except (EOFError, KeyboardInterrupt):
                print()
                break

            text = text.strip()
            if not text:
                continue
            if text.lower() in {"quit", "exit", "q"}:
                break

            try:
                if "*" in text:
                    raw = text if text.endswith("\n") else text + "\n"
                    protocol.parse_frame(raw)
                    data = raw.encode("ascii")
                    logger.log("tx_manual", payload=text, mode="raw")
                else:
                    payload = _normalize_payload(text)
                    data = protocol.encode(payload)
                    logger.log(
                        "tx_manual",
                        payload=payload,
                        frame=data.decode("ascii").rstrip(),
                    )
                transport.write(data)
            except (protocol.ProtocolError, TypeError, UnicodeEncodeError) as exc:
                print(f"ERR {exc}")
    finally:
        stop_event.set()
        if reader_thread is not None:
            reader_thread.join(timeout=1.0)
        transport.close()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Livello comunicazione e logger del robot (movimento disabilitato)."
    )
    parser.add_argument("--port", help="porta seriale reale; se assente usa il trasporto finto")
    parser.add_argument("--baud", type=int, default=115200)
    parser.add_argument("--run-id", default=None)
    parser.add_argument("--log-dir", type=Path, default=Path("logs"))
    parser.add_argument(
        "--duration",
        type=float,
        default=5.0,
        help="durata della sessione reale in secondi (default: 5)",
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="console manuale sulla porta seriale; richiede --port",
    )
    args = parser.parse_args(argv)

    if args.interactive and not args.port:
        parser.error("--interactive richiede --port")
    if args.duration <= 0:
        parser.error("--duration deve essere positivo")

    run_id = args.run_id or _default_run_id()
    log_path = args.log_dir / f"{run_id}.jsonl"

    try:
        with JsonlLogger(log_path, run_id) as logger:
            if args.interactive:
                run_interactive(logger, args.port, args.baud)
            elif args.port:
                run_real(logger, args.port, args.baud, args.duration)
            else:
                run_fake(logger)
    except KeyboardInterrupt:
        print("\ninterrotto")
        return 130
    except (SessionError, RuntimeError, OSError) as exc:
        print(f"ERR {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
