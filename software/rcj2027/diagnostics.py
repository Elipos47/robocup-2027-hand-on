"""Diagnostica software per camera, sonar e IMU.

Comandi:
  python3 -m rcj2027.diagnostics camera --device 0
  python3 -m rcj2027.diagnostics sonar --port /dev/ttyACM0 --duration 10
  python3 -m rcj2027.diagnostics imu --port /dev/ttyACM0 --duration 10
  python3 -m rcj2027.diagnostics camera-calibrate --images "calib/*.jpg"
  python3 -m rcj2027.diagnostics line --images "calib/linea/*.jpg"
  python3 -m rcj2027.diagnostics line-undistort --images "calib/csi/*.jpg"

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
    capture_sequence_libcamera,
    capture_sequence_opencv,
    find_usb_camera,
    list_libcamera_cameras,
    probe_camera,
    probe_libcamera_camera,
)
from .camera_calibration import (
    CalibrationError,
    calibrate_camera,
    save_calibration,
)
from .checkerboard import CheckerboardError, make_checkerboard_pdf
from . import line_vision
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


DEFAULT_LINE_CALIBRATION = (
    Path(__file__).resolve().parent / "calibrations" / "csi_1280x720.json"
)


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


def _resolve_device(text: str) -> int | str:
    if text == "auto":
        return find_usb_camera()
    if text.isdigit():
        return int(text)
    return text


def _parse_size(text: str) -> tuple[int, int]:
    try:
        width, height = text.lower().split("x", 1)
        size = (int(width), int(height))
    except ValueError as exc:
        raise ValueError(f"size non valida: {text}; atteso LARGHEZZAxALTEZZA") from exc
    if size[0] <= 0 or size[1] <= 0:
        raise ValueError("size deve essere positiva")
    return size


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


def _distribution(values: list[float]) -> dict[str, float] | None:
    if not values:
        return None
    ordered = sorted(values)
    middle = len(ordered) // 2
    if len(ordered) % 2:
        median = ordered[middle]
    else:
        median = (ordered[middle - 1] + ordered[middle]) / 2.0
    return {
        "min": round(ordered[0], 3),
        "median": round(median, 3),
        "mean": round(sum(ordered) / len(ordered), 3),
        "max": round(ordered[-1], 3),
    }


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
                        outlier_mm=args.outlier_mm,
                        max_outlier_ratio=args.max_outlier_ratio,
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
        usb_probes: list[CameraProbe] = []
        try:
            usb_probes.append(
                probe_camera(
                    find_usb_camera(),
                    checkerboard_size=None,
                    **metric_kwargs,
                )
            )
        except CameraError:
            pass
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
            size=_parse_size(args.size),
            warmup_s=args.warmup,
            full_fov=args.full_fov,
            save_path=args.save,
            checkerboard_size=checkerboard,
            **metric_kwargs,
        )
    else:
        device = _resolve_device(args.device)
        probe = probe_camera(
            device,
            save_path=args.save,
            checkerboard_size=checkerboard,
            **metric_kwargs,
        )

    report = asdict(probe)
    if (
        checkerboard is not None
        and probe.checkerboard_corners == 0
        and probe.quality_passed
    ):
        print(
            "ATTENZIONE: checkerboard non rilevato nonostante la qualita' del frame "
            "sia buona. Controlla che tutto il pattern e il bordo bianco siano nel frame.",
            file=sys.stderr,
        )
    print(json.dumps(report, indent=2, ensure_ascii=False))
    _write_json(report, args.json_out)
    return 0 if probe.passed else 1


def _camera_capture_report(args: argparse.Namespace) -> int:
    if args.csi:
        paths = capture_sequence_libcamera(
            args.camera_num,
            args.output_dir,
            count=args.count,
            interval_s=args.interval,
            prefix=args.prefix,
            size=_parse_size(args.size),
            warmup_s=args.warmup,
            full_fov=args.full_fov,
        )
    else:
        device = _resolve_device(args.device)
        paths = capture_sequence_opencv(
            device,
            args.output_dir,
            count=args.count,
            interval_s=args.interval,
            prefix=args.prefix,
        )

    report = {
        "count": len(paths),
        "output_dir": str(Path(args.output_dir)),
        "images": [str(path) for path in paths],
        "csi": bool(args.csi),
    }
    print(json.dumps(report, indent=2, ensure_ascii=False))
    _write_json(report, args.json_out)
    return 0


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
        min_coverage=args.min_coverage,
        min_pose_spread_px=args.min_pose_spread,
    )
    output = save_calibration(calibration, args.output)
    report = calibration.to_dict()
    report["output"] = str(output)
    print(json.dumps(report, indent=2, ensure_ascii=False))
    _write_json(report, args.json_out)
    return 0


def _line_report(args: argparse.Namespace) -> int:
    if not 0 <= args.min_found_ratio <= 1:
        raise ValueError("--min-found-ratio deve essere tra 0 e 1")
    paths = sorted(glob.glob(args.images))
    if not paths:
        raise line_vision.LineVisionError(
            f"nessuna immagine trovata: {args.images}"
        )

    camera_model = None
    if not args.no_undistort:
        camera_model = line_vision.load_camera_model(args.calibration)
    config = line_vision.LineConfig(
        roi_top=args.roi_top,
        roi_bottom=args.roi_bottom,
        threshold_block=args.block_size or None,
        threshold_c=args.threshold_c,
        dark_threshold=args.dark_threshold,
        max_run_ratio=args.max_run_ratio,
        max_gap_ratio=args.max_gap_ratio,
        width_tolerance_ratio=args.width_tolerance,
        fit_residual_px=args.fit_residual,
        min_confidence=args.min_confidence,
        min_valid_ratio=args.min_valid_ratio,
    )
    detector = line_vision.LineDetector(camera_model, config)
    tracker = line_vision.LineTracker()

    annotated_dir = Path(args.annotated_dir) if args.annotated_dir else None
    mask_dir = Path(args.mask_dir) if args.mask_dir else None
    debug_enabled = annotated_dir is not None or mask_dir is not None

    records: list[dict[str, Any]] = []
    found = 0
    confirmed = 0
    max_lost = 0
    for path in paths:
        frame = line_vision.read_image(path)
        if debug_enabled:
            observation, debug = detector.detect(frame, debug=True)
        else:
            observation = detector.detect(frame)
            debug = None
        state = tracker.update(observation)
        if observation.found:
            found += 1
        if state.confirmed:
            confirmed += 1
        max_lost = max(max_lost, state.lost_frames)

        record: dict[str, Any] = {
            "image": path,
            **observation.to_dict(),
            "tracker": asdict(state),
        }
        records.append(record)

        if debug is not None:
            stem = Path(path).stem
            if annotated_dir is not None:
                annotated = line_vision.annotate_frame(debug, observation)
                record["annotated"] = str(
                    line_vision.write_image(
                        annotated_dir / f"{stem}-annotated.jpg", annotated
                    )
                )
            if mask_dir is not None:
                record["mask"] = str(
                    line_vision.write_image(mask_dir / f"{stem}-mask.png", debug.mask)
                )

    recoveries = tracker.recoveries
    offsets = [record["offset_px"] for record in records if record["found"]]
    headings = [record["heading_deg"] for record in records if record["found"]]
    confidences = [record["confidence"] for record in records]
    latencies = [record["processing_ms"] for record in records]
    found_ratio = found / len(records)
    report = {
        "kind": "line",
        "images": len(records),
        "calibration": str(args.calibration) if camera_model is not None else None,
        "undistorted": camera_model is not None,
        "config": {
            "roi_top": args.roi_top,
            "roi_bottom": args.roi_bottom,
            "block_size": args.block_size or None,
            "threshold_c": args.threshold_c,
            "dark_threshold": config.dark_threshold,
            "dark_max_fraction": config.dark_max_fraction,
            "max_run_ratio": config.max_run_ratio,
            "max_gap_ratio": config.max_gap_ratio,
            "width_tolerance_ratio": config.width_tolerance_ratio,
            "fit_residual_px": config.fit_residual_px,
            "min_valid_rows": config.min_valid_rows,
            "min_confidence": args.min_confidence,
            "min_valid_ratio": args.min_valid_ratio,
        },
        "summary": {
            "found": found,
            "found_ratio": round(found_ratio, 4),
            "confirmed_frames": confirmed,
            "recoveries": recoveries,
            "max_lost_frames": max_lost,
            "offset_px": _distribution(offsets),
            "heading_deg": _distribution(headings),
            "confidence": _distribution(confidences),
            "processing_ms": _distribution(latencies),
        },
        "passed": found_ratio >= args.min_found_ratio,
        "frames": records,
    }
    print(json.dumps(report, indent=2, ensure_ascii=False))
    _write_json(report, args.json_out)
    return 0 if report["passed"] else 1


def _line_live_report(args: argparse.Namespace) -> int:
    if not HAS_PICAMERA2:
        raise CameraError("Picamera2 non installato")
    if args.duration <= 0:
        raise ValueError("--duration deve essere positivo")
    if args.interval < 0:
        raise ValueError("--interval non puo' essere negativo")
    if args.save_every < 1:
        raise ValueError("--save-every deve essere positivo")
    if not 0 <= args.min_found_ratio <= 1:
        raise ValueError("--min-found-ratio deve essere tra 0 e 1")

    from libcamera import controls
    from picamera2 import Picamera2

    size = _parse_size(args.size)
    camera_model = None
    if not args.no_undistort:
        camera_model = line_vision.load_camera_model(args.calibration)
        if size != camera_model.image_size:
            raise line_vision.LineVisionError(
                f"size {size[0]}x{size[1]} diversa dalla calibrazione "
                f"{camera_model.width}x{camera_model.height}"
            )

    config = line_vision.LineConfig(
        min_confidence=args.min_confidence,
        min_valid_ratio=args.min_valid_ratio,
    )
    detector = line_vision.LineDetector(camera_model, config)
    tracker = line_vision.LineTracker()
    annotated_dir = Path(args.annotated_dir) if args.annotated_dir else None
    mask_dir = Path(args.mask_dir) if args.mask_dir else None
    save_debug = annotated_dir is not None or mask_dir is not None

    run_id = args.run_id or _default_run_id("line-live")
    log_path = Path(args.log_dir) / f"{run_id}.jsonl"
    camera = Picamera2(camera_num=args.camera_num)
    started = False
    frames = 0
    found = 0
    confirmed = 0
    max_lost = 0
    offsets: list[float] = []
    headings: list[float] = []
    confidences: list[float] = []
    latencies: list[float] = []
    saved = 0

    with JsonlLogger(log_path, run_id) as logger:
        logger.log(
            "session_start",
            mode="line-live",
            camera=args.camera_num,
            size=list(size),
            full_fov=True,
            duration_s=args.duration,
            calibration=str(args.calibration) if camera_model is not None else None,
        )
        try:
            video_config = camera.create_video_configuration(
                main={"size": size, "format": "RGB888"},
                sensor={"output_size": (2304, 1296)},
            )
            camera.configure(video_config)
            camera.start()
            started = True
            try:
                camera.set_controls({"AfMode": controls.AfModeEnum.Continuous})
            except Exception:
                pass
            if args.warmup:
                time.sleep(args.warmup)

            started_at = time.monotonic()
            while time.monotonic() - started_at < args.duration:
                loop_started = time.perf_counter()
                frame = camera.capture_array("main")
                if frame.ndim == 3 and frame.shape[2] == 3:
                    frame = frame[:, :, ::-1].copy()
                if save_debug:
                    observation, debug = detector.detect(frame, debug=True)
                else:
                    observation = detector.detect(frame)
                    debug = None
                state = tracker.update(observation)
                frames += 1
                if observation.found:
                    found += 1
                    offsets.append(observation.offset_px)
                    headings.append(observation.heading_deg)
                if state.confirmed:
                    confirmed += 1
                max_lost = max(max_lost, state.lost_frames)
                confidences.append(observation.confidence)
                latencies.append(observation.processing_ms)
                logger.log(
                    "line",
                    frame=frames - 1,
                    **observation.to_dict(),
                    tracker=asdict(state),
                )
                if debug is not None and save_debug and (frames - 1) % args.save_every == 0:
                    stem = f"frame-{frames - 1:05d}"
                    if annotated_dir is not None:
                        line_vision.write_image(
                            annotated_dir / f"{stem}-annotated.jpg",
                            line_vision.annotate_frame(debug, observation),
                        )
                        saved += 1
                    if mask_dir is not None:
                        line_vision.write_image(
                            mask_dir / f"{stem}-mask.png", debug.mask
                        )
                if args.interval:
                    remaining = args.interval - (time.perf_counter() - loop_started)
                    if remaining > 0:
                        time.sleep(remaining)
                if frames % 30 == 0:
                    print(
                        f"frame {frames}: found {found}, "
                        f"offset {observation.offset_px:+.1f} px",
                        file=sys.stderr,
                        flush=True,
                    )

            elapsed = time.monotonic() - started_at
            found_ratio = found / frames if frames else 0.0
            report = {
                "kind": "line-live",
                "run_id": run_id,
                "log": str(log_path),
                "calibration": (
                    str(args.calibration) if camera_model is not None else None
                ),
                "undistorted": camera_model is not None,
                "camera": args.camera_num,
                "size": list(size),
                "full_fov": True,
                "summary": {
                    "frames": frames,
                    "found": found,
                    "found_ratio": round(found_ratio, 4),
                    "confirmed_frames": confirmed,
                    "recoveries": tracker.recoveries,
                    "max_lost_frames": max_lost,
                    "offset_px": _distribution(offsets),
                    "heading_deg": _distribution(headings),
                    "confidence": _distribution(confidences),
                    "processing_ms": _distribution(latencies),
                    "duration_s": round(elapsed, 2),
                    "fps": round(frames / elapsed, 1) if elapsed > 0 else 0.0,
                    "saved_frames": saved,
                },
                "passed": bool(frames) and found_ratio >= args.min_found_ratio,
            }
            logger.log(
                "session_end",
                mode="line-live",
                frames=frames,
                found=found,
                found_ratio=round(found_ratio, 4),
            )
        finally:
            if started:
                try:
                    camera.stop()
                except Exception:
                    pass
            try:
                camera.close()
            except Exception:
                pass

    print(json.dumps(report, indent=2, ensure_ascii=False))
    _write_json(report, args.json_out)
    return 0 if report["passed"] else 1


def _line_undistort_report(args: argparse.Namespace) -> int:
    paths = sorted(glob.glob(args.images))
    if not paths:
        raise line_vision.LineVisionError(
            f"nessuna immagine trovata: {args.images}"
        )
    model = line_vision.load_camera_model(args.calibration)
    report = line_vision.validate_undistortion(
        paths,
        model,
        pattern_size=_parse_pattern(args.pattern),
        min_images=args.min_images,
        tolerance_px=args.tolerance,
        max_mean_residual_px=args.max_mean_residual,
    )
    payload = report.to_dict()
    if args.save_dir:
        output = Path(args.save_dir)
        detector = line_vision.LineDetector(model)
        saved = []
        for path in paths:
            try:
                frame = line_vision.read_image(path)
            except line_vision.LineVisionError as exc:
                print(f"ATTENZIONE: {exc}", file=sys.stderr)
                continue
            if frame.shape[1::-1] != model.image_size:
                print(
                    f"ATTENZIONE: {path} ha risoluzione diversa dalla calibrazione",
                    file=sys.stderr,
                )
                continue
            saved.append(
                str(
                    line_vision.write_image(
                        output / f"{Path(path).stem}-undistorted.jpg",
                        detector.undistort(frame),
                    )
                )
            )
        payload["saved"] = saved
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    _write_json(payload, args.json_out)
    return 0 if report.passed else 1



    pattern = _parse_pattern(args.pattern)
    output = make_checkerboard_pdf(
        args.output,
        pattern_size=pattern,
        square_size_mm=args.square_mm,
        landscape_page=not args.portrait,
        margin_mm=args.margin_mm,
    )
    columns = pattern[0] + 1
    rows = pattern[1] + 1
    report = {
        "output": str(output),
        "pattern_size": list(pattern),
        "squares": [columns, rows],
        "square_size_mm": args.square_mm,
        "board_size_mm": [columns * args.square_mm, rows * args.square_mm],
        "print": "100% / dimensione reale",
        "scale_check": "barra 100 mm; se misura 95 mm usare --square-mm 23.75",
    }
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
    sonar.add_argument(
        "--outlier-mm",
        type=int,
        default=200,
        help="scostamento dalla mediana considerato outlier",
    )
    sonar.add_argument(
        "--max-outlier-ratio",
        type=float,
        default=0.05,
        help="frazione massima di outlier ammessa (default 0.05)",
    )
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
    camera.add_argument(
        "--device",
        default="auto",
        help="auto, indice o path OpenCV (es. 8 o /dev/video8)",
    )
    camera.add_argument(
        "--csi",
        action="store_true",
        help="usa Picamera2/libcamera (camera CSI o USB libcamera)",
    )
    camera.add_argument("--camera-num", type=int, default=0, help="indice Picamera2")
    camera.add_argument(
        "--size",
        default="640x480",
        help="risoluzione libcamera, es. 1280x720 o 1536x864",
    )
    camera.add_argument(
        "--full-fov",
        action="store_true",
        help="usa il sensore intero 2304x1296 invece del crop 1536x864",
    )
    camera.add_argument(
        "--warmup",
        type=float,
        default=1.0,
        help="attesa AF/esposizione prima dello scatto libcamera",
    )
    camera.add_argument("--list", action="store_true", help="elenca USB e camere libcamera")
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
    calibration.add_argument(
        "--min-coverage",
        type=float,
        default=0.2,
        help="frazione minima media del frame occupata dal pattern",
    )
    calibration.add_argument(
        "--min-pose-spread",
        type=float,
        default=40.0,
        help="spostamento minimo del centro del pattern tra le viste, in px",
    )
    calibration.add_argument("--output", default="camera_calibration.json")
    calibration.add_argument("--json-out", default=None)

    capture = subparsers.add_parser(
        "camera-capture",
        help="acquisisce una sequenza di frame per la calibrazione",
    )
    capture.add_argument(
        "--device",
        default="auto",
        help="auto, indice o path OpenCV (es. 8 o /dev/video8)",
    )
    capture.add_argument(
        "--csi",
        action="store_true",
        help="usa Picamera2/libcamera",
    )
    capture.add_argument("--camera-num", type=int, default=0)
    capture.add_argument(
        "--size",
        default="640x480",
        help="risoluzione libcamera, es. 1280x720 o 1536x864",
    )
    capture.add_argument(
        "--full-fov",
        action="store_true",
        help="usa il sensore intero 2304x1296 invece del crop 1536x864",
    )
    capture.add_argument("--warmup", type=float, default=1.0)
    capture.add_argument("--count", type=int, default=15)
    capture.add_argument("--interval", type=float, default=1.0)
    capture.add_argument("--output-dir", default="calib")
    capture.add_argument("--prefix", default="frame")
    capture.add_argument("--json-out", default=None)

    line = subparsers.add_parser(
        "line",
        help="rileva la linea nera su una sequenza di immagini",
    )
    line.add_argument(
        "--images",
        required=True,
        help="glob delle immagini, es. 'calib/linea/*.jpg'",
    )
    line.add_argument(
        "--calibration",
        default=str(DEFAULT_LINE_CALIBRATION),
        help="calibrazione della telecamera linea (default: CSI 1280x720)",
    )
    line.add_argument(
        "--no-undistort",
        action="store_true",
        help="analizza il frame grezzo, senza calibrazione",
    )
    line.add_argument("--roi-top", type=float, default=0.55)
    line.add_argument("--roi-bottom", type=float, default=0.98)
    line.add_argument(
        "--block-size",
        type=int,
        default=0,
        help="dimensione adattiva dispari; 0 = automatica",
    )
    line.add_argument("--threshold-c", type=float, default=10.0)
    line.add_argument("--dark-threshold", type=float, default=140.0)
    line.add_argument("--max-run-ratio", type=float, default=0.35)
    line.add_argument("--max-gap-ratio", type=float, default=0.06)
    line.add_argument("--width-tolerance", type=float, default=0.50)
    line.add_argument("--fit-residual", type=float, default=8.0)
    line.add_argument("--min-confidence", type=float, default=0.35)
    line.add_argument("--min-valid-ratio", type=float, default=0.45)
    line.add_argument(
        "--min-found-ratio",
        type=float,
        default=0.8,
        help="frazione minima di frame con linea per uscire con 0",
    )
    line.add_argument("--annotated-dir", default=None)
    line.add_argument("--mask-dir", default=None)
    line.add_argument("--json-out", default=None)

    live = subparsers.add_parser(
        "line-live",
        help="rileva la linea in tempo reale dalla CSI, senza comandi motori",
    )
    live.add_argument(
        "--calibration",
        default=str(DEFAULT_LINE_CALIBRATION),
        help="calibrazione della telecamera linea (default: CSI 1280x720)",
    )
    live.add_argument(
        "--no-undistort",
        action="store_true",
        help="analizza il frame grezzo, senza calibrazione",
    )
    live.add_argument("--camera-num", type=int, default=0)
    live.add_argument("--size", default="1280x720")
    live.add_argument("--warmup", type=float, default=2.0)
    live.add_argument("--duration", type=float, default=10.0)
    live.add_argument(
        "--interval",
        type=float,
        default=0.0,
        help="pausa minima tra frame; 0 = elabora appena possibile",
    )
    live.add_argument("--run-id", default=None)
    live.add_argument("--log-dir", type=Path, default=Path("logs"))
    live.add_argument("--annotated-dir", default=None)
    live.add_argument("--mask-dir", default=None)
    live.add_argument("--save-every", type=int, default=10)
    live.add_argument("--min-confidence", type=float, default=0.35)
    live.add_argument("--min-valid-ratio", type=float, default=0.45)
    live.add_argument("--min-found-ratio", type=float, default=0.8)
    live.add_argument("--json-out", default=None)

    undistort = subparsers.add_parser(
        "line-undistort",
        help="verifica l'undistort della telecamera linea su checkerboard",
    )
    undistort.add_argument(
        "--images",
        required=True,
        help="glob delle immagini checkerboard, es. 'calib/csi/*.jpg'",
    )
    undistort.add_argument(
        "--calibration",
        default=str(DEFAULT_LINE_CALIBRATION),
        help="calibrazione da verificare (default: CSI 1280x720)",
    )
    undistort.add_argument("--pattern", default="9x6", help="corner interni")
    undistort.add_argument("--min-images", type=int, default=3)
    undistort.add_argument(
        "--tolerance",
        type=float,
        default=0.05,
        help="peggioramento massimo ammesso dall'undistort, in px",
    )
    undistort.add_argument("--max-mean-residual", type=float, default=1.0)
    undistort.add_argument("--save-dir", default=None)
    undistort.add_argument("--json-out", default=None)

    target = subparsers.add_parser(
        "checkerboard",
        help="genera un target checkerboard PDF a dimensione reale",
    )
    target.add_argument("--pattern", default="9x6", help="corner interni, es. 9x6")
    target.add_argument("--square-mm", type=float, default=25.0)
    target.add_argument("--output", default="checkerboard.pdf")
    target.add_argument("--portrait", action="store_true")
    target.add_argument("--margin-mm", type=float, default=15.0)
    target.add_argument("--json-out", default=None)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        if args.command in {"sonar", "imu"}:
            return _serial_report(args)
        if args.command == "camera":
            return _camera_report(args)
        if args.command == "camera-capture":
            return _camera_capture_report(args)
        if args.command == "camera-calibrate":
            return _camera_calibrate_report(args)
        if args.command == "line":
            return _line_report(args)
        if args.command == "line-live":
            return _line_live_report(args)
        if args.command == "line-undistort":
            return _line_undistort_report(args)
        if args.command == "checkerboard":
            return _checkerboard_report(args)
    except (CameraError, CalibrationError, RuntimeError, OSError, ValueError) as exc:
        print(f"ERR {exc}", file=sys.stderr)
        return 2

    parser.error("comando non riconosciuto")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
