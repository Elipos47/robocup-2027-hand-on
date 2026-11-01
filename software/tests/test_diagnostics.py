from __future__ import annotations

import unittest

from rcj2027.diagnostics import _parse_pattern, build_parser, collect_readings
from rcj2027.protocol import SensorReading


class FakeClock:
    def __init__(self) -> None:
        self.value = 0.0

    def __call__(self) -> float:
        return self.value

    def advance(self, seconds: float) -> None:
        self.value += seconds


class FakeSession:
    def __init__(self, readings: list[SensorReading], clock: FakeClock) -> None:
        self._readings = iter(readings)
        self.clock = clock
        self.last_status: SensorReading | None = None

    def step(self, *, read_timeout_s: float = 0.05) -> bool:
        del read_timeout_s
        self.clock.advance(0.01)
        try:
            self.last_status = next(self._readings)
        except StopIteration:
            pass
        return self.last_status is not None


def reading(sequence: int) -> SensorReading:
    return SensorReading(
        sequence=sequence,
        distance_mm=1000,
        yaw_mdeg=0,
        pitch_mdeg=0,
        roll_mdeg=0,
        status=1,
    )


class DiagnosticsTests(unittest.TestCase):
    def test_parse_pattern(self) -> None:
        self.assertEqual(_parse_pattern("9x6"), (9, 6))
        self.assertEqual(_parse_pattern(" 7X5 "), (7, 5))

    def test_parse_pattern_rejects_invalid_values(self) -> None:
        for text in ("9", "9x", "1x6", "a x b"):
            with self.assertRaises(ValueError):
                _parse_pattern(text)

    def test_collect_readings_deduplicates_sequence(self) -> None:
        clock = FakeClock()
        session = FakeSession([reading(0), reading(0), reading(1)], clock)

        readings = collect_readings(session, 0.03, clock=clock)

        self.assertEqual([item.sequence for item in readings], [0, 1])

    def test_collect_readings_requires_positive_duration(self) -> None:
        clock = FakeClock()
        session = FakeSession([], clock)

        with self.assertRaises(ValueError):
            collect_readings(session, 0, clock=clock)

    def test_parser_builds_camera_calibration_command(self) -> None:
        parser = build_parser()

        args = parser.parse_args(
            [
                "camera-calibrate",
                "--images",
                "calib/*.jpg",
                "--pattern",
                "9x6",
            ]
        )

        self.assertEqual(args.command, "camera-calibrate")
        self.assertEqual(args.pattern, "9x6")

    def test_parser_builds_csi_camera_command(self) -> None:
        parser = build_parser()

        args = parser.parse_args(
            ["camera", "--csi", "--camera-num", "0", "--warmup", "2"]
        )

        self.assertTrue(args.csi)
        self.assertEqual(args.camera_num, 0)
        self.assertEqual(args.warmup, 2.0)

    def test_parser_builds_checkerboard_command(self) -> None:
        parser = build_parser()

        args = parser.parse_args(
            ["checkerboard", "--pattern", "9x6", "--square-mm", "25"]
        )

        self.assertEqual(args.command, "checkerboard")
        self.assertEqual(args.pattern, "9x6")
        self.assertEqual(args.square_mm, 25.0)

    def test_parser_builds_camera_capture_command(self) -> None:
        parser = build_parser()

        args = parser.parse_args(
            ["camera-capture", "--csi", "--count", "12", "--interval", "2"]
        )

        self.assertTrue(args.csi)
        self.assertEqual(args.count, 12)
        self.assertEqual(args.interval, 2.0)

    def test_camera_commands_default_to_auto_device(self) -> None:
        parser = build_parser()

        self.assertEqual(parser.parse_args(["camera"]).device, "auto")
        self.assertEqual(parser.parse_args(["camera-capture"]).device, "auto")


if __name__ == "__main__":
    unittest.main()
