from __future__ import annotations

import unittest

from rcj2027.protocol import SensorReading
from rcj2027.sensor_checks import (
    analyze_imu,
    analyze_sonar,
    check_sonar_reference,
    sequence_gaps,
)


def reading(
    sequence: int,
    *,
    distance_mm: int = -1,
    yaw_mdeg: int = 0,
    pitch_mdeg: int = 0,
    roll_mdeg: int = 0,
    status: int = 0,
) -> SensorReading:
    return SensorReading(
        sequence=sequence,
        distance_mm=distance_mm,
        yaw_mdeg=yaw_mdeg,
        pitch_mdeg=pitch_mdeg,
        roll_mdeg=roll_mdeg,
        status=status,
    )


class SonarChecksTests(unittest.TestCase):
    def test_valid_sequence_passes(self) -> None:
        readings = [reading(index, distance_mm=1000 + index * 10, status=1) for index in range(3)]

        report = analyze_sonar(readings)

        self.assertTrue(report.passed)
        self.assertEqual(report.total, 3)
        self.assertEqual(report.valid, 3)
        self.assertEqual(report.valid_ratio, 1.0)
        self.assertEqual(report.max_jump_mm, 10)
        self.assertEqual(report.sequence_gaps, 0)
        self.assertIsNotNone(report.distances)
        self.assertEqual(report.distances.minimum, 1000)
        self.assertEqual(report.distances.maximum, 1020)
        self.assertAlmostEqual(report.distances.mean, 1010.0)
        self.assertAlmostEqual(report.distances.median, 1010.0)
        self.assertAlmostEqual(report.distances.stddev, 8.165, places=3)

    def test_flag_mismatch_fails(self) -> None:
        readings = [
            reading(0, distance_mm=-1, status=1),
            reading(1, distance_mm=1000, status=0),
        ]

        report = analyze_sonar(readings)

        self.assertFalse(report.passed)
        self.assertEqual(report.flag_mismatches, 2)
        self.assertEqual(report.valid, 0)

    def test_large_jump_fails(self) -> None:
        readings = [
            reading(0, distance_mm=500, status=1),
            reading(1, distance_mm=1500, status=1),
        ]

        report = analyze_sonar(readings)

        self.assertFalse(report.passed)
        self.assertEqual(report.max_jump_mm, 1000)
        self.assertEqual(report.outlier_ratio, 1.0)
        self.assertIn("outlier", " ".join(report.notes))

    def test_single_isolated_outlier_passes(self) -> None:
        readings = [
            reading(index, distance_mm=500, status=1)
            for index in range(99)
        ] + [reading(99, distance_mm=1100, status=1)]

        report = analyze_sonar(readings)

        self.assertTrue(report.passed)
        self.assertEqual(report.outliers, 1)
        self.assertEqual(report.outlier_ratio, 0.01)
        self.assertEqual(report.max_jump_mm, 600)

    def test_many_outliers_fail(self) -> None:
        readings = [
            reading(index, distance_mm=500, status=1)
            for index in range(90)
        ] + [
            reading(90 + index, distance_mm=1100, status=1)
            for index in range(10)
        ]

        report = analyze_sonar(readings)

        self.assertFalse(report.passed)
        self.assertGreater(report.outlier_ratio, 0.05)

    def test_out_of_range_fails(self) -> None:
        report = analyze_sonar([reading(0, distance_mm=5000, status=1)])

        self.assertFalse(report.passed)
        self.assertEqual(report.out_of_range, 1)

    def test_sequence_gap_fails(self) -> None:
        readings = [
            reading(0, distance_mm=1000, status=1),
            reading(2, distance_mm=1000, status=1),
        ]

        report = analyze_sonar(readings)

        self.assertEqual(report.sequence_gaps, 1)
        self.assertFalse(report.passed)

    def test_empty_sequence_fails(self) -> None:
        report = analyze_sonar([])

        self.assertFalse(report.passed)
        self.assertEqual(report.total, 0)
        self.assertIn("nessun campione", " ".join(report.notes))

    def test_reference_within_tolerance_passes(self) -> None:
        report = analyze_sonar(
            [reading(index, distance_mm=1000 + index, status=1) for index in range(2)]
        )

        reference = check_sonar_reference(report, 1000, tolerance_mm=10)

        self.assertTrue(reference.passed)
        self.assertAlmostEqual(reference.measured_mm, 1000.5)
        self.assertAlmostEqual(reference.error_mm, 0.5)

    def test_reference_outside_tolerance_fails(self) -> None:
        report = analyze_sonar([reading(0, distance_mm=900, status=1)])

        reference = check_sonar_reference(report, 1000, tolerance_mm=50)

        self.assertFalse(reference.passed)
        self.assertAlmostEqual(reference.error_mm, -100.0)
        self.assertIn("tolleranza", " ".join(reference.notes))

    def test_reference_uses_median_not_mean(self) -> None:
        readings = [
            reading(0, distance_mm=400, status=1),
            reading(1, distance_mm=400, status=1),
            reading(2, distance_mm=400, status=1),
            reading(3, distance_mm=1100, status=1),
        ]
        report = analyze_sonar(readings)

        reference = check_sonar_reference(report, 500, tolerance_mm=50)

        self.assertFalse(reference.passed)
        self.assertEqual(reference.measured_mm, 400.0)
        self.assertGreater(reference.mean_mm, 500.0)

    def test_reference_without_data_fails(self) -> None:
        reference = check_sonar_reference(analyze_sonar([]), 500)

        self.assertFalse(reference.passed)
        self.assertIsNone(reference.measured_mm)

    def test_sequence_gap_helper_wraps(self) -> None:
        readings = [
            reading(65535, status=1),
            reading(0, status=1),
            reading(2, status=1),
        ]

        self.assertEqual(sequence_gaps(readings), 1)


class ImuChecksTests(unittest.TestCase):
    def test_stationary_sequence_passes(self) -> None:
        readings = [
            reading(index, yaw_mdeg=1000, pitch_mdeg=500, roll_mdeg=-500, status=2)
            for index in range(10)
        ]

        report = analyze_imu(readings, mode="stationary", settle_samples=2)

        self.assertTrue(report.passed)
        self.assertTrue(report.stationary)
        self.assertFalse(report.motion_detected)
        self.assertEqual(report.yaw.mean, 1000.0)
        self.assertEqual(report.pitch.mean, 500.0)
        self.assertEqual(report.roll.mean, -500.0)
        self.assertEqual(report.yaw_drift_mdeg, 0)

    def test_motion_sequence_passes_in_motion_mode(self) -> None:
        readings = [
            reading(index, yaw_mdeg=index * 10000, status=2)
            for index in range(10)
        ]

        report = analyze_imu(readings, mode="motion", settle_samples=0)

        self.assertTrue(report.passed)
        self.assertTrue(report.motion_detected)
        self.assertFalse(report.stationary)
        self.assertEqual(report.dominant_axis, "yaw")

    def test_expected_yaw_passes_on_yaw_motion(self) -> None:
        readings = [
            reading(index, yaw_mdeg=index * 10000, status=2)
            for index in range(10)
        ]

        report = analyze_imu(
            readings,
            mode="motion",
            expected_axis="yaw",
            settle_samples=0,
        )

        self.assertTrue(report.passed)
        self.assertEqual(report.expected_axis, "yaw")

    def test_expected_pitch_fails_on_yaw_motion(self) -> None:
        readings = [
            reading(index, yaw_mdeg=index * 10000, status=2)
            for index in range(10)
        ]

        report = analyze_imu(
            readings,
            mode="motion",
            expected_axis="pitch",
            settle_samples=0,
        )

        self.assertFalse(report.passed)
        self.assertFalse(report.motion_detected)
        self.assertEqual(report.dominant_axis, "yaw")
        self.assertIn("asse pitch", " ".join(report.notes))

    def test_invalid_expected_axis_raises(self) -> None:
        with self.assertRaises(ValueError):
            analyze_imu([], mode="motion", expected_axis="boh")

    def test_motion_fails_in_stationary_mode(self) -> None:
        readings = [
            reading(index, yaw_mdeg=index * 10000, status=2)
            for index in range(10)
        ]

        report = analyze_imu(readings, mode="stationary", settle_samples=0)

        self.assertFalse(report.passed)
        self.assertFalse(report.stationary)

    def test_out_of_range_pitch_fails(self) -> None:
        report = analyze_imu(
            [reading(0, pitch_mdeg=100000, status=2)],
            settle_samples=0,
        )

        self.assertFalse(report.passed)
        self.assertEqual(report.out_of_range, 1)

    def test_low_valid_ratio_fails(self) -> None:
        readings = [
            reading(0, status=0),
            reading(1, status=0),
            reading(2, status=2),
        ]

        report = analyze_imu(readings, settle_samples=0)

        self.assertFalse(report.passed)
        self.assertLess(report.valid_ratio, 0.8)

    def test_sequence_gap_fails(self) -> None:
        readings = [
            reading(0, status=2),
            reading(2, status=2),
        ]

        report = analyze_imu(readings, settle_samples=0)

        self.assertEqual(report.sequence_gaps, 1)
        self.assertFalse(report.passed)

    def test_invalid_mode_raises(self) -> None:
        with self.assertRaises(ValueError):
            analyze_imu([], mode="boh")


if __name__ == "__main__":
    unittest.main()
