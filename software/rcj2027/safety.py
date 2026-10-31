"""Gate di sicurezza: il movimento resta spento finche' i dati minimi non sono completi."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any


class SafetyError(RuntimeError):
    """Il movimento e' stato richiesto senza i parametri di sicurezza."""

    def __init__(self, missing: list[str]) -> None:
        self.missing = missing
        super().__init__("movimento disabilitato: " + ", ".join(missing))


@dataclass(frozen=True)
class HardwareConfig:
    battery_nominal_v: float | None = None
    motor_side_map: Mapping[str, str] | None = None
    motor_direction_polarity: Mapping[str, str] | None = None
    pwm_max: int | None = None
    watchdog_timeout_s: float | None = None

    def missing_for_motion(self) -> list[str]:
        missing: list[str] = []

        if (
            isinstance(self.battery_nominal_v, bool)
            or not isinstance(self.battery_nominal_v, (int, float))
            or self.battery_nominal_v <= 0
        ):
            missing.append("battery_nominal_v")

        if not self._valid_side_map():
            missing.append("motor_side_map")

        if not self._valid_polarity():
            missing.append("motor_direction_polarity")

        if (
            isinstance(self.pwm_max, bool)
            or not isinstance(self.pwm_max, int)
            or not 1 <= self.pwm_max <= 255
        ):
            missing.append("pwm_max")

        if (
            isinstance(self.watchdog_timeout_s, bool)
            or not isinstance(self.watchdog_timeout_s, (int, float))
            or self.watchdog_timeout_s <= 0
        ):
            missing.append("watchdog_timeout_s")

        return missing

    @property
    def motion_enabled(self) -> bool:
        return not self.missing_for_motion()

    def require_motion(self) -> None:
        missing = self.missing_for_motion()
        if missing:
            raise SafetyError(missing)

    def _valid_side_map(self) -> bool:
        if not isinstance(self.motor_side_map, Mapping):
            return False
        if set(self.motor_side_map) != {"A", "B"}:
            return False
        values = {str(value).lower() for value in self.motor_side_map.values()}
        return values == {"left", "right"}

    def _valid_polarity(self) -> bool:
        if not isinstance(self.motor_direction_polarity, Mapping):
            return False
        if set(self.motor_direction_polarity) != {"A", "B"}:
            return False
        values = {str(value).lower() for value in self.motor_direction_polarity.values()}
        return values <= {"normal", "inverted"}

    def snapshot(self) -> dict[str, Any]:
        return {
            "battery_nominal_v": self.battery_nominal_v,
            "motor_side_map": dict(self.motor_side_map) if self.motor_side_map else None,
            "motor_direction_polarity": (
                dict(self.motor_direction_polarity)
                if self.motor_direction_polarity
                else None
            ),
            "pwm_max": self.pwm_max,
            "watchdog_timeout_s": self.watchdog_timeout_s,
            "motion_enabled": self.motion_enabled,
            "missing_for_motion": self.missing_for_motion(),
        }


# Dati verificati a banco. pwm_max e timeout watchdog restano da scegliere.
DEFAULT_CONFIG = HardwareConfig(
    battery_nominal_v=11.1,
    motor_side_map={"A": "right", "B": "left"},
    motor_direction_polarity={"A": "inverted", "B": "inverted"},
    pwm_max=None,
    watchdog_timeout_s=None,
)
