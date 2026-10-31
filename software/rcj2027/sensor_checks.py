"""Analisi dei dati sonar e IMU per la diagnostica di banco.

Le funzioni di questo modulo sono pure: ricevono una sequenza di
``SensorReading`` e restituiscono un report con validita', statistiche e
motivi di fallimento. Non aprono porte seriali e non muovono il robot.
"""

from __future__ import annotations

import statistics
from collections.abc import Sequence
from dataclasses import dataclass

from .protocol import SensorReading

SEQUENCE_MODULO = 0x10000


@dataclass(frozen=True)
class NumericStats:
    count: int
    minimum: float
    maximum: float
    mean: float
    median: float
    stddev: float

    @classmethod
    def from_values(cls, values: Sequence[float]) -> "NumericStats | None":
        if not values:
            return None
        return cls(
            count=len(values),
            minimum=float(min(values)),
            maximum=float(max(values)),
            mean=float(statistics.fmean(values)),
            median=float(statistics.median(values)),
            stddev=float(statistics.pstdev(values)),
        )

    @property
    def span(self) -> float:
        return self.maximum - self.minimum


@dataclass(frozen=True)
class SonarReport:
    total: int
    valid: int
    invalid: int
    valid_ratio: float
    distances: NumericStats | None
    max_jump_mm: int | None
    outliers: int
    outlier_ratio: float
    outlier_mm: int
    flag_mismatches: int
    out_of_range: int
    sequence_gaps: int
    passed: bool
    notes: tuple[str, ...]


@dataclass(frozen=True)
class ReferenceCheck:
    expected_mm: int
    measured_mm: float | None
    mean_mm: float | None
    error_mm: float | None
    tolerance_mm: int
    passed: bool
    notes: tuple[str, ...]


@dataclass(frozen=True)
class ImuReport:
    total: int
    valid: int
    invalid: int
    valid_ratio: float
    yaw: NumericStats | None
    pitch: NumericStats | None
    roll: NumericStats | None
    yaw_drift_mdeg: int | None
    pitch_drift_mdeg: int | None
    roll_drift_mdeg: int | None
    stationary: bool
    motion_detected: bool
    dominant_axis: str | None
    expected_axis: str | None
    out_of_range: int
    sequence_gaps: int
    mode: str
    passed: bool
    notes: tuple[str, ...]


def sequence_gaps(readings: Sequence[SensorReading]) -> int:
    """Conta i salti nella sequenza degli status ricevuti."""
    gaps = 0
    for previous, current in zip(readings, readings[1:]):
        expected = (previous.sequence + 1) % SEQUENCE_MODULO
        if current.sequence != expected:
            gaps += 1
    return gaps


def analyze_sonar(
    readings: Sequence[SensorReading],
    *,
    min_valid_ratio: float = 0.8,
    outlier_mm: int = 200,
    max_outlier_ratio: float = 0.05,
    min_distance_mm: int = 20,
    max_distance_mm: int = 4000,
) -> SonarReport:
    """Verifica la coerenza dei campioni HC-SR04."""
    if not 0 <= max_outlier_ratio <= 1:
        raise ValueError("max_outlier_ratio deve essere tra 0 e 1")
    if outlier_mm < 0:
        raise ValueError("outlier_mm non puo' essere negativo")
    total = len(readings)
    valid_values: list[int] = []
    flag_mismatches = 0
    out_of_range = 0

    for reading in readings:
        flag = reading.flags["sonar_valid"]
        measured = reading.distance_mm > 0
        if flag != measured:
            flag_mismatches += 1

        if flag and measured:
            if min_distance_mm <= reading.distance_mm <= max_distance_mm:
                valid_values.append(reading.distance_mm)
            else:
                out_of_range += 1

    valid = len(valid_values)
    invalid = total - valid
    valid_ratio = valid / total if total else 0.0
    stats = NumericStats.from_values(valid_values)
    outliers = 0
    if stats is not None:
        outliers = sum(
            1 for value in valid_values if abs(value - stats.median) > outlier_mm
        )
    outlier_ratio = outliers / valid if valid else 0.0

    max_jump: int | None = None
    for previous, current in zip(valid_values, valid_values[1:]):
        jump = abs(current - previous)
        if max_jump is None or jump > max_jump:
            max_jump = jump

    notes: list[str] = []
    if total == 0:
        notes.append("nessun campione ricevuto")
    if total and valid_ratio < min_valid_ratio:
        notes.append(
            f"validi {valid}/{total} ({valid_ratio:.0%}) sotto la soglia "
            f"{min_valid_ratio:.0%}"
        )
    if flag_mismatches:
        notes.append(f"{flag_mismatches} campioni con flag sonar incoerente")
    if out_of_range:
        notes.append(f"{out_of_range} distanze fuori range {min_distance_mm}-{max_distance_mm} mm")
    if outlier_ratio > max_outlier_ratio:
        notes.append(
            f"{outliers}/{valid} outlier oltre ±{outlier_mm} mm "
            f"({outlier_ratio:.1%} > {max_outlier_ratio:.0%})"
        )
    gaps = sequence_gaps(readings)
    if gaps:
        notes.append(f"{gaps} salti nella sequenza degli status")

    passed = (
        total > 0
        and valid_ratio >= min_valid_ratio
        and flag_mismatches == 0
        and out_of_range == 0
        and gaps == 0
        and outlier_ratio <= max_outlier_ratio
    )

    return SonarReport(
        total=total,
        valid=valid,
        invalid=invalid,
        valid_ratio=round(valid_ratio, 3),
        distances=stats,
        max_jump_mm=max_jump,
        outliers=outliers,
        outlier_ratio=round(outlier_ratio, 3),
        outlier_mm=outlier_mm,
        flag_mismatches=flag_mismatches,
        out_of_range=out_of_range,
        sequence_gaps=gaps,
        passed=passed,
        notes=tuple(notes),
    )


def check_sonar_reference(
    report: SonarReport,
    expected_mm: int,
    *,
    tolerance_mm: int = 50,
) -> ReferenceCheck:
    """Confronta la distanza media con un riferimento misurato."""
    if expected_mm <= 0:
        raise ValueError("expected_mm deve essere positivo")
    if tolerance_mm < 0:
        raise ValueError("tolerance_mm non puo' essere negativo")

    if report.distances is None:
        return ReferenceCheck(
            expected_mm=expected_mm,
            measured_mm=None,
            mean_mm=None,
            error_mm=None,
            tolerance_mm=tolerance_mm,
            passed=False,
            notes=("nessuna distanza valida da confrontare",),
        )

    measured = report.distances.median
    error = measured - expected_mm
    passed = abs(error) <= tolerance_mm
    notes: tuple[str, ...] = ()
    if not passed:
        notes = (
            f"mediana {measured:.1f} mm, errore {error:+.1f} mm oltre la tolleranza "
            f"±{tolerance_mm} mm",
        )

    return ReferenceCheck(
        expected_mm=expected_mm,
        measured_mm=round(measured, 2),
        mean_mm=round(report.distances.mean, 2),
        error_mm=round(error, 2),
        tolerance_mm=tolerance_mm,
        passed=passed,
        notes=notes,
    )


def analyze_imu(
    readings: Sequence[SensorReading],
    *,
    mode: str = "stationary",
    expected_axis: str | None = None,
    min_valid_ratio: float = 0.8,
    settle_samples: int = 5,
    max_stationary_std_mdeg: float = 2000.0,
    max_stationary_span_mdeg: float = 5000.0,
    motion_span_mdeg: float = 5000.0,
) -> ImuReport:
    """Verifica i campioni BNO085 in modo stazionario o in movimento."""
    if mode not in {"stationary", "motion"}:
        raise ValueError("mode deve essere 'stationary' o 'motion'")
    if expected_axis not in {None, "yaw", "pitch", "roll"}:
        raise ValueError("expected_axis deve essere yaw, pitch, roll o None")

    total = len(readings)
    valid_readings = [reading for reading in readings if reading.flags["imu_valid"]]
    valid = len(valid_readings)
    invalid = total - valid
    valid_ratio = valid / total if total else 0.0

    out_of_range = 0
    for reading in valid_readings:
        if not -180000 <= reading.yaw_mdeg <= 180000:
            out_of_range += 1
        if not -90000 <= reading.pitch_mdeg <= 90000:
            out_of_range += 1
        if not -90000 <= reading.roll_mdeg <= 90000:
            out_of_range += 1

    analysis = (
        valid_readings[settle_samples:]
        if len(valid_readings) > settle_samples
        else valid_readings
    )
    yaw = NumericStats.from_values([reading.yaw_mdeg for reading in analysis])
    pitch = NumericStats.from_values([reading.pitch_mdeg for reading in analysis])
    roll = NumericStats.from_values([reading.roll_mdeg for reading in analysis])

    yaw_drift = None
    pitch_drift = None
    roll_drift = None
    if analysis:
        yaw_drift = analysis[-1].yaw_mdeg - analysis[0].yaw_mdeg
        pitch_drift = analysis[-1].pitch_mdeg - analysis[0].pitch_mdeg
        roll_drift = analysis[-1].roll_mdeg - analysis[0].roll_mdeg

    axes = [stats for stats in (yaw, pitch, roll) if stats is not None]
    stationary = bool(axes) and all(
        stats.stddev <= max_stationary_std_mdeg
        and stats.span <= max_stationary_span_mdeg
        for stats in axes
    )

    axis_stats = {"yaw": yaw, "pitch": pitch, "roll": roll}
    spans = {
        name: stats.span
        for name, stats in axis_stats.items()
        if stats is not None
    }
    dominant_axis = max(spans, key=spans.__getitem__) if spans else None
    if expected_axis is None:
        motion_detected = any(span > motion_span_mdeg for span in spans.values())
    else:
        motion_detected = spans.get(expected_axis, 0.0) > motion_span_mdeg

    notes: list[str] = []
    if total == 0:
        notes.append("nessun campione ricevuto")
    if total and valid_ratio < min_valid_ratio:
        notes.append(
            f"validi {valid}/{total} ({valid_ratio:.0%}) sotto la soglia "
            f"{min_valid_ratio:.0%}"
        )
    if out_of_range:
        notes.append(f"{out_of_range} angoli fuori range")
    if mode == "stationary" and axes and not stationary:
        notes.append("angoli non stabili: il robot o il sensore si sono mossi")
    if mode == "motion" and not motion_detected:
        if expected_axis is None:
            notes.append("nessun movimento rilevato: ruotare il robot durante il test")
        else:
            notes.append(
                f"asse {expected_axis} non rilevato; asse dominante: "
                f"{dominant_axis or 'nessuno'}"
            )
    gaps = sequence_gaps(readings)
    if gaps:
        notes.append(f"{gaps} salti nella sequenza degli status")

    if mode == "stationary":
        passed = (
            total > 0
            and valid_ratio >= min_valid_ratio
            and stationary
            and out_of_range == 0
            and gaps == 0
        )
    else:
        passed = (
            total > 0
            and valid_ratio >= min_valid_ratio
            and motion_detected
            and out_of_range == 0
            and gaps == 0
        )

    return ImuReport(
        total=total,
        valid=valid,
        invalid=invalid,
        valid_ratio=round(valid_ratio, 3),
        yaw=yaw,
        pitch=pitch,
        roll=roll,
        yaw_drift_mdeg=yaw_drift,
        pitch_drift_mdeg=pitch_drift,
        roll_drift_mdeg=roll_drift,
        stationary=stationary,
        motion_detected=motion_detected,
        dominant_axis=dominant_axis,
        expected_axis=expected_axis,
        out_of_range=out_of_range,
        sequence_gaps=gaps,
        mode=mode,
        passed=passed,
        notes=tuple(notes),
    )
