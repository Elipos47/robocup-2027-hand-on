"""Diagnostica software per camera, sonar e IMU.

Comandi:
  python3 -m rcj2027.diagnostics camera --device 0
  python3 -m rcj2027.diagnostics sonar --port /dev/ttyACM0 --duration 10
  python3 -m rcj2027.diagnostics imu --port /dev/ttyACM0 --duration 10
  python3 -m rcj2027.diagnostics camera-calibrate --images "calib/*.jpg"

La diagnostica seriale usa ``DEFAULT_CONFIG``: non abilita il movimento.
"""

from __future__ import annotations

import argparse
import glob
import json
import sys
import time
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from .camera_checks import (
    HAS_PICAMERA2,
    CameraError,
    CameraProbe,
    list_cameras,
    list_libcamera_cameras,
    probe_camera,
    probe_libcamera_camera,
)
from .camera_calibration import (
    CalibrationError,
    calibrate_camera,
    save_calibration,
)
from .logger import JsonlLogger
from .protocol import SensorReading
from .safety import DEFAULT_CONFIG
from .sensor_checks import (
    ImuReport,
    SonarReport,
    analyze_imu,
    analyze_sonar,
    check_sonar_reference,
)
from .session import RobotSession
from .transport import SerialTransport


def _default_run_id(kind: str) -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"diag-{kind}-{stamp}"


def _parse_pattern(text: str) -> tuple[int, int]:
    try:
        columns, rows = text.lower().split("x", 1)
        pattern = (int(columns), int(rows))
    except ValueError as exc:
        raise ValueError(f"pattern non valido: {text}; atteso COLONNExRIGHE") from exc
    if pattern[0] < 2 or pattern[1] < 2:
        raise ValueError("pattern deve avere almeno 2x2 corner")
    return pattern


def collect_readings(
    session: RobotSession,
    duration_s: float,
    *,
    read_timeout_s: float = 0.05,
    clock: Callable[[], float] = time.monotonic,
) -> list[SensorReading]:
    """Raccoglie gli status per ``duration_s`` secondi, senza inviare ``D``."""
    if duration_s <= 0:
        raise ValueError("duration_s deve essere positivo")

    started = clock()
    readings: list[SensorReading] = []
    last_sequence: int | None = None

    while clock() - started < duration_s:
        session.step(read_timeout_s=read_timeout_s)
        reading = session.last_status
        if reading is not None and reading.sequence != last_sequence:
            readings.append(reading)
            last_sequence = reading.sequence

    return readings


def _write_json(report: dict[str, Any], path: str | Path | None) -> None:
    if path is None:
        return
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def _serial_report(args: argparse.Namespace) -> int:
    run_id = args.run_id or _default_run_id(args.command)
    log_path = Path(args.log_dir) / f"{run_id}.jsonl"

    with JsonlLogger(log_path, run_id) as logger:
        with SerialTransport(args.port, args.baud) as transport:
            with RobotSession(transport, logger, config=DEFAULT_CONFIG) as session:
                info = session.handshake(boot_delay_s=2.0)
                if args.countdown > 0:
                    print(
                        f"Raccolta tra {args.countdown:g} s...",
                        file=sys.stderr,
                        flush=True,
                    )
                    time.sleep(args.countdown)
                readings = collect_readings(
                    session,
                    args.duration,
                    read_timeout_s=args.read_timeout,
                )

                if args.command == "sonar":
                    analysis: SonarReport | ImuReport = analyze_sonar(
                        readings,
                        min_valid_ratio=args.min_valid_ratio,
                        max_jump_mm=args.max_jump,
                    )
                    reference = (
                        check_sonar_reference(
                            analysis,
                            args.reference_mm,
                            tolerance_mm=args.reference_tolerance,
                        )
                        if args.reference_mm is not None
                        else None
                    )
                else:
                    reference = None
                    analysis = analyze_imu(
                        readings,
                        mode=args.imu_mode,
                        expected_axis=args.expected_axis,
                        min_valid_ratio=args.min_valid_ratio,
                        settle_samples=args.settle_samples,
                    )

                passed = analysis.passed and (
                    reference is None or reference.passed
                )
                report = {
                    "kind": args.command,
                    "run_id": run_id,
                    "handshake": asdict(info),
                    "readings": len(readings),
                    "analysis": asdict(analysis),
                    "reference": asdict(reference) if reference is not None else None,
                    "passed": passed,
                    "log": str(log_path),
                }
                print(json.dumps(report, indent=2, ensure_ascii=False))
                _write_json(report, args.json_out)
                return 0 if passed else 1


def _camera_report(args: argparse.Namespace) -> int:
    metric_kwargs = {
        "min_sharpness": args.min_sharpness,
        "min_contrast": args.min_contrast,
    }

    if args.list:
        if args.save:
            raise ValueError("--save non e' compatibile con --list")
        usb_probes = list_cameras(
            range(0, args.max_index + 1),
            checkerboard_size=None,
            **metric_kwargs,
        )
        libcamera = list_libcamera_cameras() if HAS_PICAMERA2 else []
        report = {
            "opencv": [asdict(probe) for probe in usb_probes],
            "libcamera": libcamera,
        }
        print(json.dumps(report, indent=2, ensure_ascii=False))
        _write_json(report, args.json_out)
        return 0 if any(probe.passed for probe in usb_probes) or libcamera else 1

    checkerboard = _parse_pattern(args.checkerboard) if args.checkerboard else None
    if args.csi:
        probe: CameraProbe = probe_libcamera_camera(
            args.camera_num,
            warmup_s=args.warmup,
            save_path=args.save,
            checkerboard_size=checkerboard,
            **metric_kwargs,
        )
    else:
        device: int | str = int(args.device) if args.device.isdigit() else args.device
        probe = probe_camera(
            device,
            save_path=args.save,
            checkerboard_size=checkerboard,
            **metric_kwargs,
        )

    report = asdict(probe)
    print(json.dumps(report, indent=2, ensure_ascii=False))
    _write_json(report, args.json_out)
    return 0 if probe.passed else 1


def _camera_calibrate_report(args: argparse.Namespace) -> int:
    pattern = _parse_pattern(args.pattern)
    images = sorted(glob.glob(args.images))
    if not images:
        raise CalibrationError(f"nessuna immagine trovata: {args.images}")

    calibration = calibrate_camera(
        images,
        pattern_size=pattern,
        square_size_mm=args.square_mm,
        min_images=args.min_images,
    )
    output = save_calibration(calibration, args.output)
    report = calibration.to_dict()
    report["output"] = str(output)
    print(json.dumps(report, indent=2, ensure_ascii=False))
    _write_json(report, args.json_out)
    return 0


def _add_serial_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--port", required=True, help="porta seriale, es. /dev/ttyACM0")
    parser.add_argument("--baud", type=int, default=115200)
    parser.add_argument("--duration", type=float, default=10.0)
    parser.add_argument("--read-timeout", type=float, default=0.05)
    parser.add_argument(
        "--countdown",
        type=float,
        default=0.0,
        help="attesa prima della raccolta, per preparare il test",
    )
    parser.add_argument("--run-id", default=None)
    parser.add_argument("--log-dir", type=Path, default=Path("logs"))
    parser.add_argument("--json-out", default=None)
    parser.add_argument("--min-valid-ratio", type=float, default=0.8)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Diagnostica software per camera, sonar e IMU."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    sonar = subparsers.add_parser("sonar", help="raccoglie e analizza HC-SR04")
    _add_serial_args(sonar)
    sonar.add_argument("--max-jump", type=int, default=500, help="salto massimo in mm")
    sonar.add_argument(
        "--reference-mm",
        type=int,
        default=None,
        help="distanza di riferimento misurata con un metro",
    )
    sonar.add_argument("--reference-tolerance", type=int, default=50)

    imu = subparsers.add_parser("imu", help="raccoglie e analizza BNO085")
    _add_serial_args(imu)
    imu.add_argument(
        "--imu-mode",
        choices=("stationary", "motion"),
        default="stationary",
        help="stationary: robot fermo; motion: ruotare il robot durante il test",
    )
    imu.add_argument(
        "--expected-axis",
        choices=("yaw", "pitch", "roll"),
        default=None,
        help="asse che deve muoversi durante il test motion",
    )
    imu.add_argument("--settle-samples", type=int, default=5)

    camera = subparsers.add_parser("camera", help="probe di una o piu' telecamere")
    camera.add_argument("--device", default="0", help="indice o path OpenCV, es. 0 o /dev/video0")
    camera.add_argument(
        "--csi",
        action="store_true",
        help="usa Picamera2/libcamera (camera CSI o USB libcamera)",
    )
    camera.add_argument("--camera-num", type=int, default=0, help="indice Picamera2")
    camera.add_argument(
        "--warmup",
        type=float,
        default=1.0,
        help="attesa AF/esposizione prima dello scatto libcamera",
    )
    camera.add_argument("--list", action="store_true", help="prova gli indici 0..max-index")
    camera.add_argument("--max-index", type=int, default=3)
    camera.add_argument("--save", default=None, help="salva il frame analizzato")
    camera.add_argument("--checkerboard", default=None, help="pattern interno, es. 9x6")
    camera.add_argument("--min-sharpness", type=float, default=50.0)
    camera.add_argument("--min-contrast", type=float, default=10.0)
    camera.add_argument("--json-out", default=None)

    calibration = subparsers.add_parser(
        "camera-calibrate",
        help="calibra una camera da immagini checkerboard",
    )
    calibration.add_argument("--images", required=True, help="glob, es. 'calib/*.jpg'")
    calibration.add_argument("--pattern", default="9x6", help="corner interni, es. 9x6")
    calibration.add_argument("--square-mm", type=float, default=25.0)
    calibration.add_argument("--min-images", type=int, default=3)
    calibration.add_argument("--output", default="camera_calibration.json")
    calibration.add_argument("--json-out", default=None)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        if args.command in {"sonar", "imu"}:
            return _serial_report(args)
        if args.command == "camera":
            return _camera_report(args)
        if args.command == "camera-calibrate":
            return _camera_calibrate_report(args)
    except (CameraError, CalibrationError, RuntimeError, OSError, ValueError) as exc:
        print(f"ERR {exc}", file=sys.stderr)
        return 2

    parser.error("comando non riconosciuto")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
