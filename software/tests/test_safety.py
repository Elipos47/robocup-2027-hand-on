from __future__ import annotations

import unittest

from rcj2027.safety import (
    DEFAULT_CONFIG,
    OPERATIONAL_CONFIG,
    HardwareConfig,
    SafetyError,
)


class SafetyTests(unittest.TestCase):
    def test_empty_config_disables_motion(self) -> None:
        config = HardwareConfig()
        self.assertFalse(config.motion_enabled)
        self.assertEqual(len(config.missing_for_motion()), 5)

    def test_default_config_still_needs_pwm_and_watchdog(self) -> None:
        self.assertFalse(DEFAULT_CONFIG.motion_enabled)
        self.assertEqual(
            DEFAULT_CONFIG.missing_for_motion(),
            ["pwm_max", "watchdog_timeout_s"],
        )
        self.assertEqual(DEFAULT_CONFIG.motor_side_map, {"A": "right", "B": "left"})
        self.assertEqual(
            DEFAULT_CONFIG.motor_direction_polarity,
            {"A": "inverted", "B": "inverted"},
        )

    def test_operational_config_uses_selected_values(self) -> None:
        self.assertTrue(OPERATIONAL_CONFIG.motion_enabled)
        self.assertEqual(OPERATIONAL_CONFIG.pwm_max, 255)
        self.assertEqual(OPERATIONAL_CONFIG.watchdog_timeout_s, 1.0)
        self.assertEqual(OPERATIONAL_CONFIG.missing_for_motion(), [])
        OPERATIONAL_CONFIG.require_motion()

    def test_complete_config_enables_motion(self) -> None:
        config = HardwareConfig(
            battery_nominal_v=11.1,
            motor_side_map={"A": "right", "B": "left"},
            motor_direction_polarity={"A": "inverted", "B": "inverted"},
            pwm_max=200,
            watchdog_timeout_s=0.5,
        )
        self.assertTrue(config.motion_enabled)
        self.assertEqual(config.missing_for_motion(), [])
        config.require_motion()

    def test_invalid_side_map(self) -> None:
        config = HardwareConfig(
            battery_nominal_v=11.1,
            motor_side_map={"A": "right", "B": "right"},
            motor_direction_polarity={"A": "normal", "B": "normal"},
            pwm_max=200,
            watchdog_timeout_s=0.5,
        )
        self.assertIn("motor_side_map", config.missing_for_motion())

    def test_invalid_polarity(self) -> None:
        config = HardwareConfig(
            battery_nominal_v=11.1,
            motor_side_map={"A": "right", "B": "left"},
            motor_direction_polarity={"A": "normal", "B": "boh"},
            pwm_max=200,
            watchdog_timeout_s=0.5,
        )
        self.assertIn("motor_direction_polarity", config.missing_for_motion())

    def test_pwm_range(self) -> None:
        for value in (0, 256):
            config = HardwareConfig(
                battery_nominal_v=11.1,
                motor_side_map={"A": "right", "B": "left"},
                motor_direction_polarity={"A": "normal", "B": "normal"},
                pwm_max=value,
                watchdog_timeout_s=0.5,
            )
            self.assertIn("pwm_max", config.missing_for_motion())

    def test_watchdog_range(self) -> None:
        config = HardwareConfig(
            battery_nominal_v=11.1,
            motor_side_map={"A": "right", "B": "left"},
            motor_direction_polarity={"A": "normal", "B": "normal"},
            pwm_max=200,
            watchdog_timeout_s=0,
        )
        self.assertIn("watchdog_timeout_s", config.missing_for_motion())

    def test_require_motion_raises(self) -> None:
        with self.assertRaises(SafetyError) as ctx:
            DEFAULT_CONFIG.require_motion()
        self.assertEqual(ctx.exception.missing, ["pwm_max", "watchdog_timeout_s"])

    def test_snapshot(self) -> None:
        snapshot = DEFAULT_CONFIG.snapshot()
        self.assertEqual(snapshot["battery_nominal_v"], 11.1)
        self.assertFalse(snapshot["motion_enabled"])
        self.assertIn("pwm_max", snapshot["missing_for_motion"])


if __name__ == "__main__":
    unittest.main()
