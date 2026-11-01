"""Primo pipeline di visione della linea nera (F0).

Il modulo e' volutamente indipendente dal movimento: legge un frame, applica
l'undistort della calibrazione, isola la linea nella regione davanti al robot e
restituisce offset, direzione e confidenza. Non invia comandi ai motori.

Convenzioni:

- l'immagine ha l'asse x verso destra e l'asse y verso il basso;
- ``offset_px`` positivo significa che la linea, in basso, e' a destra dell'asse
  ottico della telecamera;
- ``heading_deg`` positivo significa che la linea, guardando avanti, piega a
  destra. E' calcolato in coordinate immagine, non in metri.
"""

from __future__ import annotations

import json
import math
import time
from dataclasses import dataclass, field
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


class LineVisionError(RuntimeError):
    """Frame, calibrazione o configurazione non validi."""


@dataclass(frozen=True)
class CameraModel:
    """Intrinseci e distorsione di una telecamera calibrata."""

    image_size: tuple[int, int]
    camera_matrix: Any
    distortion: Any
    rms: float | None = None
    source: str | None = None

    def __post_init__(self) -> None:
        if not HAS_CV2:
            raise LineVisionError(
                "OpenCV/numpy non installati: pip install -r software/requirements.txt"
            )
        width, height = self.image_size
        if width <= 0 or height <= 0:
            raise LineVisionError("image_size deve essere positiva")
        matrix = np.asarray(self.camera_matrix, dtype=np.float64)
        distortion = np.asarray(self.distortion, dtype=np.float64).reshape(-1)
        if matrix.shape != (3, 3):
            raise LineVisionError("camera_matrix deve essere 3x3")
        if distortion.size < 4:
            raise LineVisionError("distortion deve avere almeno 4 coefficienti")
        if not np.isfinite(matrix).all() or not np.isfinite(distortion).all():
            raise LineVisionError("calibrazione con valori non finiti")
        if matrix[0, 0] <= 0 or matrix[1, 1] <= 0:
            raise LineVisionError("focale non valida nella calibrazione")
        if abs(matrix[2, 2] - 1.0) > 1e-9:
            raise LineVisionError("camera_matrix con ultimo elemento diverso da 1")
        if not np.isfinite(np.linalg.det(matrix)) or abs(np.linalg.det(matrix)) < 1e-12:
            raise LineVisionError("camera_matrix singolare")
        object.__setattr__(self, "camera_matrix", matrix)
        object.__setattr__(self, "distortion", distortion)

    @property
    def width(self) -> int:
        return self.image_size[0]

    @property
    def height(self) -> int:
        return self.image_size[1]

    @property
    def cx(self) -> float:
        return float(self.camera_matrix[0, 2])

    @property
    def cy(self) -> float:
        return float(self.camera_matrix[1, 2])

    def to_dict(self) -> dict[str, Any]:
        return {
            "image_size": [self.width, self.height],
            "camera_matrix": np.asarray(self.camera_matrix).tolist(),
            "distortion": np.asarray(self.distortion).reshape(-1).tolist(),
            "rms": self.rms,
            "source": self.source,
        }


def load_camera_model(path: str | Path) -> CameraModel:
    """Carica un JSON prodotto da ``camera-calibrate`` e lo valida."""
    if not HAS_CV2:
        raise LineVisionError(
            "OpenCV/numpy non installati: pip install -r software/requirements.txt"
        )
    calibration_path = Path(path)
    try:
        data = json.loads(calibration_path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise LineVisionError(f"calibrazione non leggibile: {calibration_path}") from exc
    except json.JSONDecodeError as exc:
        raise LineVisionError(f"calibrazione JSON non valida: {calibration_path}") from exc

    try:
        image_size = tuple(int(value) for value in data["image_size"])
        camera_matrix = data["camera_matrix"]
        distortion = data["distortion"]
    except (KeyError, TypeError, ValueError) as exc:
        raise LineVisionError(
            f"calibrazione incompleta: {calibration_path}"
        ) from exc
    if len(image_size) != 2:
        raise LineVisionError(f"image_size non valida in {calibration_path}")
    rms = data.get("rms")
    return CameraModel(
        image_size=(image_size[0], image_size[1]),
        camera_matrix=camera_matrix,
        distortion=distortion,
        rms=float(rms) if rms is not None else None,
        source=str(calibration_path),
    )


@dataclass(frozen=True)
class LineConfig:
    """Parametri del rilevamento, espressi in frazioni del frame quando possibile."""

    roi_top: float = 0.55
    roi_bottom: float = 0.98
    roi_left: float = 0.02
    roi_right: float = 0.98
    scan_rows: int = 60
    threshold_block: int | None = None
    threshold_c: float = 10.0
    dark_threshold: float = 80.0
    dark_max_fraction: float = 0.25
    blur_ksize: int = 5
    clahe_clip: float = 2.0
    clahe_grid: int = 8
    min_run_px: int = 8
    max_run_ratio: float = 0.60
    max_jump_ratio: float = 0.08
    min_valid_ratio: float = 0.45
    min_confidence: float = 0.35
    max_heading_deg: float = 75.0
    fit_residual_px: float = 4.0
    width_variation_ratio: float = 0.35
    polynomial_degree: int = 2

    def __post_init__(self) -> None:
        if not 0.0 <= self.roi_top < self.roi_bottom <= 1.0:
            raise LineVisionError("ROI verticale non valida")
        if not 0.0 <= self.roi_left < self.roi_right <= 1.0:
            raise LineVisionError("ROI orizzontale non valida")
        if self.scan_rows < 5:
            raise LineVisionError("scan_rows deve essere almeno 5")
        if self.threshold_block is not None and (
            self.threshold_block < 3 or self.threshold_block % 2 == 0
        ):
            raise LineVisionError("threshold_block deve essere dispari e >= 3")
        if self.threshold_c < 0:
            raise LineVisionError("threshold_c non puo' essere negativo")
        if not 0 <= self.dark_threshold <= 255:
            raise LineVisionError("dark_threshold deve essere tra 0 e 255")
        if not 0 <= self.dark_max_fraction <= 1:
            raise LineVisionError("dark_max_fraction deve essere tra 0 e 1")
        if self.blur_ksize < 1 or self.blur_ksize % 2 == 0:
            raise LineVisionError("blur_ksize deve essere dispari e >= 1")
        if self.min_run_px < 1:
            raise LineVisionError("min_run_px deve essere positivo")
        if not 0 < self.max_run_ratio <= 1:
            raise LineVisionError("max_run_ratio deve essere tra 0 e 1")
        if not 0 < self.max_jump_ratio <= 1:
            raise LineVisionError("max_jump_ratio deve essere tra 0 e 1")
        if not 0 <= self.min_valid_ratio <= 1:
            raise LineVisionError("min_valid_ratio deve essere tra 0 e 1")
        if not 0 <= self.min_confidence <= 1:
            raise LineVisionError("min_confidence deve essere tra 0 e 1")
        if not 0 < self.max_heading_deg <= 90:
            raise LineVisionError("max_heading_deg deve essere tra 0 e 90")
        if self.fit_residual_px <= 0:
            raise LineVisionError("fit_residual_px deve essere positivo")
        if self.width_variation_ratio <= 0:
            raise LineVisionError("width_variation_ratio deve essere positivo")
        if self.polynomial_degree not in (1, 2):
            raise LineVisionError("polynomial_degree deve essere 1 o 2")


@dataclass(frozen=True)
class LineObservation:
    """Misure di un singolo frame. I valori restano validi solo se ``found``."""

    found: bool
    offset_px: float
    offset_ratio: float
    heading_deg: float
    confidence: float
    valid_rows: int
    scan_rows: int
    line_width_px: float
    residual_px: float
    line_x_bottom_px: float
    optical_x_px: float
    roi: tuple[int, int, int, int]
    processing_ms: float
    undistorted: bool
    reason: str = "ok"

    def to_dict(self) -> dict[str, Any]:
        return {
            "found": self.found,
            "offset_px": round(self.offset_px, 2),
            "offset_ratio": round(self.offset_ratio, 5),
            "heading_deg": round(self.heading_deg, 2),
            "confidence": round(self.confidence, 4),
            "valid_rows": self.valid_rows,
            "scan_rows": self.scan_rows,
            "line_width_px": round(self.line_width_px, 2),
            "residual_px": round(self.residual_px, 3),
            "line_x_bottom_px": round(self.line_x_bottom_px, 2),
            "optical_x_px": round(self.optical_x_px, 2),
            "roi": list(self.roi),
            "processing_ms": round(self.processing_ms, 2),
            "undistorted": self.undistorted,
            "reason": self.reason,
        }


@dataclass(frozen=True)
class LineDebug:
    """Dati intermedi usati per disegnare il frame annotato."""

    frame: Any
    mask: Any
    points: tuple[tuple[float, float, int], ...]
    roi: tuple[int, int, int, int]
    polynomial: tuple[float, float, float] | None
    bottom_y: int
    roi_height: int
    optical_x: float


def _as_gray(frame: Any) -> Any:
    if not HAS_CV2:
        raise LineVisionError(
            "OpenCV/numpy non installati: pip install -r software/requirements.txt"
        )
    if frame is None or not hasattr(frame, "ndim"):
        raise LineVisionError("frame vuoto o non valido")
    if frame.ndim == 2:
        return frame
    if frame.ndim != 3:
        raise LineVisionError(f"frame con {frame.ndim} dimensioni non supportato")
    if frame.shape[2] == 3:
        return cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    if frame.shape[2] == 4:
        return cv2.cvtColor(frame, cv2.COLOR_BGRA2GRAY)
    raise LineVisionError(f"frame con {frame.shape[2]} canali non supportato")


def read_image(path: str | Path) -> Any:
    """Legge un frame da disco e fallisce con un messaggio esplicito."""
    if not HAS_CV2:
        raise LineVisionError(
            "OpenCV/numpy non installati: pip install -r software/requirements.txt"
        )
    source = Path(path)
    if not source.exists():
        raise LineVisionError(f"immagine non trovata: {source}")
    frame = cv2.imread(str(source))
    if frame is None:
        raise LineVisionError(f"immagine non leggibile: {source}")
    return frame


def write_image(path: str | Path, image: Any) -> Path:
    """Salva un frame annotato o una maschera."""
    if not HAS_CV2:
        raise LineVisionError(
            "OpenCV/numpy non installati: pip install -r software/requirements.txt"
        )
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    if not cv2.imwrite(str(output), image):
        raise LineVisionError(f"impossibile salvare l'immagine in {output}")
    return output


def _roi_bounds(width: int, height: int, config: LineConfig) -> tuple[int, int, int, int]:
    left = int(round(width * config.roi_left))
    right = int(round(width * config.roi_right))
    top = int(round(height * config.roi_top))
    bottom = int(round(height * config.roi_bottom))
    left = max(0, min(left, width - 2))
    right = max(left + 2, min(right, width))
    top = max(0, min(top, height - 2))
    bottom = max(top + 2, min(bottom, height))
    return left, top, right, bottom


def _auto_block_size(width: int, height: int) -> int:
    block = int(round(width * 0.12))
    if block % 2 == 0:
        block += 1
    block = max(31, block)
    limit = min(width, height)
    if limit % 2 == 0:
        limit -= 1
    return max(3, min(block, limit))


def _merge_nearby_runs(
    runs: list[tuple[int, int]], max_gap: int
) -> list[tuple[int, int]]:
    """Unisce run separate da pochi pixel, tipiche di una linea tagliata a meta'."""
    if not runs:
        return []
    merged = [runs[0]]
    for start, end in runs[1:]:
        last_start, last_end = merged[-1]
        if start - last_end <= max_gap:
            merged[-1] = (last_start, end)
        else:
            merged.append((start, end))
    return merged


def _row_runs(row: Any, min_width: int, max_width: int) -> list[tuple[int, int]]:
    binary = row > 0
    changes = np.diff(np.concatenate(([0], binary.view(np.int8), [0])))
    starts = np.where(changes == 1)[0]
    ends = np.where(changes == -1)[0]
    runs = [(int(start), int(end)) for start, end in zip(starts, ends)]
    gap = max(2, min_width // 3)
    runs = _merge_nearby_runs(runs, gap)
    return [
        (start, end)
        for start, end in runs
        if min_width <= end - start <= max_width
    ]


def _fit_polynomial(
    points: Any,
    bottom_y: int,
    roi_height: int,
    degree: int,
    residual_px: float,
) -> tuple[Any, Any, float]:
    """Fit robusto x(y); restituisce coefficienti, punti mantenuti e residuo RMS."""
    t = (points[:, 1] - bottom_y) / roi_height
    coefficient = np.polyfit(t, points[:, 0], degree)
    keep = np.ones(len(points), dtype=bool)
    for _ in range(2):
        residual = points[:, 0] - np.polyval(coefficient, t)
        median_abs = float(np.median(np.abs(residual)))
        limit = max(3.0 * 1.4826 * median_abs, residual_px * 0.5)
        candidate = np.abs(residual) <= limit
        if int(candidate.sum()) < max(5, degree + 2):
            keep = np.ones(len(points), dtype=bool)
            break
        keep = candidate
        coefficient = np.polyfit(t[keep], points[keep, 0], degree)
    residual = points[keep, 0] - np.polyval(coefficient, t[keep])
    rms = float(np.sqrt(np.mean(residual**2))) if len(residual) else float("inf")
    return coefficient, points[keep], rms


def _width_score(points: Any, max_variation_ratio: float) -> float:
    """Quanto il bordo ha larghezza regolare lungo la linea."""
    if len(points) < 3:
        return 1.0
    widths = points[:, 2]
    median_width = float(np.median(widths))
    if median_width <= 0:
        return 0.0
    coefficient = np.polyfit(points[:, 1], widths, 1)
    residual = widths - np.polyval(coefficient, points[:, 1])
    ratio = float(np.median(np.abs(residual))) / median_width
    # La larghezza prospettica varia in modo graduale: il termine e' un
    # correttivo, non un veto, per non perdere linee reali molto inclinate.
    return max(0.5, min(1.0, 1.0 - ratio / max_variation_ratio))


class LineDetector:
    """Rilevatore con cache delle mappe di undistort per una sequenza di frame."""

    def __init__(
        self,
        camera_model: CameraModel | None = None,
        config: LineConfig | None = None,
    ) -> None:
        self.camera_model = camera_model
        self.config = config or LineConfig()
        self._maps: tuple[Any, Any] | None = None

    def undistort(self, frame: Any) -> Any:
        if self.camera_model is None:
            return frame
        height, width = frame.shape[:2]
        if (width, height) != self.camera_model.image_size:
            raise LineVisionError(
                f"frame {width}x{height} diverso dalla calibrazione "
                f"{self.camera_model.width}x{self.camera_model.height}; "
                "la calibrazione e' legata alla risoluzione"
            )
        if self._maps is None:
            matrix = np.asarray(self.camera_model.camera_matrix, dtype=np.float64)
            distortion = np.asarray(
                self.camera_model.distortion, dtype=np.float64
            ).reshape(-1)
            self._maps = cv2.initUndistortRectifyMap(
                matrix,
                distortion,
                None,
                matrix,
                self.camera_model.image_size,
                cv2.CV_16SC2,
            )
        map_x, map_y = self._maps
        return cv2.remap(
            frame,
            map_x,
            map_y,
            interpolation=cv2.INTER_LINEAR,
            borderMode=cv2.BORDER_REPLICATE,
        )

    def detect(
        self, frame: Any, *, debug: bool = False
    ) -> LineObservation | tuple[LineObservation, LineDebug]:
        started = time.perf_counter()
        if frame is None or not hasattr(frame, "ndim"):
            raise LineVisionError("frame vuoto o non valido")
        working = self.undistort(frame) if self.camera_model is not None else frame
        gray = _as_gray(working)

        height, width = gray.shape[:2]
        left, top, right, bottom = _roi_bounds(width, height, self.config)
        roi = gray[top:bottom, left:right]
        roi_height, roi_width = roi.shape[:2]

        enhanced = cv2.createCLAHE(
            clipLimit=self.config.clahe_clip,
            tileGridSize=(self.config.clahe_grid, self.config.clahe_grid),
        ).apply(roi)
        if self.config.blur_ksize > 1:
            enhanced = cv2.GaussianBlur(
                enhanced, (self.config.blur_ksize, self.config.blur_ksize), 0
            )
        block = (
            self.config.threshold_block
            if self.config.threshold_block is not None
            else _auto_block_size(roi_width, roi_height)
        )
        mask = cv2.adaptiveThreshold(
            enhanced,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY_INV,
            block,
            self.config.threshold_c,
        )
        # Una linea molto vicina alla camera puo' essere piu' larga del blocco
        # adattivo: in quel caso il centro resta chiaro. Aggiungiamo i pixel
        # sotto una soglia scura fissa, ma solo se non invadono il frame.
        _, dark_mask = cv2.threshold(
            enhanced,
            self.config.dark_threshold,
            255,
            cv2.THRESH_BINARY_INV,
        )
        if float(np.count_nonzero(dark_mask)) / dark_mask.size <= (
            self.config.dark_max_fraction
        ):
            mask = cv2.bitwise_or(mask, dark_mask)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))

        scan_rows = int(
            min(self.config.scan_rows, max(5, roi_height))
        )
        rows = np.unique(
            np.linspace(roi_height - 1, 0, scan_rows).astype(int)
        )[::-1]
        max_run = max(1, int(round(roi_width * self.config.max_run_ratio)))
        max_jump = max(4, int(round(roi_width * self.config.max_jump_ratio)))

        previous_x = roi_width / 2.0
        points: list[tuple[float, float, int]] = []
        for index, row_index in enumerate(rows):
            runs = _row_runs(mask[row_index], self.config.min_run_px, max_run)
            if not runs:
                continue
            candidates = [
                ((start + end - 1) / 2.0, end - start) for start, end in runs
            ]
            center, line_width = min(
                candidates, key=lambda item: abs(item[0] - previous_x)
            )
            if index > 0 and abs(center - previous_x) > max_jump:
                continue
            points.append((center, float(row_index + top), line_width))
            previous_x = center

        optical_x = (
            self.camera_model.cx
            if self.camera_model is not None
            else (width - 1) / 2.0
        )
        roi_tuple = (left, top, right, bottom)

        minimum_rows = max(5, int(round(len(rows) * self.config.min_valid_ratio)))
        if len(points) < minimum_rows:
            processing_ms = (time.perf_counter() - started) * 1000.0
            observation = LineObservation(
                found=False,
                offset_px=0.0,
                offset_ratio=0.0,
                heading_deg=0.0,
                confidence=0.0,
                valid_rows=len(points),
                scan_rows=len(rows),
                line_width_px=0.0,
                residual_px=0.0,
                line_x_bottom_px=optical_x,
                optical_x_px=optical_x,
                roi=roi_tuple,
                processing_ms=processing_ms,
                undistorted=self.camera_model is not None,
                reason="few_rows",
            )
            debug_data = LineDebug(
                frame=working,
                mask=mask,
                points=tuple(points),
                roi=roi_tuple,
                polynomial=None,
                bottom_y=bottom - 1,
                roi_height=roi_height,
                optical_x=optical_x,
            )
            return (observation, debug_data) if debug else observation

        array = np.asarray(points, dtype=np.float64)
        coefficient, inliers, rms = _fit_polynomial(
            array,
            bottom - 1,
            roi_height,
            self.config.polynomial_degree,
            self.config.fit_residual_px,
        )
        residual_score = max(
            0.0, min(1.0, 1.0 - rms / self.config.fit_residual_px)
        )
        coverage = len(inliers) / len(rows)
        confidence = coverage * residual_score * _width_score(
            inliers, self.config.width_variation_ratio
        )

        line_x = float(np.polyval(coefficient, 0.0)) + left
        offset = line_x - optical_x
        t_heading = -0.25
        derivative = (
            2.0 * coefficient[0] * t_heading + coefficient[1]
        ) / roi_height
        heading = -math.degrees(math.atan(derivative))
        line_width = float(np.median(inliers[:, 2])) if len(inliers) else 0.0

        reason = "ok"
        if abs(heading) > self.config.max_heading_deg:
            reason = "heading"
        elif confidence < self.config.min_confidence:
            reason = "low_confidence"
        found = reason == "ok"
        processing_ms = (time.perf_counter() - started) * 1000.0

        observation = LineObservation(
            found=found,
            offset_px=offset,
            offset_ratio=offset / width,
            heading_deg=heading,
            confidence=confidence,
            valid_rows=len(inliers),
            scan_rows=len(rows),
            line_width_px=line_width,
            residual_px=rms,
            line_x_bottom_px=line_x,
            optical_x_px=optical_x,
            roi=roi_tuple,
            processing_ms=processing_ms,
            undistorted=self.camera_model is not None,
            reason=reason,
        )
        debug_data = LineDebug(
            frame=working,
            mask=mask,
            points=tuple(points),
            roi=roi_tuple,
            polynomial=tuple(float(value) for value in coefficient),
            bottom_y=bottom - 1,
            roi_height=roi_height,
            optical_x=optical_x,
        )
        return (observation, debug_data) if debug else observation


def detect_line(
    frame: Any,
    camera_model: CameraModel | None = None,
    config: LineConfig | None = None,
) -> LineObservation:
    """Scorciatoia per un singolo frame, senza cache delle mappe."""
    return LineDetector(camera_model, config).detect(frame)  # type: ignore[return-value]


def annotate_frame(
    debug: LineDebug,
    observation: LineObservation,
) -> Any:
    """Disegna ROI, punti, fit e misure sul frame di lavoro."""
    if not HAS_CV2:
        raise LineVisionError("OpenCV non disponibile")
    frame = debug.frame
    if frame.ndim == 2:
        frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
    else:
        frame = frame.copy()

    left, top, right, bottom = debug.roi
    color = (0, 200, 0) if observation.found else (0, 0, 220)
    cv2.rectangle(frame, (left, top), (right - 1, bottom - 1), (160, 160, 160), 1)
    cv2.line(
        frame,
        (int(round(debug.optical_x)), top),
        (int(round(debug.optical_x)), bottom - 1),
        (0, 220, 220),
        1,
    )
    for x, y, _ in debug.points:
        cv2.circle(frame, (int(round(x + left)), int(round(y))), 2, color, -1)
    if debug.polynomial is not None:
        curve = []
        for step in range(0, 101):
            t = -step / 100.0
            x = float(np.polyval(debug.polynomial, t)) + left
            y = debug.bottom_y + t * debug.roi_height
            curve.append((int(round(x)), int(round(y))))
        cv2.polylines(frame, [np.asarray(curve, dtype=np.int32)], False, (255, 120, 0), 2)
        bottom_x = int(round(float(np.polyval(debug.polynomial, 0.0)) + left))
        cv2.line(
            frame,
            (int(round(debug.optical_x)), debug.bottom_y),
            (bottom_x, debug.bottom_y),
            color,
            2,
        )
        cv2.circle(frame, (bottom_x, debug.bottom_y), 4, color, -1)

    text = (
        f"{'FOUND' if observation.found else 'LOST'} "
        f"offset={observation.offset_px:+.1f}px "
        f"heading={observation.heading_deg:+.1f}deg "
        f"conf={observation.confidence:.2f}"
    )
    cv2.putText(
        frame,
        text,
        (left + 4, max(18, top - 6)),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.55,
        color,
        1,
        cv2.LINE_AA,
    )
    return frame


@dataclass(frozen=True)
class TrackState:
    """Stato filtrato della linea, con conferma temporale."""

    found: bool
    confirmed: bool
    offset_px: float
    heading_deg: float
    confidence: float
    lost_frames: int
    found_streak: int
    recoveries: int


class LineTracker:
    """Filtro esponenziale e conferma su piu' frame.

    La conferma evita che un singolo falso positivo faccia partire il controllo.
    Dopo ``max_lost_frames`` frame senza linea lo stato confermato viene perso.
    """

    def __init__(
        self,
        *,
        alpha: float = 0.35,
        confirm_frames: int = 3,
        max_lost_frames: int = 5,
    ) -> None:
        if not 0 < alpha <= 1:
            raise ValueError("alpha deve essere tra 0 e 1")
        if confirm_frames < 1:
            raise ValueError("confirm_frames deve essere positivo")
        if max_lost_frames < 0:
            raise ValueError("max_lost_frames non puo' essere negativo")
        self.alpha = alpha
        self.confirm_frames = confirm_frames
        self.max_lost_frames = max_lost_frames
        self.offset_px = 0.0
        self.heading_deg = 0.0
        self.confidence = 0.0
        self.lost_frames = 0
        self.found_streak = 0
        self.recoveries = 0
        self.confirmed = False
        self._ever_confirmed = False
        self._initialized = False

    def update(self, observation: LineObservation) -> TrackState:
        if observation.found:
            if not self._initialized:
                self.offset_px = observation.offset_px
                self.heading_deg = observation.heading_deg
                self.confidence = observation.confidence
                self._initialized = True
            else:
                alpha = self.alpha
                self.offset_px = (
                    alpha * observation.offset_px + (1 - alpha) * self.offset_px
                )
                self.heading_deg = (
                    alpha * observation.heading_deg
                    + (1 - alpha) * self.heading_deg
                )
                self.confidence = (
                    alpha * observation.confidence
                    + (1 - alpha) * self.confidence
                )
            self.lost_frames = 0
            self.found_streak += 1
            if self.found_streak >= self.confirm_frames:
                if not self.confirmed and self._ever_confirmed:
                    self.recoveries += 1
                self.confirmed = True
                self._ever_confirmed = True
        else:
            self.lost_frames += 1
            self.found_streak = 0
            if self.lost_frames > self.max_lost_frames:
                self.confirmed = False
                self._initialized = False

        return TrackState(
            found=observation.found,
            confirmed=self.confirmed,
            offset_px=self.offset_px,
            heading_deg=self.heading_deg,
            confidence=self.confidence,
            lost_frames=self.lost_frames,
            found_streak=self.found_streak,
            recoveries=self.recoveries,
        )


@dataclass(frozen=True)
class UndistortFrameReport:
    image: str
    detected: bool
    raw_mean_px: float | None = None
    raw_max_px: float | None = None
    undistorted_mean_px: float | None = None
    undistorted_max_px: float | None = None
    shift_mean_px: float | None = None
    shift_max_px: float | None = None
    error: str | None = None


@dataclass(frozen=True)
class UndistortReport:
    calibration: str
    pattern_size: tuple[int, int]
    images: int
    accepted: int
    raw_mean_px: float
    undistorted_mean_px: float
    shift_mean_px: float
    shift_max_px: float
    improvement_ratio: float
    tolerance_px: float
    max_mean_residual_px: float
    passed: bool
    frames: tuple[UndistortFrameReport, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return {
            "calibration": self.calibration,
            "pattern_size": list(self.pattern_size),
            "images": self.images,
            "accepted": self.accepted,
            "raw_mean_px": round(self.raw_mean_px, 4),
            "undistorted_mean_px": round(self.undistorted_mean_px, 4),
            "shift_mean_px": round(self.shift_mean_px, 4),
            "shift_max_px": round(self.shift_max_px, 4),
            "improvement_ratio": round(self.improvement_ratio, 4),
            "tolerance_px": self.tolerance_px,
            "max_mean_residual_px": self.max_mean_residual_px,
            "passed": self.passed,
            "frames": [
                {
                    "image": frame.image,
                    "detected": frame.detected,
                    "raw_mean_px": (
                        round(frame.raw_mean_px, 4)
                        if frame.raw_mean_px is not None
                        else None
                    ),
                    "raw_max_px": (
                        round(frame.raw_max_px, 4)
                        if frame.raw_max_px is not None
                        else None
                    ),
                    "undistorted_mean_px": (
                        round(frame.undistorted_mean_px, 4)
                        if frame.undistorted_mean_px is not None
                        else None
                    ),
                    "undistorted_max_px": (
                        round(frame.undistorted_max_px, 4)
                        if frame.undistorted_max_px is not None
                        else None
                    ),
                    "shift_mean_px": (
                        round(frame.shift_mean_px, 4)
                        if frame.shift_mean_px is not None
                        else None
                    ),
                    "shift_max_px": (
                        round(frame.shift_max_px, 4)
                        if frame.shift_max_px is not None
                        else None
                    ),
                    "error": frame.error,
                }
                for frame in self.frames
            ],
        }


def _homography_residual(corners: Any, pattern_size: tuple[int, int]) -> tuple[float, float]:
    grid = np.mgrid[0 : pattern_size[0], 0 : pattern_size[1]]
    object_points = grid.T.reshape(-1, 2).astype(np.float32)
    image_points = corners.reshape(-1, 1, 2).astype(np.float32)
    matrix, _ = cv2.findHomography(object_points, image_points, 0)
    if matrix is None:
        return float("inf"), float("inf")
    projected = cv2.perspectiveTransform(
        object_points.reshape(-1, 1, 2), matrix
    ).reshape(-1, 2)
    errors = np.linalg.norm(projected - image_points.reshape(-1, 2), axis=1)
    return float(errors.mean()), float(errors.max())


def validate_undistortion(
    images: Iterable[str | Path],
    camera_model: CameraModel,
    *,
    pattern_size: tuple[int, int] = (9, 6),
    min_images: int = 3,
    tolerance_px: float = 0.05,
    max_mean_residual_px: float = 1.0,
) -> UndistortReport:
    """Confronta l'errore di omografia prima e dopo l'undistort.

    Le immagini checkerboard usate per la calibrazione non sono una prova
    indipendente: il report serve a verificare che la mappa non peggiori il
    modello, non a stimare la distorsione. La verifica definitiva e' visiva su
    una linea retta reale ai bordi del frame.
    """
    if not HAS_CV2:
        raise LineVisionError(
            "OpenCV/numpy non installati: pip install -r software/requirements.txt"
        )
    if min_images < 1:
        raise ValueError("min_images deve essere positivo")
    if tolerance_px < 0 or max_mean_residual_px <= 0:
        raise ValueError("soglie non valide")

    matrix = np.asarray(camera_model.camera_matrix, dtype=np.float64)
    distortion = np.asarray(camera_model.distortion, dtype=np.float64).reshape(-1)
    frames: list[UndistortFrameReport] = []
    raw_values: list[float] = []
    undistorted_values: list[float] = []
    shift_means: list[float] = []
    shift_maxima: list[float] = []

    criteria = (
        cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER,
        30,
        0.001,
    )
    for image in images:
        path = Path(image)
        frame = cv2.imread(str(path))
        if frame is None:
            frames.append(
                UndistortFrameReport(
                    image=str(path), detected=False, error="immagine non leggibile"
                )
            )
            continue
        height, width = frame.shape[:2]
        if (width, height) != camera_model.image_size:
            frames.append(
                UndistortFrameReport(
                    image=str(path),
                    detected=False,
                    error=(
                        f"risoluzione {width}x{height} diversa dalla calibrazione "
                        f"{camera_model.width}x{camera_model.height}"
                    ),
                )
            )
            continue
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        found, corners = cv2.findChessboardCorners(
            gray,
            pattern_size,
            flags=cv2.CALIB_CB_ADAPTIVE_THRESH | cv2.CALIB_CB_NORMALIZE_IMAGE,
        )
        if not found or corners is None:
            frames.append(
                UndistortFrameReport(
                    image=str(path), detected=False, error="checkerboard non rilevato"
                )
            )
            continue
        corners = cv2.cornerSubPix(
            gray, corners, (11, 11), (-1, -1), criteria
        )
        undistorted_corners = cv2.undistortPoints(
            corners, matrix, distortion, P=matrix
        )
        raw_mean, raw_max = _homography_residual(corners, pattern_size)
        und_mean, und_max = _homography_residual(
            undistorted_corners, pattern_size
        )
        shift = np.linalg.norm(
            undistorted_corners.reshape(-1, 2) - corners.reshape(-1, 2), axis=1
        )
        raw_values.append(raw_mean)
        undistorted_values.append(und_mean)
        shift_means.append(float(shift.mean()))
        shift_maxima.append(float(shift.max()))
        frames.append(
            UndistortFrameReport(
                image=str(path),
                detected=True,
                raw_mean_px=raw_mean,
                raw_max_px=raw_max,
                undistorted_mean_px=und_mean,
                undistorted_max_px=und_max,
                shift_mean_px=float(shift.mean()),
                shift_max_px=float(shift.max()),
            )
        )

    accepted = len(raw_values)
    if accepted < min_images:
        raise LineVisionError(
            f"checkerboard valido in {accepted} immagini, ne servono almeno "
            f"{min_images}"
        )
    raw_mean = float(np.mean(raw_values))
    undistorted_mean = float(np.mean(undistorted_values))
    shift_mean = float(np.mean(shift_means))
    shift_max = float(np.max(shift_maxima))
    improvement = (
        (raw_mean - undistorted_mean) / raw_mean if raw_mean > 0 else 0.0
    )
    passed = (
        undistorted_mean <= raw_mean + tolerance_px
        and undistorted_mean <= max_mean_residual_px
    )
    return UndistortReport(
        calibration=camera_model.source or "",
        pattern_size=pattern_size,
        images=len(frames),
        accepted=accepted,
        raw_mean_px=raw_mean,
        undistorted_mean_px=undistorted_mean,
        shift_mean_px=shift_mean,
        shift_max_px=shift_max,
        improvement_ratio=improvement,
        tolerance_px=tolerance_px,
        max_mean_residual_px=max_mean_residual_px,
        passed=passed,
        frames=tuple(frames),
    )
