from __future__ import annotations

import unittest

from rcj2027 import protocol


class ChecksumTests(unittest.TestCase):
    def test_known_checksum(self) -> None:
        self.assertEqual(protocol.checksum("D,17,90,-90"), 0x43)

    def test_encode_drive_example(self) -> None:
        self.assertEqual(protocol.encode("D,17,90,-90"), b"D,17,90,-90*43\n")

    def test_non_ascii_payload(self) -> None:
        with self.assertRaises(protocol.ProtocolError) as ctx:
            protocol.checksum("D,1,è,2")
        self.assertEqual(ctx.exception.code, "BAD_FORMAT")


class EncoderTests(unittest.TestCase):
    def test_version_request(self) -> None:
        self.assertEqual(protocol.version_request(), b"V,1*4B\n")

    def test_version_response(self) -> None:
        self.assertEqual(
            protocol.version_response(), b"V,1,ARDUINO_MEGA,1*61\n"
        )

    def test_heartbeat(self) -> None:
        self.assertEqual(protocol.heartbeat(18), b"H,18*6D\n")

    def test_drive(self) -> None:
        self.assertEqual(protocol.drive(17, 90, -90), b"D,17,90,-90*43\n")

    def test_stop(self) -> None:
        self.assertEqual(protocol.stop(19), b"X,19*7C\n")

    def test_servo(self) -> None:
        self.assertEqual(protocol.servo(20, 90), b"Z,20,90*51\n")

    def test_ack(self) -> None:
        self.assertEqual(protocol.ack(17), b"K,17*61\n")

    def test_error(self) -> None:
        self.assertEqual(protocol.error("BAD_RANGE"), b"E,BAD_RANGE*2E\n")

    def test_sensor_status(self) -> None:
        self.assertEqual(
            protocol.sensor_status(18, 145, -1200, 35, 0, 3),
            b"A,18,145,-1200,35,0,3*53\n",
        )

    def test_motor_out_of_range(self) -> None:
        for value in (-256, 256):
            with self.assertRaises(protocol.ProtocolError) as ctx:
                protocol.drive(1, value, 0)
            self.assertEqual(ctx.exception.code, "BAD_RANGE")

    def test_sequence_out_of_range(self) -> None:
        for value in (-1, 65536):
            with self.assertRaises(protocol.ProtocolError) as ctx:
                protocol.heartbeat(value)
            self.assertEqual(ctx.exception.code, "BAD_RANGE")

    def test_servo_out_of_range(self) -> None:
        for value in (-1, 181):
            with self.assertRaises(protocol.ProtocolError) as ctx:
                protocol.servo(1, value)
            self.assertEqual(ctx.exception.code, "BAD_RANGE")

    def test_reserved_character(self) -> None:
        with self.assertRaises(protocol.ProtocolError) as ctx:
            protocol.encode("D,1,0,0*00")
        self.assertEqual(ctx.exception.code, "BAD_FORMAT")

    def test_line_too_long(self) -> None:
        with self.assertRaises(protocol.ProtocolError) as ctx:
            protocol.encode("D," + "1" * 120)
        self.assertEqual(ctx.exception.code, "LINE_TOO_LONG")

    def test_max_length_boundary(self) -> None:
        frame = protocol.encode("D," + "1" * 90)
        self.assertEqual(len(frame), 96)
        self.assertEqual(protocol.parse_frame(frame).kind, "D")


class ParserTests(unittest.TestCase):
    def test_parse_version(self) -> None:
        frame = protocol.parse_frame(b"V,1,ARDUINO_MEGA,1*61\n")
        info = protocol.parse_incoming(frame)
        self.assertIsInstance(info, protocol.VersionInfo)
        assert isinstance(info, protocol.VersionInfo)
        self.assertEqual(info.protocol, "1")
        self.assertEqual(info.board, "ARDUINO_MEGA")
        self.assertEqual(info.firmware, "1")

    def test_parse_sensor_and_flags(self) -> None:
        frame = protocol.parse_frame(b"A,18,145,-1200,35,0,3*53\n")
        reading = protocol.parse_incoming(frame)
        self.assertIsInstance(reading, protocol.SensorReading)
        assert isinstance(reading, protocol.SensorReading)
        self.assertEqual(reading.sequence, 18)
        self.assertEqual(reading.distance_mm, 145)
        self.assertEqual(reading.yaw_mdeg, -1200)
        self.assertTrue(reading.flags["sonar_valid"])
        self.assertTrue(reading.flags["imu_valid"])
        self.assertFalse(reading.flags["watchdog_tripped"])

    def test_parse_ack(self) -> None:
        frame = protocol.parse_frame(b"K,17*61\n")
        self.assertEqual(protocol.parse_incoming(frame), 17)

    def test_parse_error(self) -> None:
        frame = protocol.parse_frame(b"E,BAD_RANGE*2E\n")
        self.assertEqual(protocol.parse_incoming(frame), "BAD_RANGE")

    def test_parse_crlf(self) -> None:
        frame = protocol.parse_frame(b"K,17*61\r\n")
        self.assertEqual(protocol.parse_ack(frame), 17)

    def test_bad_checksum(self) -> None:
        with self.assertRaises(protocol.ProtocolError) as ctx:
            protocol.parse_frame(b"D,17,90,-90*00\n")
        self.assertEqual(ctx.exception.code, "BAD_CHECKSUM")

    def test_duplicate_checksum_separator(self) -> None:
        with self.assertRaises(protocol.ProtocolError) as ctx:
            protocol.parse_frame(b"K,17*61*61\n")
        self.assertEqual(ctx.exception.code, "BAD_FORMAT")

    def test_line_too_long_on_parse(self) -> None:
        line = b"K," + b"1" * 100 + b"*00\n"
        with self.assertRaises(protocol.ProtocolError) as ctx:
            protocol.parse_frame(line)
        self.assertEqual(ctx.exception.code, "LINE_TOO_LONG")

    def test_lowercase_kind_rejected(self) -> None:
        with self.assertRaises(protocol.ProtocolError) as ctx:
            protocol.parse_frame(protocol.encode("d,1,0,0"))
        self.assertEqual(ctx.exception.code, "BAD_FORMAT")

    def test_missing_checksum(self) -> None:
        with self.assertRaises(protocol.ProtocolError) as ctx:
            protocol.parse_frame(b"D,17,90,-90\n")
        self.assertEqual(ctx.exception.code, "BAD_FORMAT")

    def test_empty_frame(self) -> None:
        with self.assertRaises(protocol.ProtocolError) as ctx:
            protocol.parse_frame(b"\n")
        self.assertEqual(ctx.exception.code, "BAD_FORMAT")

    def test_non_ascii_frame(self) -> None:
        with self.assertRaises(protocol.ProtocolError) as ctx:
            protocol.parse_frame(b"D,1,90,90*00\xff\n")
        self.assertEqual(ctx.exception.code, "BAD_FORMAT")

    def test_wrong_field_count(self) -> None:
        frame = protocol.parse_frame(protocol.encode("A,1,100,0,0,0"))
        with self.assertRaises(protocol.ProtocolError) as ctx:
            protocol.parse_sensor(frame)
        self.assertEqual(ctx.exception.code, "BAD_FORMAT")

    def test_invalid_distance(self) -> None:
        frame = protocol.parse_frame(protocol.encode("A,1,-2,0,0,0,0"))
        with self.assertRaises(protocol.ProtocolError) as ctx:
            protocol.parse_sensor(frame)
        self.assertEqual(ctx.exception.code, "BAD_RANGE")

    def test_unknown_incoming_kind(self) -> None:
        frame = protocol.parse_frame(protocol.encode("H,1"))
        with self.assertRaises(protocol.ProtocolError) as ctx:
            protocol.parse_incoming(frame)
        self.assertEqual(ctx.exception.code, "UNKNOWN_COMMAND")

    def test_status_flags(self) -> None:
        flags = protocol.status_flags(0b100101)
        self.assertTrue(flags["sonar_valid"])
        self.assertFalse(flags["imu_valid"])
        self.assertTrue(flags["motors_active"])
        self.assertFalse(flags["watchdog_tripped"])
        self.assertFalse(flags["estop_active"])
        self.assertTrue(flags["servo_ready"])


if __name__ == "__main__":
    unittest.main()
