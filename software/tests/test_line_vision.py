from __future__ import annotations

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

import numpy as np

from rcj2027 import line_vision
from rcj2027.diagnostics import build_parser, main

if line_vision.HAS_CV2:
    import cv2
else:  # pragma: no cover - dipende dall'ambiente
    cv2 = None


def line_frame(
    width: int = 640,
    height: int = 360,
    bottom_x: int = 320,
    slope: float = 0.0,
    thickness: int = 28,
    background: int = 200,
    line: int = 30,
) -> np.ndarray:
    image = np.full((height, width), background, np.uint8)
    points = [
        (int(round(bottom_x + slope * (height - 1 - y))), y)
        for y in range(height - 1, -1, -1)
    ]
    cv2.polylines(
        image,
        [np.asarray(points, dtype=np.int32)],
        False,
        line,
        thickness,
    )
    return image


def curved_frame(width: int = 640, height: int = 360) -> np.ndarray:
    image = np.full((height, width), 200, np.uint8)
    points = np.asarray(
        [
            (320 + 120 * ((height - y) / height) ** 2, y)
            for y in range(height - 1, -1, -1)
        ],
        dtype=np.int32,
    )
    cv2.polylines(image, [points], False, 30, 28)
    return image


def tabletop_frame(width: int = 1280, height: int = 720) -> np.ndarray:
    """Linea che termina sul bordo del tavolo, con pavimento scuro sotto."""
    image = np.full((height, width), 200, np.uint8)
    cv2.line(image, (620, 0), (620, 584), 30, 140)
    cv2.rectangle(image, (0, 590), (width - 1, 610), 60, -1)
    image[610:, :] = 100
    rng = np.random.default_rng(12)
    for x in range(0, width, 23):
        top = 610 + int(rng.integers(0, 40))
        cv2.line(image, (x, top), (x + 8, height - 1), 55, 3)
    return image


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
    for dx, dy, skew in ((0, 0, 0.0), (20, 10, 0.02), (-15, 20, -0.02)):
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


def identity_model(width: int = 640, height: int = 360) -> line_vision.CameraModel:
    return line_vision.CameraModel(
        image_size=(width, height),
        camera_matrix=[
            [500.0, 0.0, width / 2.0],
            [0.0, 500.0, height / 2.0],
            [0.0, 0.0, 1.0],
        ],
        distortion=[0.0, 0.0, 0.0, 0.0],
    )


def observation(found: bool, offset: float = 0.0) -> line_vision.LineObservation:
    return line_vision.LineObservation(
        found=found,
        offset_px=offset,
        offset_ratio=offset / 640.0,
        heading_deg=0.0,
        confidence=1.0 if found else 0.0,
        valid_rows=60 if found else 0,
        scan_rows=60,
        line_width_px=30.0 if found else 0.0,
        residual_px=0.0 if found else 0.0,
        line_x_bottom_px=320.0 + offset,
        optical_x_px=320.0,
        roi=(0, 198, 640, 353),
        processing_ms=1.0,
        undistorted=False,
    )


@unittest.skipUnless(line_vision.HAS_CV2, "OpenCV/numpy non disponibili")
class CameraModelTests(unittest.TestCase):
    def test_load_calibration(self) -> None:
        payload = {
            "image_size": [640, 360],
            "camera_matrix": [
                [500.0, 0.0, 320.0],
                [0.0, 500.0, 180.0],
                [0.0, 0.0, 1.0],
            ],
            "distortion": [0.0, 0.0, 0.0, 0.0],
            "rms": 0.4,
        }
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "calibration.json"
            path.write_text(json.dumps(payload), encoding="utf-8")

            model = line_vision.load_camera_model(path)

        self.assertEqual(model.image_size, (640, 360))
        self.assertAlmostEqual(model.cx, 320.0)
        self.assertAlmostEqual(model.cy, 180.0)
        self.assertEqual(model.rms, 0.4)

    def test_load_calibration_rejects_missing_fields(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "calibration.json"
            path.write_text(json.dumps({"image_size": [640, 360]}), encoding="utf-8")

            with self.assertRaises(line_vision.LineVisionError):
                line_vision.load_camera_model(path)

    def test_camera_model_rejects_bad_matrix(self) -> None:
        with self.assertRaises(line_vision.LineVisionError):
            line_vision.CameraModel(
                image_size=(640, 360),
                camera_matrix=[[1.0, 0.0], [0.0, 1.0]],
                distortion=[0.0, 0.0, 0.0, 0.0],
            )

    def test_config_rejects_inverted_roi(self) -> None:
        with self.assertRaises(line_vision.LineVisionError):
            line_vision.LineConfig(roi_top=0.9, roi_bottom=0.5)

    def test_config_rejects_even_block(self) -> None:
        with self.assertRaises(line_vision.LineVisionError):
            line_vision.LineConfig(threshold_block=40)


@unittest.skipUnless(line_vision.HAS_CV2, "OpenCV/numpy non disponibili")
class LineDetectionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.config = line_vision.LineConfig(threshold_block=77)
        self.detector = line_vision.LineDetector(config=self.config)

    def test_centered_line(self) -> None:
        observation = self.detector.detect(line_frame())

        self.assertTrue(observation.found)
        self.assertLess(abs(observation.offset_px), 2.0)
        self.assertLess(abs(observation.heading_deg), 2.0)
        self.assertGreater(observation.confidence, 0.8)

    def test_auto_block_at_1280(self) -> None:
        detector = line_vision.LineDetector()
        frame = line_frame(width=1280, height=720, bottom_x=640, thickness=44)

        observation = detector.detect(frame)

        self.assertTrue(observation.found)
        self.assertLess(abs(observation.offset_px), 3.0)
        self.assertGreater(observation.confidence, 0.8)

    def test_wide_line_near_camera(self) -> None:
        detector = line_vision.LineDetector()
        frame = line_frame(width=1280, height=720, bottom_x=640, thickness=180)

        observation = detector.detect(frame)

        self.assertTrue(observation.found)
        self.assertLess(abs(observation.offset_px), 3.0)
        self.assertGreater(observation.line_width_px, 150.0)

    def test_line_ending_at_table_edge(self) -> None:
        detector = line_vision.LineDetector()

        observation = detector.detect(tabletop_frame())

        self.assertTrue(observation.found)
        self.assertGreater(observation.confidence, 0.8)
        self.assertLess(observation.residual_px, 1.0)
        self.assertAlmostEqual(observation.offset_px, -19.5, delta=5.0)
        self.assertLess(observation.valid_rows, observation.scan_rows)

    def test_line_on_the_right_has_positive_offset(self) -> None:
        observation = self.detector.detect(line_frame(bottom_x=380))

        self.assertTrue(observation.found)
        self.assertGreater(observation.offset_px, 40.0)

    def test_line_on_the_left_has_negative_offset(self) -> None:
        observation = self.detector.detect(line_frame(bottom_x=260))

        self.assertTrue(observation.found)
        self.assertLess(observation.offset_px, -40.0)

    def test_slant_sign(self) -> None:
        right = self.detector.detect(line_frame(slope=0.5))
        left = self.detector.detect(line_frame(slope=-0.5))

        self.assertGreater(right.heading_deg, 15.0)
        self.assertLess(left.heading_deg, -15.0)

    def test_curved_line_is_detected(self) -> None:
        observation = self.detector.detect(curved_frame())

        self.assertTrue(observation.found)
        self.assertGreater(observation.valid_rows, 40)
        self.assertLess(observation.residual_px, 2.0)

    def test_uniform_background_is_lost(self) -> None:
        observation = self.detector.detect(np.full((360, 640), 200, np.uint8))

        self.assertFalse(observation.found)
        self.assertEqual(observation.reason, "few_rows")

    def test_dark_floor_is_lost(self) -> None:
        observation = self.detector.detect(np.full((360, 640), 60, np.uint8))

        self.assertFalse(observation.found)

    def test_noise_does_not_break_line(self) -> None:
        frame = line_frame()
        rng = np.random.default_rng(4)
        noisy = np.clip(
            frame.astype(np.int16)
            + rng.integers(-10, 11, frame.shape, dtype=np.int16),
            0,
            255,
        ).astype(np.uint8)

        observation = self.detector.detect(noisy)

        self.assertTrue(observation.found)

    def test_undistort_keeps_size(self) -> None:
        detector = line_vision.LineDetector(identity_model())
        frame = line_frame()

        corrected = detector.undistort(frame)

        self.assertEqual(corrected.shape, frame.shape)
        self.assertTrue(detector.detect(frame).found)

    def test_wrong_resolution_is_rejected(self) -> None:
        detector = line_vision.LineDetector(identity_model(1280, 720))

        with self.assertRaises(line_vision.LineVisionError):
            detector.detect(line_frame())

    def test_debug_annotation(self) -> None:
        observation, debug = self.detector.detect(line_frame(), debug=True)

        annotated = line_vision.annotate_frame(debug, observation)

        self.assertTrue(observation.found)
        self.assertEqual(debug.mask.ndim, 2)
        self.assertGreater(len(debug.points), 0)
        self.assertEqual(annotated.shape, (360, 640, 3))

    def test_lost_frame_annotation(self) -> None:
        observation, debug = self.detector.detect(
            np.full((360, 640), 200, np.uint8), debug=True
        )

        annotated = line_vision.annotate_frame(debug, observation)

        self.assertFalse(observation.found)
        self.assertEqual(annotated.shape, (360, 640, 3))

    def test_read_write_image(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = line_vision.write_image(
                Path(tmp) / "frame.jpg", line_frame()
            )
            loaded = line_vision.read_image(path)

        self.assertEqual(loaded.shape[:2], (360, 640))

    def test_read_missing_image_raises(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(line_vision.LineVisionError):
                line_vision.read_image(Path(tmp) / "immagine-che-non-esiste.jpg")


@unittest.skipUnless(line_vision.HAS_CV2, "OpenCV/numpy non disponibili")
class LineTrackerTests(unittest.TestCase):
    def test_confirmation_after_three_found_frames(self) -> None:
        tracker = line_vision.LineTracker(confirm_frames=3, max_lost_frames=5)

        first = tracker.update(observation(True, 10.0))
        second = tracker.update(observation(True, 12.0))
        third = tracker.update(observation(True, 14.0))

        self.assertFalse(first.confirmed)
        self.assertFalse(second.confirmed)
        self.assertTrue(third.confirmed)
        self.assertEqual(third.found_streak, 3)

    def test_confirmation_survives_short_loss(self) -> None:
        tracker = line_vision.LineTracker(confirm_frames=3, max_lost_frames=5)
        for _ in range(3):
            tracker.update(observation(True, 0.0))

        state = tracker.update(observation(False))

        self.assertTrue(state.confirmed)
        self.assertEqual(state.lost_frames, 1)

    def test_confirmation_is_lost_after_timeout(self) -> None:
        tracker = line_vision.LineTracker(confirm_frames=3, max_lost_frames=5)
        for _ in range(3):
            tracker.update(observation(True, 0.0))
        for _ in range(6):
            state = tracker.update(observation(False))

        self.assertFalse(state.confirmed)

    def test_recovery_after_loss(self) -> None:
        tracker = line_vision.LineTracker(confirm_frames=3, max_lost_frames=2)
        for _ in range(3):
            tracker.update(observation(True, 0.0))
        for _ in range(3):
            tracker.update(observation(False))
        for _ in range(3):
            state = tracker.update(observation(True, 5.0))

        self.assertTrue(state.confirmed)
        self.assertEqual(tracker.recoveries, 1)


@unittest.skipUnless(line_vision.HAS_CV2, "OpenCV/numpy non disponibili")
class UndistortValidationTests(unittest.TestCase):
    def test_identity_model_does_not_worsen_homography(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = []
            for index, view in enumerate(synthetic_views()):
                path = Path(tmp) / f"view-{index}.jpg"
                cv2.imwrite(str(path), view)
                paths.append(path)
            model = identity_model(view.shape[1], view.shape[0])

            report = line_vision.validate_undistortion(paths, model)

        self.assertEqual(report.accepted, 3)
        self.assertTrue(report.passed)
        self.assertLess(report.undistorted_mean_px, 1.0)

    def test_too_few_images_raise(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "one.jpg"
            cv2.imwrite(str(path), synthetic_views()[0])
            model = identity_model(740, 460)

            with self.assertRaises(line_vision.LineVisionError):
                line_vision.validate_undistortion([path], model, min_images=2)


@unittest.skipUnless(line_vision.HAS_CV2, "OpenCV/numpy non disponibili")
class LineCliTests(unittest.TestCase):
    def test_parser_builds_line_command(self) -> None:
        parser = build_parser()

        args = parser.parse_args(
            ["line", "--images", "calib/linea/*.jpg", "--no-undistort"]
        )

        self.assertEqual(args.command, "line")
        self.assertTrue(args.no_undistort)
        self.assertEqual(args.min_found_ratio, 0.8)
        self.assertEqual(args.dark_threshold, 140.0)
        self.assertEqual(args.max_gap_ratio, 0.06)

    def test_parser_builds_line_undistort_command(self) -> None:
        parser = build_parser()

        args = parser.parse_args(
            ["line-undistort", "--images", "calib/csi/*.jpg", "--pattern", "9x6"]
        )

        self.assertEqual(args.command, "line-undistort")
        self.assertEqual(args.pattern, "9x6")

    def test_line_command_writes_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for index, bottom_x in enumerate((320, 330, 340)):
                cv2.imwrite(
                    str(root / f"frame-{index}.jpg"),
                    line_frame(bottom_x=bottom_x),
                )
            output = root / "report.json"
            buffer = io.StringIO()

            with contextlib.redirect_stdout(buffer):
                code = main(
                    [
                        "line",
                        "--images",
                        str(root / "*.jpg"),
                        "--no-undistort",
                        "--min-found-ratio",
                        "0.5",
                        "--json-out",
                        str(output),
                    ]
                )

            report = json.loads(output.read_text(encoding="utf-8"))

        self.assertEqual(code, 0)
        self.assertEqual(report["images"], 3)
        self.assertEqual(report["summary"]["found"], 3)
        self.assertTrue(report["passed"])


if __name__ == "__main__":
    unittest.main()
