"""Protocollo seriale Raspberry Pi <-> Arduino, revisione 1.1.

Il frame e' ASCII: ``<payload>*<HH>\\n`` dove ``HH`` e' lo XOR di tutti i
byte del payload. Questo modulo non parla con l'hardware: codifica, decodifica
e valida i messaggi.
"""

from __future__ import annotations

from dataclasses import dataclass

PROTOCOL_VERSION = "1"
MAX_FRAME_BYTES = 96
SEQUENCE_MAX = 0xFFFF
MOTOR_MIN = -255
MOTOR_MAX = 255
SERVO_MIN = 0
SERVO_MAX = 180
STATUS_MAX = 0xFFFF

STATUS_FLAGS: dict[int, str] = {
    0: "sonar_valid",
    1: "imu_valid",
    2: "motors_active",
    3: "watchdog_tripped",
    4: "estop_active",
    5: "servo_ready",
}

ERROR_CODES = frozenset(
    {
        "UNKNOWN_COMMAND",
        "BAD_FORMAT",
        "BAD_RANGE",
        "BAD_CHECKSUM",
        "LINE_TOO_LONG",
        "WATCHDOG_STOP",
        "MOTION_DISABLED",
        "SERVO_UNVERIFIED",
    }
)

INCOMING_KINDS = frozenset({"V", "A", "E", "K"})


class ProtocolError(ValueError):
    """Errore di protocollo con un codice adatto al log e al campo E."""

    def __init__(self, code: str, detail: str = "") -> None:
        self.code = code
        self.detail = detail
        message = code if not detail else f"{code}: {detail}"
        super().__init__(message)


def checksum(payload: str) -> int:
    """XOR dei byte ASCII del payload."""
    if not isinstance(payload, str):
        raise TypeError("payload must be a string")

    try:
        data = payload.encode("ascii")
    except UnicodeEncodeError as exc:
        raise ProtocolError("BAD_FORMAT", "payload non ASCII") from exc

    value = 0
    for byte in data:
        value ^= byte
    return value


def encode(payload: str) -> bytes:
    """Costruisce un frame completo con checksum e newline."""
    if not isinstance(payload, str):
        raise TypeError("payload must be a string")
    if not payload:
        raise ProtocolError("BAD_FORMAT", "payload vuoto")
    if any(char in payload for char in ("*", "\n", "\r")):
        raise ProtocolError("BAD_FORMAT", "carattere riservato nel payload")

    frame = f"{payload}*{checksum(payload):02X}\n"
    if len(frame.encode("ascii")) > MAX_FRAME_BYTES:
        raise ProtocolError("LINE_TOO_LONG", f"frame oltre {MAX_FRAME_BYTES} byte")
    return frame.encode("ascii")


@dataclass(frozen=True)
class Frame:
    """Frame sintatticamente valido, con checksum gia' verificato."""

    kind: str
    fields: tuple[str, ...]
    payload: str
    checksum: int

    def require_fields(self, count: int) -> None:
        if len(self.fields) != count:
            raise ProtocolError(
                "BAD_FORMAT",
                f"{self.kind}: attesi {count} campi, trovati {len(self.fields)}",
            )

    def integer(self, index: int) -> int:
        try:
            return int(self.fields[index], 10)
        except (IndexError, ValueError) as exc:
            raise ProtocolError("BAD_FORMAT", f"{self.kind}: campo {index} non intero") from exc

    @property
    def sequence(self) -> int | None:
        if self.kind in {"H", "D", "X", "Z", "A", "K"} and self.fields:
            return self.integer(0)
        return None


def parse_frame(line: bytes | bytearray | str) -> Frame:
    """Valida un frame ricevuto e ne restituisce i campi."""
    if isinstance(line, (bytes, bytearray)):
        try:
            text = bytes(line).decode("ascii")
        except UnicodeDecodeError as exc:
            raise ProtocolError("BAD_FORMAT", "frame non ASCII") from exc
    elif isinstance(line, str):
        text = line
    else:
        raise TypeError("line must be bytes or str")

    text = text.rstrip("\r\n")
    if not text:
        raise ProtocolError("BAD_FORMAT", "frame vuoto")
    try:
        encoded_text = text.encode("ascii")
    except UnicodeEncodeError as exc:
        raise ProtocolError("BAD_FORMAT", "frame non ASCII") from exc
    if len(encoded_text) > MAX_FRAME_BYTES:
        raise ProtocolError("LINE_TOO_LONG", f"frame oltre {MAX_FRAME_BYTES} byte")
    if "\n" in text or "\r" in text:
        raise ProtocolError("BAD_FORMAT", "newline interna al frame")
    if text.count("*") != 1:
        raise ProtocolError("BAD_FORMAT", "checksum mancante o duplicato")

    payload, checksum_text = text.rsplit("*", 1)
    if len(checksum_text) != 2:
        raise ProtocolError("BAD_FORMAT", "checksum non di due cifre")
    try:
        received_checksum = int(checksum_text, 16)
    except ValueError as exc:
        raise ProtocolError("BAD_FORMAT", "checksum non esadecimale") from exc

    expected_checksum = checksum(payload)
    if received_checksum != expected_checksum:
        raise ProtocolError(
            "BAD_CHECKSUM",
            f"atteso {expected_checksum:02X}, ricevuto {checksum_text.upper()}",
        )

    parts = payload.split(",")
    kind = parts[0]
    if len(kind) != 1 or not kind.isalpha() or not kind.isupper():
        raise ProtocolError("BAD_FORMAT", "tipo messaggio non valido")

    return Frame(kind=kind, fields=tuple(parts[1:]), payload=payload, checksum=received_checksum)


def _validate_sequence(sequence: int) -> int:
    if isinstance(sequence, bool) or not isinstance(sequence, int):
        raise TypeError("sequence must be an int")
    if not 0 <= sequence <= SEQUENCE_MAX:
        raise ProtocolError("BAD_RANGE", f"sequenza fuori range: {sequence}")
    return sequence


def _validate_motor(value: int, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{name} must be an int")
    if not MOTOR_MIN <= value <= MOTOR_MAX:
        raise ProtocolError("BAD_RANGE", f"{name} fuori range: {value}")
    return value


def _validate_status(status: int) -> int:
    if isinstance(status, bool) or not isinstance(status, int):
        raise TypeError("status must be an int")
    if not 0 <= status <= STATUS_MAX:
        raise ProtocolError("BAD_RANGE", f"status fuori range: {status}")
    return status


def version_request() -> bytes:
    return encode(f"V,{PROTOCOL_VERSION}")


def version_response(
    protocol: str = PROTOCOL_VERSION,
    board: str = "ARDUINO_MEGA",
    firmware: str = "1",
) -> bytes:
    return encode(f"V,{protocol},{board},{firmware}")


def heartbeat(sequence: int) -> bytes:
    return encode(f"H,{_validate_sequence(sequence)}")


def drive(sequence: int, left: int, right: int) -> bytes:
    _validate_sequence(sequence)
    _validate_motor(left, "left")
    _validate_motor(right, "right")
    return encode(f"D,{sequence},{left},{right}")


def stop(sequence: int) -> bytes:
    return encode(f"X,{_validate_sequence(sequence)}")


def servo(sequence: int, angle: int) -> bytes:
    _validate_sequence(sequence)
    if isinstance(angle, bool) or not isinstance(angle, int):
        raise TypeError("angle must be an int")
    if not SERVO_MIN <= angle <= SERVO_MAX:
        raise ProtocolError("BAD_RANGE", f"angolo servo fuori range: {angle}")
    return encode(f"Z,{sequence},{angle}")


def ack(sequence: int) -> bytes:
    return encode(f"K,{_validate_sequence(sequence)}")


def error(code: str) -> bytes:
    if code not in ERROR_CODES:
        raise ProtocolError("BAD_FORMAT", f"codice errore sconosciuto: {code}")
    return encode(f"E,{code}")


def sensor_status(
    sequence: int,
    distance_mm: int,
    yaw_mdeg: int,
    pitch_mdeg: int,
    roll_mdeg: int,
    status: int,
) -> bytes:
    _validate_sequence(sequence)
    if isinstance(distance_mm, bool) or not isinstance(distance_mm, int):
        raise TypeError("distance_mm must be an int")
    if distance_mm < -1:
        raise ProtocolError("BAD_RANGE", f"distanza fuori range: {distance_mm}")
    _validate_status(status)
    for value, name in (
        (yaw_mdeg, "yaw_mdeg"),
        (pitch_mdeg, "pitch_mdeg"),
        (roll_mdeg, "roll_mdeg"),
    ):
        if isinstance(value, bool) or not isinstance(value, int):
            raise TypeError(f"{name} must be an int")
    return encode(
        f"A,{sequence},{distance_mm},{yaw_mdeg},{pitch_mdeg},{roll_mdeg},{status}"
    )


@dataclass(frozen=True)
class VersionInfo:
    protocol: str
    board: str
    firmware: str


@dataclass(frozen=True)
class SensorReading:
    sequence: int
    distance_mm: int
    yaw_mdeg: int
    pitch_mdeg: int
    roll_mdeg: int
    status: int

    @property
    def flags(self) -> dict[str, bool]:
        return status_flags(self.status)


def parse_version(frame: Frame) -> VersionInfo:
    if frame.kind != "V":
        raise ProtocolError("BAD_FORMAT", f"atteso V, ricevuto {frame.kind}")
    frame.require_fields(3)
    protocol, board, firmware = frame.fields
    if protocol != PROTOCOL_VERSION:
        raise ProtocolError("BAD_FORMAT", f"versione protocollo non supportata: {protocol}")
    if not board or not firmware:
        raise ProtocolError("BAD_FORMAT", "board o firmware vuoti")
    return VersionInfo(protocol=protocol, board=board, firmware=firmware)


def parse_sensor(frame: Frame) -> SensorReading:
    if frame.kind != "A":
        raise ProtocolError("BAD_FORMAT", f"atteso A, ricevuto {frame.kind}")
    frame.require_fields(6)

    sequence = frame.integer(0)
    distance_mm = frame.integer(1)
    yaw_mdeg = frame.integer(2)
    pitch_mdeg = frame.integer(3)
    roll_mdeg = frame.integer(4)
    status = frame.integer(5)

    _validate_sequence(sequence)
    if distance_mm < -1:
        raise ProtocolError("BAD_RANGE", f"distanza fuori range: {distance_mm}")
    _validate_status(status)

    return SensorReading(
        sequence=sequence,
        distance_mm=distance_mm,
        yaw_mdeg=yaw_mdeg,
        pitch_mdeg=pitch_mdeg,
        roll_mdeg=roll_mdeg,
        status=status,
    )


def parse_ack(frame: Frame) -> int:
    if frame.kind != "K":
        raise ProtocolError("BAD_FORMAT", f"atteso K, ricevuto {frame.kind}")
    frame.require_fields(1)
    sequence = frame.integer(0)
    _validate_sequence(sequence)
    return sequence


def parse_error(frame: Frame) -> str:
    if frame.kind != "E":
        raise ProtocolError("BAD_FORMAT", f"atteso E, ricevuto {frame.kind}")
    frame.require_fields(1)
    code = frame.fields[0]
    if not code:
        raise ProtocolError("BAD_FORMAT", "codice errore vuoto")
    return code


def parse_incoming(frame: Frame) -> VersionInfo | SensorReading | int | str:
    """Interpreta un messaggio Arduino -> Raspberry; rifiuta i tipi sconosciuti."""
    if frame.kind not in INCOMING_KINDS:
        raise ProtocolError("UNKNOWN_COMMAND", f"tipo inatteso: {frame.kind}")
    if frame.kind == "V":
        return parse_version(frame)
    if frame.kind == "A":
        return parse_sensor(frame)
    if frame.kind == "K":
        return parse_ack(frame)
    return parse_error(frame)


def status_flags(status: int) -> dict[str, bool]:
    _validate_status(status)
    return {
        name: bool(status & (1 << bit))
        for bit, name in STATUS_FLAGS.items()
    }
