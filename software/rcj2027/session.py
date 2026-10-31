"""Sessione seriale Raspberry Pi <-> Arduino: handshake, heartbeat, status e log.

La sessione non decide il movimento: apre il link, tiene vivo l'Arduino con gli
heartbeat, interpreta i frame in arrivo e li registra. Il gate di movimento
resta in ``safety.py``.
"""

from __future__ import annotations

import time
from dataclasses import asdict
from typing import Callable

from . import protocol
from .logger import JsonlLogger
from .safety import DEFAULT_CONFIG, HardwareConfig
from .transport import Transport


class SessionError(RuntimeError):
    """La sessione non puo' continuare (handshake fallito o link non pronto)."""


class CommandRejected(RuntimeError):
    """L'Arduino ha rifiutato un comando o non ha risposto in tempo."""

    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(f"comando rifiutato: {code}")


class RobotSession:
    """Collega trasporto, protocollo, sicurezza e logger in un'unica sessione."""

    def __init__(
        self,
        transport: Transport,
        logger: JsonlLogger,
        *,
        config: HardwareConfig = DEFAULT_CONFIG,
        heartbeat_interval_s: float = 0.2,
        link_timeout_s: float = 0.5,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        if heartbeat_interval_s <= 0:
            raise ValueError("heartbeat_interval_s deve essere positivo")
        if link_timeout_s <= 0:
            raise ValueError("link_timeout_s deve essere positivo")

        self.transport = transport
        self.logger = logger
        self.config = config
        self.heartbeat_interval_s = heartbeat_interval_s
        self.link_timeout_s = link_timeout_s
        self._clock = clock

        self.sequence = 0
        self.handshake_info: protocol.VersionInfo | None = None
        self.last_status: protocol.SensorReading | None = None
        self.last_status_flags: dict[str, bool] | None = None
        self.status_count = 0
        self.heartbeat_count = 0
        self.error_count = 0
        self.invalid_count = 0
        self.discarded_count = 0
        self.watchdog_tripped = False

        self._next_heartbeat_at = clock()
        self._last_rx_at: float | None = None
        self._last_status_at: float | None = None
        self._link_down = False
        self._link_down_since: float | None = None
        self._closed = False

    # ------------------------------------------------------------------ link

    def handshake(
        self,
        *,
        boot_delay_s: float = 0.0,
        attempts: int = 3,
        reads_per_attempt: int = 500,
        read_timeout_s: float = 0.1,
        timeout_s: float = 2.0,
    ) -> protocol.VersionInfo:
        """Invia ``V`` e attende la versione del firmware.

        ``boot_delay_s`` copre il reset provocato dall'apertura della porta
        seriale sul Mega. I tentativi rendono l'operazione ripetibile senza
        dipendere da una singola lettura. Se il Mega sta gia' inviando status,
        l'handshake li drena fino alla risposta ``V`` entro ``timeout_s``.
        """
        if self.handshake_info is not None:
            return self.handshake_info
        if boot_delay_s < 0:
            raise ValueError("boot_delay_s non puo' essere negativo")
        if attempts < 1 or reads_per_attempt < 1:
            raise ValueError("attempts e reads_per_attempt devono essere positivi")
        if timeout_s <= 0:
            raise ValueError("timeout_s deve essere positivo")

        started = self._clock()
        if boot_delay_s:
            time.sleep(boot_delay_s)

        for attempt in range(1, attempts + 1):
            self.logger.log("handshake_request", attempt=attempt)
            request_at = self._clock()
            deadline = request_at + timeout_s
            self.transport.write(protocol.version_request())

            for _ in range(reads_per_attempt):
                now = self._clock()
                if now >= deadline:
                    break
                remaining = deadline - now
                line = self.transport.read_line(
                    timeout=min(read_timeout_s, remaining)
                )
                if line is None:
                    continue
                message = self._consume_line(line)
                if isinstance(message, protocol.VersionInfo):
                    now = self._clock()
                    self.handshake_info = message
                    self._last_rx_at = now
                    self._last_status_at = now
                    self._next_heartbeat_at = now
                    self.logger.log(
                        "handshake_ok",
                        attempt=attempt,
                        elapsed_ms=round((now - started) * 1000.0, 1),
                        response_ms=round((now - request_at) * 1000.0, 1),
                        discarded_frames=self.discarded_count,
                        safety=self.config.snapshot(),
                    )
                    return message

            self.logger.log("handshake_retry", attempt=attempt)

        self.logger.log(
            "handshake_failed",
            attempts=attempts,
            discarded_frames=self.discarded_count,
        )
        raise SessionError(f"handshake fallito dopo {attempts} tentativi")

    def _require_handshake(self) -> None:
        if self.handshake_info is None:
            raise SessionError("handshake non completato")

    def _next_sequence(self) -> int:
        sequence = self.sequence
        self.sequence = (self.sequence + 1) & protocol.SEQUENCE_MAX
        return sequence

    def send_heartbeat(self) -> int:
        self._require_handshake()
        sequence = self._next_sequence()
        self.transport.write(protocol.heartbeat(sequence))
        self.heartbeat_count += 1
        self.logger.log("heartbeat", sequence=sequence)
        return sequence

    def drive(
        self,
        left: int,
        right: int,
        *,
        wait_ack_s: float = 0.5,
        read_timeout_s: float = 0.05,
    ) -> int:
        """Invia ``D`` solo se il gate di movimento e' completo.

        I valori sono limitati a ``config.pwm_max`` e devono essere interi.
        Durante l'attesa dell'ack la sessione continua a inviare heartbeat.
        """
        self.config.require_motion()
        self._require_handshake()
        if wait_ack_s < 0:
            raise ValueError("wait_ack_s non puo' essere negativo")
        if read_timeout_s <= 0:
            raise ValueError("read_timeout_s deve essere positivo")

        pwm_max = self.config.pwm_max
        if isinstance(pwm_max, bool) or not isinstance(pwm_max, int):
            raise SessionError("pwm_max non valido dopo il gate")

        for name, value in (("left", left), ("right", right)):
            if isinstance(value, bool) or not isinstance(value, int):
                raise TypeError(f"{name} must be an int")
            if abs(value) > pwm_max:
                raise ValueError(f"{name} fuori limite pwm_max={pwm_max}: {value}")

        sequence = self._next_sequence()
        self.transport.write(protocol.drive(sequence, left, right))
        self.logger.log(
            "drive_sent",
            sequence=sequence,
            left=left,
            right=right,
            pwm_max=pwm_max,
        )

        try:
            accepted = self._wait_for_ack(
                sequence,
                wait_ack_s=wait_ack_s,
                read_timeout_s=read_timeout_s,
            )
        except CommandRejected as exc:
            self.logger.log("drive_rejected", sequence=sequence, code=exc.code)
            self._safe_stop(reason="drive_rejected")
            raise

        if not accepted:
            self.logger.log(
                "drive_ack_timeout",
                sequence=sequence,
                wait_s=wait_ack_s,
            )
            self._safe_stop(reason="drive_ack_timeout")
            raise CommandRejected("ACK_TIMEOUT")

        self.logger.log("drive_ack", sequence=sequence)
        return sequence

    def _wait_for_ack(
        self,
        sequence: int,
        *,
        wait_ack_s: float,
        read_timeout_s: float,
    ) -> bool:
        attempts = max(1, int(wait_ack_s / read_timeout_s))
        for _ in range(attempts):
            self._maybe_heartbeat(self._clock())
            line = self.transport.read_line(timeout=read_timeout_s)
            if line is None:
                continue
            message = self._consume_line(line)
            if isinstance(message, int) and message == sequence:
                return True
            if isinstance(message, str):
                raise CommandRejected(message)
        return False

    def _safe_stop(self, *, reason: str) -> None:
        try:
            self.stop(wait_ack_s=0.2)
        except (OSError, RuntimeError) as exc:
            self.logger.log("stop_failed", error=str(exc), reason=reason)

    def _maybe_heartbeat(self, now: float) -> None:
        if now >= self._next_heartbeat_at:
            self.send_heartbeat()
            self._next_heartbeat_at = now + self.heartbeat_interval_s

    def step(self, *, now: float | None = None, read_timeout_s: float = 0.05) -> bool:
        """Esegue un ciclo: heartbeat se dovuto, una lettura, controllo link."""
        self._require_handshake()
        current = self._clock() if now is None else now

        self._maybe_heartbeat(current)

        line = self.transport.read_line(timeout=read_timeout_s)
        received = line is not None
        if received:
            self._consume_line(line)

        self._check_link(current)
        return received

    def run(self, duration_s: float, *, read_timeout_s: float = 0.05) -> None:
        """Mantiene la sessione per ``duration_s`` secondi (tempo monotono)."""
        if duration_s <= 0:
            raise ValueError("duration_s deve essere positivo")
        self._require_handshake()

        started = self._clock()
        while self._clock() - started < duration_s:
            self.step(read_timeout_s=read_timeout_s)

    def stop(self, *, wait_ack_s: float = 0.5, read_timeout_s: float = 0.05) -> bool:
        """Invia ``X`` e attende l'ack entro il tempo indicato."""
        self._require_handshake()
        sequence = self._next_sequence()
        self.transport.write(protocol.stop(sequence))
        self.logger.log("stop_sent", sequence=sequence)

        attempts = max(1, int(wait_ack_s / read_timeout_s))
        for _ in range(attempts):
            line = self.transport.read_line(timeout=read_timeout_s)
            if line is None:
                continue
            message = self._consume_line(line)
            if isinstance(message, int) and message == sequence:
                self.logger.log("stop_ack", sequence=sequence)
                return True

        self.logger.log("stop_ack_timeout", sequence=sequence, wait_s=wait_ack_s)
        return False

    def close(self, *, reason: str = "session_end") -> None:
        """Ferma i motori (se il link e' pronto) e chiude il trasporto."""
        if self._closed:
            return

        stop_ok: bool | None = None
        stop_error: str | None = None
        if self.handshake_info is not None:
            try:
                stop_ok = self.stop()
            except (OSError, RuntimeError) as exc:
                stop_error = str(exc)
                self.logger.log("stop_failed", error=stop_error)

        self._closed = True
        try:
            self.transport.close()
        finally:
            self.logger.log(
                "session_end",
                reason=reason,
                heartbeats=self.heartbeat_count,
                statuses=self.status_count,
                errors=self.error_count,
                invalid_frames=self.invalid_count,
                discarded_frames=self.discarded_count,
                watchdog_tripped=self.watchdog_tripped,
                stop_ack=stop_ok,
                stop_error=stop_error,
            )

    def __enter__(self) -> "RobotSession":
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    # --------------------------------------------------------------- ricezione

    def _consume_line(self, line: bytes | bytearray | str) -> object | None:
        raw = (
            bytes(line).decode("ascii", errors="replace").rstrip("\r\n")
            if isinstance(line, (bytes, bytearray))
            else str(line).rstrip("\r\n")
        )

        try:
            frame = protocol.parse_frame(line)
            message = protocol.parse_incoming(frame)
        except protocol.ProtocolError as exc:
            if self.handshake_info is None:
                self.discarded_count += 1
                return None
            self.invalid_count += 1
            self.logger.log(
                "rx_invalid",
                error=exc.code,
                detail=exc.detail,
                frame=raw,
            )
            return None

        now = self._clock()
        self._last_rx_at = now
        if self._link_down:
            self._link_down = False
            down_s = 0.0 if self._link_down_since is None else now - self._link_down_since
            self._link_down_since = None
            self.logger.log("link_restored", down_s=round(down_s, 3))

        if isinstance(message, protocol.VersionInfo):
            self.logger.log("version", **asdict(message))
        elif isinstance(message, protocol.SensorReading):
            if self.handshake_info is None:
                self.discarded_count += 1
                return message
            self._record_status(message)
        elif isinstance(message, int):
            self.logger.log("ack", sequence=message)
        else:
            self.error_count += 1
            self.logger.log("arduino_error", code=message)
            if message == "WATCHDOG_STOP":
                self.watchdog_tripped = True
                self.logger.log("watchdog_stop")

        return message

    def _record_status(self, reading: protocol.SensorReading) -> None:
        self.status_count += 1
        self.last_status = reading
        flags = reading.flags
        self.logger.log("status", **asdict(reading), flags=flags)

        if self.last_status_flags is not None and flags != self.last_status_flags:
            changed = [
                name
                for name, value in flags.items()
                if value != self.last_status_flags.get(name)
            ]
            self.logger.log(
                "status_change",
                status=reading.status,
                changed=changed,
                flags=flags,
            )

        self.last_status_flags = flags
        self._last_status_at = self._clock()

    def _check_link(self, now: float) -> None:
        reference = self._last_status_at
        if reference is None:
            reference = self._last_rx_at
        if reference is None:
            return

        elapsed = now - reference
        if elapsed > self.link_timeout_s and not self._link_down:
            self._link_down = True
            self._link_down_since = now
            self.logger.log(
                "link_lost",
                last_status_s=round(elapsed, 3),
                timeout_s=self.link_timeout_s,
            )
