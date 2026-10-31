"""Calibrazione intrinseca delle telecamere da immagini checkerboard."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable

try:
    import cv2
    import numpy as np

    HAS_CV2 = True
except ImportError:  # pragma: no cover - dipende dall'ambiente
    cv2 = None  # type: ignore[assignment]
    np = None  # type: ignore[assignment]
    HAS_CV2 = False


class CalibrationError(RuntimeError):
    """Immagini insufficienti o checkerboard non rilevato."""


@dataclass(frozen=True)
class CameraCalibration:
    image_count: int
    pattern_size: tuple[int, int]
    square_size_mm: float
    image_size: tuple[int, int]
    rms: float
    camera_matrix: list[list[float]]
    distortion: list[float]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _load_image(image: Any) -> Any:
    if isinstance(image, (str, Path)):
        loaded = cv2.imread(str(image))
        if loaded is None:
            raise CalibrationError(f"immagine non leggibile: {image}")
        return loaded
    if hasattr(image, "shape"):
        return image
    raise TypeError("immagine deve essere un path o un array")


def calibrate_camera(
    images: Iterable[Any],
    *,
    pattern_size: tuple[int, int] = (9, 6),
    square_size_mm: float = 25.0,
    min_images: int = 3,
) -> CameraCalibration:
    """Calcola matrice intrinseca e distorsione da immagini checkerboard.

    ``pattern_size`` e' il numero di corner interni, non il numero di quadrati.
    """
    if not HAS_CV2:
        raise CalibrationError(
            "OpenCV/numpy non installati: pip install -r software/requirements.txt"
        )
    if square_size_mm <= 0:
        raise ValueError("square_size_mm deve essere positivo")
    if min_images < 1:
        raise ValueError("min_images deve essere positivo")

    object_template = np.zeros(
        (pattern_size[0] * pattern_size[1], 3),
        np.float32,
    )
    grid = np.mgrid[0 : pattern_size[0], 0 : pattern_size[1]]
    object_template[:, :2] = grid.T.reshape(-1, 2) * square_size_mm

    object_points: list[Any] = []
    image_points: list[Any] = []
    image_size: tuple[int, int] | None = None
    rejected = 0

    criteria = (
        cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER,
        30,
        0.001,
    )

    for image in images:
        try:
            frame = _load_image(image)
        except CalibrationError:
            rejected += 1
            continue

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY) if frame.ndim == 3 else frame
        size = (int(gray.shape[1]), int(gray.shape[0]))
        if image_size is None:
            image_size = size
        elif image_size != size:
            rejected += 1
            continue

        found, corners = cv2.findChessboardCorners(
            gray,
            pattern_size,
            flags=cv2.CALIB_CB_ADAPTIVE_THRESH | cv2.CALIB_CB_NORMALIZE_IMAGE,
        )
        if not found or corners is None:
            rejected += 1
            continue

        refined = cv2.cornerSubPix(gray, corners, (11, 11), (-1, -1), criteria)
        object_points.append(object_template.copy())
        image_points.append(refined)

    if image_size is None or len(object_points) < min_images:
        raise CalibrationError(
            f"checkerboard valido in {len(object_points)} immagini, "
            f"ne servono almeno {min_images} (scartate {rejected})"
        )

    rms, camera_matrix, distortion, _, _ = cv2.calibrateCamera(
        object_points,
        image_points,
        image_size,
        None,
        None,
    )

    return CameraCalibration(
        image_count=len(object_points),
        pattern_size=pattern_size,
        square_size_mm=square_size_mm,
        image_size=image_size,
        rms=round(float(rms), 6),
        camera_matrix=[[float(value) for value in row] for row in camera_matrix],
        distortion=[float(value) for value in distortion.reshape(-1)],
    )


def save_calibration(calibration: CameraCalibration, path: str | Path) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(calibration.to_dict(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return output
