"""Probe e verifiche software delle telecamere.

Il modulo usa OpenCV solo quando viene chiamato: la suite host puo' importarlo
anche su una macchina senza camera. Le metriche sono pensate per un controllo
rapido del frame, non per sostituire una calibrazione con target.
"""

from __future__ import annotations

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
    sharpness = float(cv2.Laplacian(gray, cv2.CV_64F).var())

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
        )
    finally:
        capture.release()


def list_cameras(indices: range = range(0, 4), **kwargs: object) -> list[CameraProbe]:
    """Prova una serie di indici e restituisce un report per ciascuno."""
    return [probe_camera(index, **kwargs) for index in indices]
