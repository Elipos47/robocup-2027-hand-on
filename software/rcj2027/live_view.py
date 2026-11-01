"""Vista live della telecamera per le prove F0.

Fornisce uno stream MJPEG via HTTP, senza dipendenze aggiuntive oltre a OpenCV.
Lo stream mostra il frame annotato dal pipeline della linea. Non apre porte su
Internet: va usato solo sulla rete locale del robot.
"""

from __future__ import annotations

import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

try:
    import cv2

    HAS_CV2 = True
except ImportError:  # pragma: no cover - dipende dall'ambiente
    cv2 = None  # type: ignore[assignment]
    HAS_CV2 = False


class LiveViewError(RuntimeError):
    """Stream o frame non disponibili."""


_INDEX_HTML = """<!doctype html>
<html lang="it">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>RCJ2027 line-live</title>
<style>
  body { margin: 0; background: #111; color: #eee; font-family: sans-serif; }
  header { padding: 10px 14px; background: #1d1d1d; }
  main { display: flex; justify-content: center; align-items: center; min-height: 80vh; }
  img { max-width: 100vw; max-height: 85vh; display: block; }
</style>
</head>
<body>
<header><strong>RCJ2027 line-live</strong> - stream locale della telecamera linea</header>
<main><img src="/stream.mjpg" alt="stream telecamera"></main>
</body>
</html>
"""


class MjpegServer:
    """Server HTTP minimale che pubblica l'ultimo frame come MJPEG."""

    def __init__(
        self,
        host: str = "0.0.0.0",
        port: int = 8080,
        *,
        width: int = 960,
        quality: int = 70,
    ) -> None:
        if not HAS_CV2:
            raise LiveViewError("OpenCV non disponibile per lo stream")
        if not 0 <= port <= 65535:
            raise ValueError("porta non valida")
        if width < 160:
            raise ValueError("width dello stream troppo piccola")
        if not 30 <= quality <= 95:
            raise ValueError("qualita' JPEG tra 30 e 95")

        self.host = host
        self._width = int(width)
        self._quality = int(quality)
        self._condition = threading.Condition()
        self._frame: bytes | None = None
        self._sequence = 0
        self._stopped = threading.Event()
        self._server = ThreadingHTTPServer((host, port), self._make_handler())
        self._server.daemon_threads = True
        self._thread: threading.Thread | None = None
        self._started = False
        self._closed = False

    @property
    def port(self) -> int:
        return int(self._server.server_address[1])

    def _make_handler(self) -> type[BaseHTTPRequestHandler]:
        outer = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, format: str, *args: Any) -> None:
                return

            def do_GET(self) -> None:
                if self.path in ("/", "/index.html"):
                    body = _INDEX_HTML.encode("utf-8")
                    self.send_response(200)
                    self.send_header("Content-Type", "text/html; charset=utf-8")
                    self.send_header("Content-Length", str(len(body)))
                    self.send_header("Cache-Control", "no-store")
                    self.end_headers()
                    self.wfile.write(body)
                    return
                if self.path in ("/stream.mjpg", "/stream"):
                    outer._serve_stream(self)
                    return
                self.send_error(404)

        return Handler

    def _serve_stream(self, handler: BaseHTTPRequestHandler) -> None:
        handler.send_response(200)
        handler.send_header(
            "Content-Type", "multipart/x-mixed-replace; boundary=frame"
        )
        handler.send_header("Cache-Control", "no-store")
        handler.end_headers()
        last_sequence = -1
        while not self._stopped.is_set():
            with self._condition:
                while (
                    self._sequence == last_sequence
                    and not self._stopped.is_set()
                ):
                    self._condition.wait(timeout=0.5)
                if self._stopped.is_set():
                    break
                frame = self._frame
                last_sequence = self._sequence
            if frame is None:
                continue
            try:
                handler.wfile.write(b"--frame\r\n")
                handler.wfile.write(b"Content-Type: image/jpeg\r\n")
                handler.wfile.write(
                    f"Content-Length: {len(frame)}\r\n\r\n".encode("ascii")
                )
                handler.wfile.write(frame)
                handler.wfile.write(b"\r\n")
                handler.wfile.flush()
            except (BrokenPipeError, ConnectionResetError, OSError):
                break

    def start(self) -> None:
        if not self._started:
            self._thread = threading.Thread(
                target=self._server.serve_forever,
                kwargs={"poll_interval": 0.2},
                daemon=True,
            )
            self._thread.start()
            self._started = True

    def update(self, frame: Any) -> None:
        if not HAS_CV2:
            raise LiveViewError("OpenCV non disponibile per lo stream")
        if frame is None or not hasattr(frame, "shape"):
            raise LiveViewError("frame non valido per lo stream")
        height, width = frame.shape[:2]
        if width > self._width:
            scale = self._width / width
            frame = cv2.resize(
                frame,
                (self._width, max(1, int(round(height * scale)))),
                interpolation=cv2.INTER_AREA,
            )
        ok, encoded = cv2.imencode(
            ".jpg",
            frame,
            [int(cv2.IMWRITE_JPEG_QUALITY), self._quality],
        )
        if not ok:
            raise LiveViewError("codifica JPEG fallita")
        with self._condition:
            self._frame = encoded.tobytes()
            self._sequence += 1
            self._condition.notify_all()

    def stop(self) -> None:
        if self._closed:
            return
        self._closed = True
        self._stopped.set()
        with self._condition:
            self._condition.notify_all()
        if self._started:
            self._server.shutdown()
            self._started = False
        self._server.server_close()
        if self._thread is not None:
            self._thread.join(timeout=1.0)

    def __enter__(self) -> "MjpegServer":
        self.start()
        return self

    def __exit__(self, *args: object) -> None:
        self.stop()
