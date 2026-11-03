from __future__ import annotations

import contextlib
import io
import unittest

from pwm_sweep import _parse_pwms, main


class PwmSweepTests(unittest.TestCase):
    def test_parse_pwms(self) -> None:
        self.assertEqual(_parse_pwms("150, 160,255"), [150, 160, 255])

    def test_parse_rejects_out_of_range(self) -> None:
        with self.assertRaises(ValueError):
            _parse_pwms("150,256")

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
