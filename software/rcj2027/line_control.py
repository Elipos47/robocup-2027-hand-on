"""Controller line-following in dry-run (F0-5).

Il modulo trasforma lo stato del tracker in una proposta di comando differenziale.
Non apre la seriale e non invia nulla ai motori: serve a validare la legge di
controllo sui log reali prima di collegare l'Arduino.

Convenzioni:

- ``left`` e ``right`` sono i PWM logici delle ruote sinistra e destra;
- offset positivo (linea a destra) produce una correzione positiva: la ruota
  sinistra accelera e la destra rallenta, quindi il robot gira a destra;
- heading positivo (linea che piega a destra) produce la stessa correzione.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

from .line_vision import TrackState


class LineControlError(RuntimeError):
    """Configurazione o stato non validi."""


@dataclass(frozen=True)
class LineControlConfig:
    """Parametri provvisori del controller, da tarare sul campo."""

    pwm_max: int = 255
    cruise: int = 200
    k_offset: float = 0.35
    k_heading: float = 1.5
    max_correction: int = 80
    offset_deadband_px: float = 3.0
    heading_deadband_deg: float = 1.0

    def __post_init__(self) -> None:
        if isinstance(self.pwm_max, bool) or not isinstance(self.pwm_max, int):
            raise LineControlError("pwm_max deve essere intero")
        if not 1 <= self.pwm_max <= 255:
            raise LineControlError("pwm_max deve essere tra 1 e 255")
        if isinstance(self.cruise, bool) or not isinstance(self.cruise, int):
            raise LineControlError("cruise deve essere intero")
        if not 0 <= self.cruise <= self.pwm_max:
            raise LineControlError("cruise deve essere tra 0 e pwm_max")
        if not math.isfinite(self.k_offset) or self.k_offset < 0:
            raise LineControlError("k_offset deve essere finito e non negativo")
        if not math.isfinite(self.k_heading) or self.k_heading < 0:
            raise LineControlError("k_heading deve essere finito e non negativo")
        if isinstance(self.max_correction, bool) or not isinstance(
            self.max_correction, int
        ):
            raise LineControlError("max_correction deve essere intero")
        if not 0 <= self.max_correction <= self.pwm_max:
            raise LineControlError("max_correction deve essere tra 0 e pwm_max")
        if not math.isfinite(self.offset_deadband_px) or self.offset_deadband_px < 0:
            raise LineControlError("offset_deadband_px non valido")
        if (
            not math.isfinite(self.heading_deadband_deg)
            or self.heading_deadband_deg < 0
        ):
            raise LineControlError("heading_deadband_deg non valido")


@dataclass(frozen=True)
class DriveCommand:
    """Proposta di comando; non viene inviata da questo modulo."""

    left: int
    right: int
    state: str
    correction: float
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "left": self.left,
            "right": self.right,
            "state": self.state,
            "correction": round(self.correction, 2),
            "reason": self.reason,
        }


class LineController:
    """Legge offset/heading e produce PWM differenziali, senza motori."""

    def __init__(self, config: LineControlConfig | None = None) -> None:
        self.config = config or LineControlConfig()

    def _clamp_pwm(self, value: int) -> int:
        return max(0, min(self.config.pwm_max, value))

    def update(self, state: TrackState) -> DriveCommand:
        if not state.found:
            return DriveCommand(
                left=0,
                right=0,
                state="STOP",
                correction=0.0,
                reason="not_found",
            )
        if not state.confirmed:
            return DriveCommand(
                left=0,
                right=0,
                state="STOP",
                correction=0.0,
                reason="not_confirmed",
            )

        offset = (
            0.0
            if abs(state.offset_px) < self.config.offset_deadband_px
            else state.offset_px
        )
        heading = (
            0.0
            if abs(state.heading_deg) < self.config.heading_deadband_deg
            else state.heading_deg
        )
        correction = (
            self.config.k_offset * offset
            + self.config.k_heading * heading
        )
        correction = max(
            -self.config.max_correction,
            min(self.config.max_correction, correction),
        )
        left = self._clamp_pwm(int(round(self.config.cruise + correction)))
        right = self._clamp_pwm(int(round(self.config.cruise - correction)))
        return DriveCommand(
            left=left,
            right=right,
            state="FOLLOW",
            correction=correction,
            reason="ok",
        )
