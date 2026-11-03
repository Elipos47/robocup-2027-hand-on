from __future__ import annotations

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from rcj2027.diagnostics import main
from rcj2027.line_control import (
    DriveCommand,
    LineControlConfig,
    LineControlError,
    LineController,
)
from rcj2027.line_vision import LineObservation, TrackState


def track(
    *,
    found: bool = True,
    confirmed: bool = True,
    offset: float = 0.0,
    heading: float = 0.0,
) -> TrackState:
    return TrackState(
        found=found,
        confirmed=confirmed,
        offset_px=offset,
        heading_deg=heading,
        confidence=1.0,
        lost_frames=0,
        found_streak=3,
        recoveries=0,
        width_px=30.0,
        expected_width_px=30.0,
        width_ok=True,
    )


def observation(
    *,
    found: bool,
    offset: float = 0.0,
    width: float = 30.0,
) -> LineObservation:
    return LineObservation(
        found=found,
        offset_px=offset,
        offset_ratio=offset / 640.0,
        heading_deg=0.0,
        confidence=1.0 if found else 0.0,
        valid_rows=60 if found else 0,
        scan_rows=60,
        line_width_px=width if found else 0.0,
        residual_px=0.0 if found else 0.0,
        line_x_bottom_px=320.0 + offset,
        optical_x_px=320.0,
        roi=(0, 198, 640, 353),
        processing_ms=1.0,
        undistorted=False,
    )


class LineControllerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.controller = LineController(
            LineControlConfig(
                pwm_max=255,
                cruise=200,
                k_offset=0.5,
                k_heading=2.0,
                max_correction=80,
                offset_deadband_px=2.0,
                heading_deadband_deg=0.5,
            )
        )

    def test_stops_when_not_found(self) -> None:
        command = self.controller.update(track(found=False, confirmed=False))

        self.assertEqual(command.left, 0)
        self.assertEqual(command.right, 0)
        self.assertEqual(command.state, "STOP")
        self.assertEqual(command.reason, "not_found")

    def test_stops_when_not_confirmed(self) -> None:
        command = self.controller.update(track(found=True, confirmed=False))

        self.assertEqual(command.left, 0)
        self.assertEqual(command.right, 0)
        self.assertEqual(command.reason, "not_confirmed")

    def test_centered_line_goes_straight(self) -> None:
        command = self.controller.update(track(offset=0.0, heading=0.0))

        self.assertEqual(command.state, "FOLLOW")
        self.assertEqual(command.left, 200)
        self.assertEqual(command.right, 200)
        self.assertAlmostEqual(command.correction, 0.0)

    def test_positive_offset_turns_right(self) -> None:
        command = self.controller.update(track(offset=20.0, heading=0.0))

        self.assertGreater(command.left, command.right)
        self.assertGreater(command.correction, 0.0)

    def test_negative_offset_turns_left(self) -> None:
        command = self.controller.update(track(offset=-20.0, heading=0.0))

        self.assertLess(command.left, command.right)
        self.assertLess(command.correction, 0.0)

    def test_positive_heading_turns_right(self) -> None:
        command = self.controller.update(track(offset=0.0, heading=5.0))

        self.assertGreater(command.left, command.right)

    def test_deadband_keeps_straight(self) -> None:
        command = self.controller.update(track(offset=1.0, heading=0.2))

        self.assertEqual(command.left, 200)
        self.assertEqual(command.right, 200)

    def test_correction_and_pwm_are_clamped(self) -> None:
        command = self.controller.update(track(offset=1000.0, heading=90.0))

        self.assertLessEqual(command.left, 255)
        self.assertGreaterEqual(command.right, 0)
        self.assertAlmostEqual(command.correction, 80.0)
        self.assertEqual(command.left, 255)
        self.assertEqual(command.right, 120)

    def test_command_is_serializable(self) -> None:
        command: DriveCommand = self.controller.update(track(offset=10.0))

        payload = command.to_dict()

        self.assertEqual(payload["state"], "FOLLOW")
        self.assertIn("left", payload)
        self.assertIn("right", payload)

    def test_config_rejects_bad_values(self) -> None:
        for kwargs in (
            {"pwm_max": 0},
            {"cruise": 300},
            {"k_offset": -1},
            {"k_heading": -1},
            {"max_correction": 300},
            {"offset_deadband_px": -1},
            {"heading_deadband_deg": -1},
        ):
            with self.assertRaises(LineControlError):
                LineControlConfig(**kwargs)

    def test_cli_dry_run_reads_log(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            log = root / "run.jsonl"
            with log.open("w", encoding="utf-8") as handle:
                for index in range(6):
                    obs = observation(
                        found=True,
                        offset=0.0 if index < 3 else 10.0,
                    )
                    record = {
                        "event": "line",
                        "frame": index,
                        **obs.to_dict(),
                    }
                    handle.write(json.dumps(record) + "\n")
                lost = observation(found=False)
                handle.write(
                    json.dumps(
                        {"event": "line", "frame": 6, **lost.to_dict()}
                    )
                    + "\n"
                )
            report_path = root / "report.json"
            commands_path = root / "commands.jsonl"
            buffer = io.StringIO()

            with contextlib.redirect_stdout(buffer):
                code = main(
                    [
                        "line-control",
                        "--log",
                        str(log),
                        "--json-out",
                        str(report_path),
                        "--commands-out",
                        str(commands_path),
                    ]
                )

            report = json.loads(report_path.read_text(encoding="utf-8"))
            commands = [
                json.loads(line)
                for line in commands_path.read_text(encoding="utf-8").splitlines()
            ]

        self.assertEqual(code, 0)
        self.assertFalse(report["motor_output"])
        self.assertEqual(report["summary"]["frames"], 7)
        self.assertEqual(report["summary"]["follow"], 4)
        self.assertEqual(report["summary"]["stop_not_confirmed"], 2)
        self.assertEqual(report["summary"]["stop_not_found"], 1)
        self.assertEqual(len(commands), 7)


if __name__ == "__main__":
    unittest.main()
