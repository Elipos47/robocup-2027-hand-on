from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from rcj2027 import protocol
from rcj2027.logger import JsonlLogger
from rcj2027.safety import HardwareConfig, SafetyError
from rcj2027.session import CommandRejected, RobotSession, SessionError
from rcj2027.transport import FakeTransport


class FakeClock:
    def __init__(self, value: float = 0.0) -> None:
        self.value = value

    def __call__(self) -> float:
        return self.value


class SessionTestBase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.path = Path(self._tmp.name) / "run.jsonl"
        self.logger = JsonlLogger(self.path, "test-run")
        self.addCleanup(self.logger.close)
        self.transport = FakeTransport()
        self.clock = FakeClock()

    def make_session(self, **kwargs: object) -> RobotSession:
        return RobotSession(
            self.transport,
            self.logger,
            clock=self.clock,
            **kwargs,
        )

    def connect(self, **kwargs: object) -> RobotSession:
        session = self.make_session(**kwargs)
        self.transport.feed_line(protocol.version_response())
        session.handshake()
        return session

    def records(self) -> list[dict[str, object]]:
        return [
            json.loads(line)
            for line in self.path.read_text(encoding="utf-8").splitlines()
        ]

    def events(self) -> list[str]:
        return [str(record["event"]) for record in self.records()]

    def find(self, event: str) -> list[dict[str, object]]:
        return [
            record for record in self.records() if record["event"] == event
        ]


class HandshakeTests(SessionTestBase):
    def test_handshake_logs_version_and_safety(self) -> None:
        session = self.make_session()
        self.transport.feed_line(protocol.version_response())

        info = session.handshake()

        self.assertEqual(info.protocol, "1")
        self.assertEqual(info.board, "ARDUINO_MEGA")
        self.assertEqual(info.firmware, "1")
        self.assertEqual(self.transport.sent_text()[0], "V,1*4B\n")

        handshake = self.find("handshake_ok")[0]
        self.assertEqual(handshake["attempt"], 1)
        self.assertEqual(handshake["safety"]["motion_enabled"], False)
        self.assertIn("pwm_max", handshake["safety"]["missing_for_motion"])
        self.assertIn("watchdog_timeout_s", handshake["safety"]["missing_for_motion"])
        self.assertEqual(len(self.find("version")), 1)

    def test_handshake_retries_then_fails(self) -> None:
        session = self.make_session()

        with self.assertRaises(SessionError):
            session.handshake(attempts=2, reads_per_attempt=1)

        self.assertEqual(self.transport.sent_text(), ["V,1*4B\n", "V,1*4B\n"])
        self.assertEqual(len(self.find("handshake_retry")), 2)
        self.assertEqual(len(self.find("handshake_failed")), 1)

    def test_handshake_skips_invalid_frame(self) -> None:
        session = self.make_session()
        self.transport.feed_line("A,1,0,0,0,0,0*00")
        self.transport.feed_line(protocol.version_response())

        info = session.handshake()

        self.assertEqual(info.board, "ARDUINO_MEGA")
        self.assertEqual(session.invalid_count, 0)
        self.assertEqual(session.discarded_count, 1)
        self.assertEqual(len(self.find("rx_invalid")), 0)
        self.assertEqual(self.find("handshake_ok")[0]["discarded_frames"], 1)

    def test_handshake_drains_status_frames_before_version(self) -> None:
        session = self.make_session()
        for sequence in range(5):
            self.transport.feed_line(
                protocol.sensor_status(sequence, -1, 0, 0, 0, 0)
            )
        self.transport.feed_line(protocol.version_response())

        session.handshake()

        self.assertEqual(session.status_count, 0)
        self.assertEqual(session.discarded_count, 5)
        self.assertEqual(len(self.find("status")), 0)
        self.assertEqual(self.find("handshake_ok")[0]["discarded_frames"], 5)


class StatusTests(SessionTestBase):
    def test_status_is_logged_with_flags(self) -> None:
        session = self.connect()
        self.transport.feed_line(
            protocol.sensor_status(
                sequence=7,
                distance_mm=250,
                yaw_mdeg=-100,
                pitch_mdeg=20,
                roll_mdeg=0,
                status=0b1101,
            )
        )

        received = session.step(now=0.0)

        self.assertTrue(received)
        self.assertEqual(session.status_count, 1)
        self.assertIsNotNone(session.last_status)

        status = self.find("status")[0]
        self.assertEqual(status["sequence"], 7)
        self.assertEqual(status["distance_mm"], 250)
        self.assertEqual(status["yaw_mdeg"], -100)
        self.assertTrue(status["flags"]["sonar_valid"])
        self.assertTrue(status["flags"]["motors_active"])
        self.assertTrue(status["flags"]["watchdog_tripped"])
        self.assertFalse(status["flags"]["imu_valid"])

    def test_status_change_is_logged_only_when_flags_change(self) -> None:
        session = self.connect()

        for status in (0, 0, 0b100):
            self.transport.feed_line(
                protocol.sensor_status(1, -1, 0, 0, 0, status)
            )
            session.step(now=0.0)

        self.assertEqual(len(self.find("status")), 3)
        changes = self.find("status_change")
        self.assertEqual(len(changes), 1)
        self.assertEqual(changes[0]["status"], 0b100)
        self.assertEqual(changes[0]["changed"], ["motors_active"])

    def test_arduino_error_sets_watchdog_flag(self) -> None:
        session = self.connect()
        self.transport.feed_line(protocol.error("WATCHDOG_STOP"))

        session.step(now=0.0)

        self.assertEqual(session.error_count, 1)
        self.assertTrue(session.watchdog_tripped)
        self.assertEqual(self.find("arduino_error")[0]["code"], "WATCHDOG_STOP")
        self.assertEqual(len(self.find("watchdog_stop")), 1)

    def test_invalid_frame_is_logged_without_crashing(self) -> None:
        session = self.connect()
        self.transport.feed_line("A,1,0,0,0,0,0*00")

        session.step(now=0.0)

        self.assertEqual(session.invalid_count, 1)
        self.assertEqual(session.status_count, 0)
        self.assertEqual(self.find("rx_invalid")[0]["error"], "BAD_CHECKSUM")


class HeartbeatTests(SessionTestBase):
    def test_heartbeat_is_sent_at_the_configured_interval(self) -> None:
        session = self.connect(heartbeat_interval_s=0.2)

        session.step(now=0.0)
        session.step(now=0.1)
        session.step(now=0.2)

        self.assertEqual(session.heartbeat_count, 2)
        self.assertEqual(
            self.transport.sent_text(),
            [
                "V,1*4B\n",
                protocol.heartbeat(0).decode("ascii"),
                protocol.heartbeat(1).decode("ascii"),
            ],
        )
        self.assertEqual(len(self.find("heartbeat")), 2)

    def test_link_loss_is_logged_once_and_recovery_is_logged(self) -> None:
        session = self.connect(link_timeout_s=0.5)

        session.step(now=0.6)
        session.step(now=0.7)
        self.assertEqual(len(self.find("link_lost")), 1)

        self.transport.feed_line(protocol.sensor_status(1, -1, 0, 0, 0, 0))
        session.step(now=0.8)

        self.assertEqual(len(self.find("link_restored")), 1)
        self.assertEqual(session.status_count, 1)


class DriveTests(SessionTestBase):
    def motion_config(self, pwm_max: int = 200) -> HardwareConfig:
        return HardwareConfig(
            battery_nominal_v=11.1,
            motor_side_map={"A": "right", "B": "left"},
            motor_direction_polarity={"A": "inverted", "B": "inverted"},
            pwm_max=pwm_max,
            watchdog_timeout_s=1.0,
        )

    def test_drive_is_blocked_without_complete_safety_config(self) -> None:
        session = self.connect()

        with self.assertRaises(SafetyError) as ctx:
            session.drive(10, 10)

        self.assertIn("pwm_max", ctx.exception.missing)
        self.assertIn("watchdog_timeout_s", ctx.exception.missing)
        self.assertEqual(self.transport.sent_text(), ["V,1*4B\n"])

    def test_drive_sends_command_and_waits_for_ack(self) -> None:
        session = self.connect(config=self.motion_config())
        self.transport.feed_line(protocol.ack(0))

        sequence = session.drive(100, -100)

        self.assertEqual(sequence, 0)
        self.assertIn(
            protocol.drive(0, 100, -100).decode("ascii"),
            self.transport.sent_text(),
        )
        sent = self.find("drive_sent")[0]
        self.assertEqual(sent["left"], 100)
        self.assertEqual(sent["right"], -100)
        self.assertEqual(sent["pwm_max"], 200)
        self.assertEqual(len(self.find("drive_ack")), 1)

    def test_drive_keeps_heartbeat_alive_while_waiting(self) -> None:
        session = self.connect(config=self.motion_config())
        self.transport.feed_line(protocol.ack(0))

        session.drive(100, 100)

        self.assertEqual(session.heartbeat_count, 1)
        self.assertIn(protocol.heartbeat(1).decode("ascii"), self.transport.sent_text())

    def test_drive_rejects_value_above_pwm_max(self) -> None:
        session = self.connect(config=self.motion_config(pwm_max=200))

        with self.assertRaises(ValueError):
            session.drive(201, 0)

        self.assertEqual(self.transport.sent_text(), ["V,1*4B\n"])

    def test_drive_rejects_non_integer_value(self) -> None:
        session = self.connect(config=self.motion_config())

        with self.assertRaises(TypeError):
            session.drive(True, 0)  # type: ignore[arg-type]

        self.assertEqual(self.transport.sent_text(), ["V,1*4B\n"])

    def test_drive_reports_firmware_error_and_stops(self) -> None:
        session = self.connect(config=self.motion_config())
        self.transport.feed_line(protocol.error("MOTION_DISABLED"))
        self.transport.feed_line(protocol.ack(2))

        with self.assertRaises(CommandRejected) as ctx:
            session.drive(100, 100)

        self.assertEqual(ctx.exception.code, "MOTION_DISABLED")
        self.assertEqual(self.find("drive_rejected")[0]["code"], "MOTION_DISABLED")
        self.assertIn(protocol.stop(2).decode("ascii"), self.transport.sent_text())

    def test_drive_ack_timeout_stops_the_link(self) -> None:
        session = self.connect(config=self.motion_config())
        self.transport.feed_line(protocol.ack(2))

        with self.assertRaises(CommandRejected) as ctx:
            session.drive(100, 100, wait_ack_s=0.0)

        self.assertEqual(ctx.exception.code, "ACK_TIMEOUT")
        self.assertEqual(len(self.find("drive_ack_timeout")), 1)
        self.assertIn(protocol.stop(2).decode("ascii"), self.transport.sent_text())

    def test_drive_drains_status_backlog_before_ack(self) -> None:
        session = self.connect(config=self.motion_config())
        for sequence in range(20):
            self.transport.feed_line(
                protocol.sensor_status(sequence, -1, 0, 0, 0, 0)
            )
        self.transport.feed_line(protocol.ack(0))

        self.assertEqual(session.drive(100, 100), 0)
        self.assertEqual(session.status_count, 20)
        self.assertEqual(len(self.find("drive_ack")), 1)

    def test_drive_requires_handshake_with_complete_config(self) -> None:
        session = self.make_session(config=self.motion_config())

        with self.assertRaises(SessionError):
            session.drive(10, 10)


class StopTests(SessionTestBase):
    def test_stop_sends_x_and_logs_ack(self) -> None:
        session = self.connect()
        self.transport.feed_line(protocol.ack(0))

        self.assertTrue(session.stop())

        self.assertEqual(self.transport.sent_text()[-1], "X,0*44\n")
        self.assertEqual(self.find("stop_ack")[0]["sequence"], 0)

    def test_stop_timeout_is_logged(self) -> None:
        session = self.connect()

        self.assertFalse(session.stop(wait_ack_s=0.0))

        self.assertEqual(len(self.find("stop_ack_timeout")), 1)

    def test_stop_drains_status_backlog_before_ack(self) -> None:
        session = self.connect()
        for sequence in range(20):
            self.transport.feed_line(
                protocol.sensor_status(sequence, -1, 0, 0, 0, 0)
            )
        self.transport.feed_line(protocol.ack(0))

        self.assertTrue(session.stop())

        self.assertEqual(session.status_count, 20)
        self.assertEqual(len(self.find("stop_ack")), 1)

    def test_close_sends_stop_closes_transport_and_logs_end(self) -> None:
        session = self.connect()
        self.transport.feed_line(protocol.ack(0))

        session.close(reason="test_end")
        session.close(reason="second_close")

        self.assertTrue(self.transport.closed)
        self.assertEqual(self.transport.sent_text()[-1], "X,0*44\n")
        endings = self.find("session_end")
        self.assertEqual(len(endings), 1)
        self.assertEqual(endings[0]["reason"], "test_end")
        self.assertEqual(endings[0]["stop_ack"], True)

    def test_close_without_handshake_does_not_send_stop(self) -> None:
        session = self.make_session()

        session.close()

        self.assertTrue(self.transport.closed)
        self.assertEqual(self.transport.sent_text(), [])
        self.assertEqual(self.find("session_end")[0]["stop_ack"], None)

    def test_commands_require_handshake(self) -> None:
        session = self.make_session()

        with self.assertRaises(SessionError):
            session.step()
        with self.assertRaises(SessionError):
            session.stop()
        with self.assertRaises(SessionError):
            session.send_heartbeat()


if __name__ == "__main__":
    unittest.main()
