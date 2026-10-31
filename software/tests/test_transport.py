from __future__ import annotations

import sys
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from rcj2027.transport import FakeTransport, SerialTransport, Transport


class FakeSerial:
    def __init__(self, chunks: list[bytes]) -> None:
        self.chunks = list(chunks)
        self.timeout: float | None = 0.1
        self.closed = False
        self.written: list[bytes] = []

    @property
    def in_waiting(self) -> int:
        return len(self.chunks[0]) if self.chunks else 0

    def read(self, size: int) -> bytes:
        if not self.chunks:
            return b""
        chunk = self.chunks[0]
        if len(chunk) <= size:
            self.chunks.pop(0)
            return chunk
        self.chunks[0] = chunk[size:]
        return chunk[:size]

    def write(self, data: bytes) -> None:
        self.written.append(data)

    def flush(self) -> None:
        pass

    def close(self) -> None:
        self.closed = True


class FakeTransportTests(unittest.TestCase):
    def test_write_and_read(self) -> None:
        transport = FakeTransport()
        transport.write(b"V,1*4B\n")
        transport.feed_line("K,17*61")

        self.assertEqual(transport.read_line(), b"K,17*61\n")
        self.assertEqual(transport.sent_text(), ["V,1*4B\n"])
        self.assertIsInstance(transport, Transport)

    def test_read_empty(self) -> None:
        transport = FakeTransport()
        self.assertIsNone(transport.read_line())

    def test_write_requires_bytes(self) -> None:
        transport = FakeTransport()
        with self.assertRaises(TypeError):
            transport.write("V,1*4B\n")  # type: ignore[arg-type]

    def test_closed_transport(self) -> None:
        transport = FakeTransport()
        transport.close()
        with self.assertRaises(RuntimeError):
            transport.write(b"V,1*4B\n")
        with self.assertRaises(RuntimeError):
            transport.read_line()


class SerialTransportTests(unittest.TestCase):
    def _transport(self, serial_port: FakeSerial) -> SerialTransport:
        fake_module = SimpleNamespace(Serial=lambda **kwargs: serial_port)
        with patch.dict(sys.modules, {"serial": fake_module}):
            return SerialTransport("fake", baudrate=115200, timeout=0.1)

    def test_partial_lines_are_buffered_between_reads(self) -> None:
        serial_port = FakeSerial([b"FIRS", b"T\nSECOND\n"])
        transport = self._transport(serial_port)

        self.assertEqual(transport.read_line(timeout=0.05), b"FIRST\n")
        self.assertEqual(transport.read_line(timeout=0.05), b"SECOND\n")
        self.assertEqual(serial_port.timeout, 0.1)

    def test_partial_line_survives_a_timeout(self) -> None:
        serial_port = FakeSerial([b"PART"])
        transport = self._transport(serial_port)

        self.assertIsNone(transport.read_line(timeout=0.01))

        serial_port.chunks.append(b"IAL\n")
        self.assertEqual(transport.read_line(timeout=0.05), b"PARTIAL\n")

    def test_write_flushes(self) -> None:
        serial_port = FakeSerial([])
        transport = self._transport(serial_port)

        transport.write(b"V,1*4B\n")

        self.assertEqual(serial_port.written, [b"V,1*4B\n"])
        transport.close()
        self.assertTrue(serial_port.closed)


if __name__ == "__main__":
    unittest.main()
