from __future__ import annotations

import unittest

from rcj2027.transport import FakeTransport, Transport


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


if __name__ == "__main__":
    unittest.main()
