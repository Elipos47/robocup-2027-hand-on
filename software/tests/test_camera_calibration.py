from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import numpy as np

from rcj2027.camera_calibration import (
    HAS_CV2,
    CalibrationError,
    calibrate_camera,
    save_calibration,
)

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


def synthetic_views() -> list[np.ndarray]:
    base = checkerboard()
    height, width = base.shape[:2]
    source = np.float32(
        [[0, 0], [width - 1, 0], [width - 1, height - 1], [0, height - 1]]
    )
    views: list[np.ndarray] = []
    transforms = (
        (0, 0, 0.0),
        (20, 10, 0.02),
        (-15, 20, -0.02),
        (10, -15, 0.03),
        (25, 5, -0.03),
    )
    for dx, dy, skew in transforms:
        destination = np.float32(
            [
                [dx, dy],
                [width - 1 + dx + skew * width, dy],
                [width - 1 + dx, height - 1 + dy],
                [dx - skew * width, height - 1 + dy],
            ]
        )
        matrix = cv2.getPerspectiveTransform(source, destination)
        views.append(
            cv2.warpPerspective(
                base,
                matrix,
                (width + 100, height + 100),
                borderValue=(255, 255, 255),
            )
        )
    return views


@unittest.skipUnless(HAS_CV2, "OpenCV/numpy non disponibili")
class CameraCalibrationTests(unittest.TestCase):
    def test_calibration_from_synthetic_views(self) -> None:
        calibration = calibrate_camera(
            synthetic_views(),
            pattern_size=(9, 6),
            square_size_mm=25.0,
            min_images=3,
        )

        self.assertEqual(calibration.image_count, 5)
        self.assertEqual(calibration.pattern_size, (9, 6))
        self.assertEqual(calibration.square_size_mm, 25.0)
        self.assertGreater(calibration.rms, 0)
        self.assertGreater(calibration.coverage_min, 0.2)
        self.assertGreater(calibration.coverage_mean, 0.2)
        self.assertGreater(calibration.pose_spread_px, 40)
        self.assertGreater(calibration.size_ratio, 1.05)
        self.assertEqual(len(calibration.camera_matrix), 3)
        self.assertEqual(len(calibration.camera_matrix[0]), 3)
        self.assertTrue(calibration.distortion)

    def test_identical_views_rejected(self) -> None:
        frame = synthetic_views()[0]

        with self.assertRaises(CalibrationError):
            calibrate_camera([frame, frame, frame], min_images=3)

    def test_small_board_rejected(self) -> None:
        small = checkerboard(square_px=10, margin=10)
        frame = np.full((480, 640, 3), 255, np.uint8)
        height, width = small.shape[:2]
        frame[190 : 190 + height, 260 : 260 + width] = small

        with self.assertRaises(CalibrationError):
            calibrate_camera([frame, frame, frame], min_images=3)

    def test_too_few_images_raises(self) -> None:
        with self.assertRaises(CalibrationError):
            calibrate_camera(
                synthetic_views()[:1],
                pattern_size=(9, 6),
                min_images=3,
            )

    def test_invalid_square_size_raises(self) -> None:
        with self.assertRaises(ValueError):
            calibrate_camera([], square_size_mm=0)

    def test_committed_usb_calibration_is_consistent(self) -> None:
        path = (
            Path(__file__).resolve().parent.parent
            / "rcj2027"
            / "calibrations"
            / "usb_640x480.json"
        )
        data = json.loads(path.read_text(encoding="utf-8"))

        self.assertEqual(data["image_count"], 15)
        self.assertEqual(data["image_size"], [640, 480])
        self.assertEqual(data["square_size_mm"], 23.75)
        self.assertLess(data["rms"], 1.0)
        self.assertGreaterEqual(data["coverage_mean"], 0.2)
        self.assertEqual(len(data["camera_matrix"]), 3)

    def test_save_calibration(self) -> None:
        calibration = calibrate_camera(synthetic_views(), min_images=3)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "calibration.json"
            output = save_calibration(calibration, path)

            self.assertEqual(output, path)
            data = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(data["image_count"], 5)
            self.assertEqual(len(data["camera_matrix"]), 3)


if __name__ == "__main__":
    unittest.main()
