from __future__ import annotations

import contextlib
import io
import unittest

from pwm_sweep import _motor_values, _parse_pwms, main


class PwmSweepTests(unittest.TestCase):
    def test_parse_pwms(self) -> None:
        self.assertEqual(_parse_pwms("150, 160,255"), [150, 160, 255])

    def test_parse_pwms_accepts_reverse(self) -> None:
        self.assertEqual(_parse_pwms("255,-255"), [255, -255])

    def test_parse_rejects_out_of_range(self) -> None:
        for text in ("150,256", "150,-256"):
            with self.assertRaises(ValueError):
                _parse_pwms(text)

    def test_parse_rejects_zero(self) -> None:
        with self.assertRaises(ValueError):
            _parse_pwms("0")

    def test_motor_values_both(self) -> None:
        self.assertEqual(_motor_values(255, "both"), (255, 255))

    def test_motor_values_left(self) -> None:
        self.assertEqual(_motor_values(-200, "left"), (-200, 0))

    def test_motor_values_right(self) -> None:
        self.assertEqual(_motor_values(150, "right"), (0, 150))

    def test_motor_values_rejects_unknown_side(self) -> None:
        with self.assertRaises(ValueError):
            _motor_values(255, "front")

    def test_parse_rejects_empty(self) -> None:
        with self.assertRaises(ValueError):
            _parse_pwms(" , ")

    def test_requires_confirmation(self) -> None:
        buffer = io.StringIO()
        with contextlib.redirect_stderr(buffer):
            code = main(["--port", "/dev/null", "--pwms", "150"])

        self.assertEqual(code, 2)
        self.assertIn("confirm-wheels-raised", buffer.getvalue())


if __name__ == "__main__":
    unittest.main()
