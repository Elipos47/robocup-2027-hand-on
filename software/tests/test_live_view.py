from __future__ import annotations

import unittest
import urllib.request

import numpy as np

from rcj2027.live_view import HAS_CV2, LiveViewError, MjpegServer


@unittest.skipUnless(HAS_CV2, "OpenCV/numpy non disponibili")
class MjpegServerTests(unittest.TestCase):
    def test_index_and_frame_update(self) -> None:
        server = MjpegServer(host="127.0.0.1", port=0, width=320, quality=60)
        server.start()
        try:
            server.update(np.zeros((120, 160, 3), np.uint8))
            with urllib.request.urlopen(
                f"http://127.0.0.1:{server.port}/", timeout=2
            ) as response:
                body = response.read()
                content_type = response.headers.get("Content-Type", "")
        finally:
            server.stop()

        self.assertIn(b"line-live", body)
        self.assertIn("text/html", content_type)

    def test_invalid_frame_raises(self) -> None:
        server = MjpegServer(host="127.0.0.1", port=0)
        server.start()
        try:
            with self.assertRaises(LiveViewError):
                server.update(None)
        finally:
            server.stop()

    def test_stop_endpoint(self) -> None:
        server = MjpegServer(host="127.0.0.1", port=0)
        server.start()
        try:
            self.assertFalse(server.stop_requested)
            with urllib.request.urlopen(
                f"http://127.0.0.1:{server.port}/stop", timeout=2
            ) as response:
                body = response.read()
            self.assertIn(b"stop", body)
            self.assertTrue(server.stop_requested)
        finally:
            server.stop()

    def test_invalid_quality_raises(self) -> None:
        with self.assertRaises(ValueError):
            MjpegServer(host="127.0.0.1", port=0, quality=10)

    def test_invalid_width_raises(self) -> None:
        with self.assertRaises(ValueError):
            MjpegServer(host="127.0.0.1", port=0, width=80)


if __name__ == "__main__":
    unittest.main()
