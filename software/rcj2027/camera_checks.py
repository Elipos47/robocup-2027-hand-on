"""Probe e verifiche software delle telecamere.

Il modulo usa OpenCV solo quando viene chiamato: la suite host puo' importarlo
anche su una macchina senza camera. Le metriche sono pensate per un controllo
rapido del frame, non per sostituire una calibrazione con target.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

try:
    import cv2
    import numpy as np

    HAS_CV2 = True
except ImportError:  # pragma: no cover - dipende dall'ambiente
    cv2 = None  # type: ignore[assignment]
    np = None  # type: ignore[assignment]
    HAS_CV2 = False

try:
    from picamera2 import Picamera2

    HAS_PICAMERA2 = True
except ImportError:  # pragma: no cover - dipende dall'ambiente
    Picamera2 = None  # type: ignore[assignment]
    HAS_PICAMERA2 = False


class CameraError(RuntimeError):
    """La telecamera o OpenCV non sono disponibili."""


@dataclass(frozen=True)
class FrameMetrics:
    width: int
    height: int
    brightness: float
    contrast: float
    sharpness: float
    dark: bool
    overexposed: bool
    blurry: bool
    passed: bool


@dataclass(frozen=True)
class CameraProbe:
    device: str
    opened: bool
    width: int | None
    height: int | None
    fps: float | None
    metrics: FrameMetrics | None
    checkerboard_corners: int | None
    saved_path: str | None
    error: str | None
    passed: bool
    quality_passed: bool | None = None
    model: str | None = None


def _require_cv2() -> None:
    if not HAS_CV2:
        raise CameraError("OpenCV/numpy non installati: pip install -r software/requirements.txt")


def _gray(frame: Any) -> Any:
    _require_cv2()
    if frame is None:
        raise CameraError("frame vuoto")
    if frame.ndim == 2:
        return frame
    if frame.ndim != 3:
        raise CameraError(f"frame con {frame.ndim} dimensioni non supportato")
    if frame.shape[2] == 3:
        return cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    if frame.shape[2] == 4:
        return cv2.cvtColor(frame, cv2.COLOR_BGRA2GRAY)
    raise CameraError(f"frame con {frame.shape[2]} canali non supportato")


def frame_metrics(
    frame: Any,
    *,
    dark_below: float = 30.0,
    overexposed_above: float = 225.0,
    min_contrast: float = 10.0,
    min_sharpness: float = 50.0,
) -> FrameMetrics:
    """Calcola luminosita', contrasto e nitidezza di un frame."""
    gray = _gray(frame)
    brightness = float(gray.mean())
    contrast = float(gray.std())

    sharp_gray = gray
    if gray.shape[1] > 640:
        scale = 640.0 / gray.shape[1]
        sharp_gray = cv2.resize(
            gray,
            (640, max(1, int(gray.shape[0] * scale))),
            interpolation=cv2.INTER_AREA,
        )
    sharpness = float(cv2.Laplacian(sharp_gray, cv2.CV_64F).var())

    dark = brightness < dark_below
    overexposed = brightness > overexposed_above
    blurry = sharpness < min_sharpness
    passed = not dark and not overexposed and not blurry and contrast >= min_contrast

    return FrameMetrics(
        width=int(gray.shape[1]),
        height=int(gray.shape[0]),
        brightness=round(brightness, 2),
        contrast=round(contrast, 2),
        sharpness=round(sharpness, 2),
        dark=dark,
        overexposed=overexposed,
        blurry=blurry,
        passed=passed,
    )


def find_checkerboard_points(frame: Any, pattern_size: tuple[int, int]) -> Any | None:
    """Restituisce i corner del checkerboard o ``None`` se non viene trovato."""
    gray = _gray(frame)
    flags = cv2.CALIB_CB_ADAPTIVE_THRESH | cv2.CALIB_CB_NORMALIZE_IMAGE
    found, corners = cv2.findChessboardCorners(gray, pattern_size, flags=flags)
    if not found or corners is None:
        return None
    return corners


def analyze_frame(
    frame: Any,
    *,
    device: str = "0",
    save_path: str | Path | None = None,
    checkerboard_size: tuple[int, int] | None = None,
    dark_below: float = 30.0,
    overexposed_above: float = 225.0,
    min_contrast: float = 10.0,
    min_sharpness: float = 50.0,
) -> CameraProbe:
    """Analizza un frame gia' acquisito, utile anche nei test host."""
    metrics = frame_metrics(
        frame,
        dark_below=dark_below,
        overexposed_above=overexposed_above,
        min_contrast=min_contrast,
        min_sharpness=min_sharpness,
    )
    quality_passed = metrics.passed

    corner_count: int | None = None
    if checkerboard_size is not None:
        corners = find_checkerboard_points(frame, checkerboard_size)
        corner_count = 0 if corners is None else len(corners)
        if corner_count == 0:
            metrics = replace(metrics, passed=False)

    saved_path: str | None = None
    if save_path is not None:
        path = Path(save_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        if not cv2.imwrite(str(path), frame):
            raise CameraError(f"impossibile salvare il frame in {path}")
        saved_path = str(path)

    return CameraProbe(
        device=str(device),
        opened=True,
        width=metrics.width,
        height=metrics.height,
        fps=None,
        metrics=metrics,
        checkerboard_corners=corner_count,
        saved_path=saved_path,
        error=None,
        passed=metrics.passed,
        quality_passed=quality_passed,
    )


def probe_camera(
    device: int | str = 0,
    *,
    save_path: str | Path | None = None,
    checkerboard_size: tuple[int, int] | None = None,
    **metric_kwargs: float,
) -> CameraProbe:
    """Apre la telecamera, legge un frame e restituisce il report."""
    _require_cv2()
    capture = cv2.VideoCapture(device)
    if not capture.isOpened():
        capture.release()
        return CameraProbe(
            device=str(device),
            opened=False,
            width=None,
            height=None,
            fps=None,
            metrics=None,
            checkerboard_corners=None,
            saved_path=None,
            error="telecamera non apribile",
            passed=False,
        )

    try:
        fps = float(capture.get(cv2.CAP_PROP_FPS))
        ok, frame = capture.read()
        if not ok or frame is None:
            return CameraProbe(
                device=str(device),
                opened=True,
                width=int(capture.get(cv2.CAP_PROP_FRAME_WIDTH)) or None,
                height=int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT)) or None,
                fps=fps if fps > 0 else None,
                metrics=None,
                checkerboard_corners=None,
                saved_path=None,
                error="frame non leggibile",
                passed=False,
            )

        probed = analyze_frame(
            frame,
            device=str(device),
            save_path=save_path,
            checkerboard_size=checkerboard_size,
            **metric_kwargs,
        )
        width = probed.width
        height = probed.height
        if width is None or height is None:
            width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH)) or None
            height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT)) or None
        return CameraProbe(
            device=probed.device,
            opened=True,
            width=width,
            height=height,
            fps=fps if fps > 0 else None,
            metrics=probed.metrics,
            checkerboard_corners=probed.checkerboard_corners,
            saved_path=probed.saved_path,
            error=None,
            passed=probed.passed,
            quality_passed=probed.quality_passed,
        )
    finally:
        capture.release()


def list_libcamera_cameras() -> list[dict[str, Any]]:
    """Elenca le camere viste da Picamera2/libcamera (USB e CSI)."""
    if not HAS_PICAMERA2:
        raise CameraError("Picamera2 non installato")
    return [dict(info) for info in Picamera2.global_camera_info()]


def probe_libcamera_camera(
    camera_num: int = 0,
    *,
    size: tuple[int, int] = (640, 480),
    warmup_s: float = 1.0,
    full_fov: bool = False,
    save_path: str | Path | None = None,
    checkerboard_size: tuple[int, int] | None = None,
    **metric_kwargs: float,
) -> CameraProbe:
    """Acquisisce un frame da Picamera2 (CSI o USB libcamera) e lo analizza."""
    if not HAS_PICAMERA2:
        raise CameraError("Picamera2 non installato")
    if not HAS_CV2:
        raise CameraError("OpenCV/numpy non installati")
    if warmup_s < 0:
        raise ValueError("warmup_s non puo' essere negativo")

    device = f"libcamera:{camera_num}"
    try:
        camera = Picamera2(camera_num=camera_num)
    except Exception as exc:
        return CameraProbe(
            device=device,
            opened=False,
            width=None,
            height=None,
            fps=None,
            metrics=None,
            checkerboard_corners=None,
            saved_path=None,
            error=str(exc),
            passed=False,
        )

    started = False
    model: str | None = None
    try:
        properties = camera.camera_properties
        if properties.get("Model"):
            model = str(properties["Model"])

        config = camera.create_still_configuration(
            main={"size": size, "format": "RGB888"},
            **(
                {"sensor": {"output_size": (2304, 1296)}}
                if full_fov
                else {}
            ),
        )
        camera.configure(config)
        camera.start()
        started = True
        try:
            from libcamera import controls

            camera.set_controls(
                {"AfMode": controls.AfModeEnum.Continuous}
            )
        except Exception:
            pass
        if warmup_s:
            time.sleep(warmup_s)
        frame = camera.capture_array("main")
        if frame.ndim == 3 and frame.shape[2] == 3:
            frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

        probed = analyze_frame(
            frame,
            device=device,
            save_path=save_path,
            checkerboard_size=checkerboard_size,
            **metric_kwargs,
        )
        return replace(probed, model=model)
    except Exception as exc:
        return CameraProbe(
            device=device,
            opened=True,
            width=None,
            height=None,
            fps=None,
            metrics=None,
            checkerboard_corners=None,
            saved_path=None,
            error=str(exc),
            passed=False,
            model=model,
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


def capture_sequence_opencv(
    device: int | str,
    output_dir: str | Path,
    *,
    count: int = 15,
    interval_s: float = 1.0,
    prefix: str = "frame",
) -> list[Path]:
    """Acquisisce una sequenza da OpenCV, utile per la calibrazione."""
    _require_cv2()
    if count < 1:
        raise ValueError("count deve essere positivo")
    if interval_s < 0:
        raise ValueError("interval_s non puo' essere negativo")

    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    capture = cv2.VideoCapture(device)
    if not capture.isOpened():
        capture.release()
        raise CameraError(f"telecamera non apribile: {device}")

    paths: list[Path] = []
    try:
        for index in range(count):
            ok, frame = capture.read()
            if not ok or frame is None:
                raise CameraError(f"frame {index} non leggibile")
            path = output / f"{prefix}-{index:03d}.jpg"
            if not cv2.imwrite(str(path), frame):
                raise CameraError(f"impossibile salvare {path}")
            paths.append(path)
            if index < count - 1 and interval_s:
                time.sleep(interval_s)
    finally:
        capture.release()
    return paths


def capture_sequence_libcamera(
    camera_num: int,
    output_dir: str | Path,
    *,
    count: int = 15,
    interval_s: float = 1.0,
    prefix: str = "frame",
    size: tuple[int, int] = (640, 480),
    warmup_s: float = 1.0,
    full_fov: bool = False,
) -> list[Path]:
    """Acquisisce una sequenza da Picamera2 (CSI o USB libcamera)."""
    if not HAS_PICAMERA2:
        raise CameraError("Picamera2 non installato")
    if not HAS_CV2:
        raise CameraError("OpenCV/numpy non installati")
    if count < 1:
        raise ValueError("count deve essere positivo")
    if interval_s < 0:
        raise ValueError("interval_s non puo' essere negativo")
    if warmup_s < 0:
        raise ValueError("warmup_s non puo' essere negativo")

    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    camera = Picamera2(camera_num=camera_num)
    started = False
    paths: list[Path] = []
    try:
        config = camera.create_still_configuration(
            main={"size": size, "format": "RGB888"},
            **(
                {"sensor": {"output_size": (2304, 1296)}}
                if full_fov
                else {}
            ),
        )
        camera.configure(config)
        camera.start()
        started = True
        try:
            from libcamera import controls

            camera.set_controls({"AfMode": controls.AfModeEnum.Continuous})
        except Exception:
            pass
        if warmup_s:
            time.sleep(warmup_s)

        for index in range(count):
            frame = camera.capture_array("main")
            if frame.ndim == 3 and frame.shape[2] == 3:
                frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            path = output / f"{prefix}-{index:03d}.jpg"
            if not cv2.imwrite(str(path), frame):
                raise CameraError(f"impossibile salvare {path}")
            paths.append(path)
            if index < count - 1 and interval_s:
                time.sleep(interval_s)
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
    return paths


def find_usb_camera(
    sysfs_root: str | Path = "/sys/class/video4linux",
) -> str:
    """Trova il primo nodo video di una telecamera USB reale."""
    root = Path(sysfs_root)
    for entry in sorted(root.glob("video*")):
        name_file = entry / "name"
        try:
            name = name_file.read_text(encoding="utf-8", errors="replace").strip()
        except OSError:
            continue
        lowered = name.lower()
        if "rp1-cfe" in lowered or "pispbe" in lowered or "hevc" in lowered:
            continue
        if "usb" in lowered or "camera" in lowered:
            return f"/dev/{entry.name}"
    raise CameraError("nessuna telecamera USB trovata")


def list_cameras(indices: range = range(0, 4), **kwargs: object) -> list[CameraProbe]:
    """Prova una serie di indici OpenCV e restituisce un report per ciascuno."""
    return [probe_camera(index, **kwargs) for index in indices]
