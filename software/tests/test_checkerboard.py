from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from rcj2027.checkerboard import (
    HAS_REPORTLAB,
    CheckerboardError,
    make_checkerboard_pdf,
)


@unittest.skipUnless(HAS_REPORTLAB, "reportlab non disponibile")
class CheckerboardTests(unittest.TestCase):
    def test_generates_pdf(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "target.pdf"

            output = make_checkerboard_pdf(
                path,
                pattern_size=(9, 6),
                square_size_mm=25.0,
            )

            self.assertEqual(output, path)
            self.assertTrue(path.exists())
            self.assertGreater(path.stat().st_size, 1000)
            self.assertEqual(path.read_bytes()[:4], b"%PDF")

    def test_invalid_pattern_raises(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                make_checkerboard_pdf(
                    Path(tmp) / "target.pdf",
                    pattern_size=(1, 6),
                )

    def test_board_too_large_raises(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(CheckerboardError):
                make_checkerboard_pdf(
                    Path(tmp) / "target.pdf",
                    pattern_size=(9, 6),
                    square_size_mm=30.0,
                )

    def test_portrait_with_smaller_square(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "target.pdf"

            make_checkerboard_pdf(
                path,
                pattern_size=(9, 6),
                square_size_mm=18.0,
                landscape_page=False,
            )

            self.assertTrue(path.exists())


if __name__ == "__main__":
    unittest.main()
