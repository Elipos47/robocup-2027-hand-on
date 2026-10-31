"""Trasporti seriali: reale e finto per i test."""

from __future__ import annotations

from collections import deque
from typing import Protocol, runtime_checkable


@runtime_checkable
class Transport(Protocol):
    """Interfaccia minima usata dal session layer."""

    def write(self, data: bytes) -> None:
        ...

    def read_line(self, timeout: float | None = None) -> bytes | None:
        ...

    def close(self) -> None:
        ...


class FakeTransport:
    """Trasporto in memoria: utile per test e demo senza hardware."""

    def __init__(self) -> None:
        self.sent: list[bytes] = []
        self._incoming: deque[bytes] = deque()
        self.closed = False

    def feed_line(self, line: bytes | str) -> None:
        if self.closed:
            raise RuntimeError("transport closed")
        if isinstance(line, str):
            raw = line.encode("ascii")
        elif isinstance(line, (bytes, bytearray)):
            raw = bytes(line)
        else:
            raise TypeError("line must be bytes or str")
        if not raw.endswith(b"\n"):
            raw += b"\n"
        self._incoming.append(raw)

    def write(self, data: bytes) -> None:
        if self.closed:
            raise RuntimeError("transport closed")
        if not isinstance(data, (bytes, bytearray)):
            raise TypeError("data must be bytes")
        self.sent.append(bytes(data))

    def read_line(self, timeout: float | None = None) -> bytes | None:
        del timeout  # il finto trasporto risponde subito
        if self.closed:
            raise RuntimeError("transport closed")
        if not self._incoming:
            return None
        return self._incoming.popleft()

    def sent_text(self) -> list[str]:
        return [data.decode("ascii", errors="replace") for data in self.sent]

    def close(self) -> None:
        self.closed = True

    def __enter__(self) -> "FakeTransport":
        return self

    def __exit__(self, *args: object) -> None:
        self.close()


class SerialTransport:
    """Trasporto reale su pyserial.

    pyserial viene importato solo quando si apre una porta reale, cosi' i test
    e la modalita' finta funzionano anche senza il pacchetto installato.
    """

    def __init__(self, port: str, baudrate: int = 115200, timeout: float = 0.1) -> None:
        try:
            import serial
        except ImportError as exc:
            raise RuntimeError(
                "pyserial non installato: esegui 'pip install -r software/requirements.txt'"
            ) from exc

        self._serial = serial.Serial(port=port, baudrate=baudrate, timeout=timeout)

    def write(self, data: bytes) -> None:
        if not isinstance(data, (bytes, bytearray)):
            raise TypeError("data must be bytes")
        self._serial.write(bytes(data))
        self._serial.flush()

    def read_line(self, timeout: float | None = None) -> bytes | None:
        previous_timeout = self._serial.timeout
        if timeout is not None:
            self._serial.timeout = timeout
        try:
            line = self._serial.readline()
        finally:
            self._serial.timeout = previous_timeout
        return line or None

    def close(self) -> None:
        self._serial.close()

    def __enter__(self) -> "SerialTransport":
        return self

    def __exit__(self, *args: object) -> None:
        self.close()
