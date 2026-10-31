from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import numpy as np

from rcj2027.camera_checks import HAS_CV2, analyze_frame, frame_metrics

if HAS_CV2:
    import cv2
else:  # pragma: no cover - dipende dall'ambiente
    cv2 = None


def checkerboard(
    squares_x: int = 10,
    squares_y: int = 7,
    square_px: int = 40,
    margin: int = 40,
) -> np.ndarray:
    width = squares_x * square_px + 2 * margin
    height = squares_y * square_px + 2 * margin
    image = np.full((height, width, 3), 255, np.uint8)
    for row in range(squares_y):
        for column in range(squares_x):
            if (row + column) % 2 == 0:
                top_left = (margin + column * square_px, margin + row * square_px)
                bottom_right = (
                    margin + (column + 1) * square_px - 1,
                    margin + (row + 1) * square_px - 1,
                )
                cv2.rectangle(image, top_left, bottom_right, (0, 0, 0), -1)
    return image


@unittest.skipUnless(HAS_CV2, "OpenCV/numpy non disponibili")
class CameraChecksTests(unittest.TestCase):
    def test_good_frame_passes(self) -> None:
        rng = np.random.default_rng(1234)
        frame = rng.integers(0, 256, (240, 320, 3), dtype=np.uint8)

        metrics = frame_metrics(frame)

        self.assertTrue(metrics.passed)
        self.assertEqual(metrics.width, 320)
        self.assertEqual(metrics.height, 240)
        self.assertFalse(metrics.dark)
        self.assertFalse(metrics.overexposed)
        self.assertFalse(metrics.blurry)

    def test_dark_frame_fails(self) -> None:
        frame = np.zeros((120, 160, 3), np.uint8)

        metrics = frame_metrics(frame)

        self.assertFalse(metrics.passed)
        self.assertTrue(metrics.dark)
        self.assertTrue(metrics.blurry)

    def test_overexposed_frame_fails(self) -> None:
        frame = np.full((120, 160, 3), 255, np.uint8)

        metrics = frame_metrics(frame)

        self.assertFalse(metrics.passed)
        self.assertTrue(metrics.overexposed)

    def test_uniform_gray_frame_fails_for_contrast_and_sharpness(self) -> None:
        frame = np.full((120, 160, 3), 128, np.uint8)

        metrics = frame_metrics(frame)

        self.assertFalse(metrics.passed)
        self.assertTrue(metrics.blurry)
        self.assertLess(metrics.contrast, 10)

    def test_grayscale_frame_is_supported(self) -> None:
        rng = np.random.default_rng(99)
        frame = rng.integers(0, 256, (64, 256), dtype=np.uint8)

        metrics = frame_metrics(frame)

        self.assertEqual(metrics.width, 256)
        self.assertEqual(metrics.height, 64)
        self.assertTrue(metrics.passed)

    def test_checkerboard_is_detected(self) -> None:
        frame = checkerboard()

        probe = analyze_frame(frame, checkerboard_size=(9, 6))

        self.assertEqual(probe.checkerboard_corners, 54)
        self.assertTrue(probe.passed)

    def test_missing_checkerboard_fails_when_expected(self) -> None:
        rng = np.random.default_rng(7)
        frame = rng.integers(0, 256, (240, 320, 3), dtype=np.uint8)

        probe = analyze_frame(frame, checkerboard_size=(9, 6))

        self.assertEqual(probe.checkerboard_corners, 0)
        self.assertFalse(probe.passed)

    def test_analyze_frame_saves_snapshot(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "frame.jpg"
            probe = analyze_frame(
                np.full((60, 80, 3), 128, np.uint8),
                save_path=path,
            )

            self.assertEqual(probe.saved_path, str(path))
            self.assertTrue(path.exists())

    def test_frame_metrics_shape(self) -> None:
        metrics = frame_metrics(np.zeros((10, 20, 3), np.uint8))

        self.assertEqual((metrics.width, metrics.height), (20, 10))


if __name__ == "__main__":
    unittest.main()
