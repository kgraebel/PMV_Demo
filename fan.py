"""Typical local air speed produced by a fan at low/medium/high settings.

These are reference air speeds felt by an occupant sitting a normal
working distance from a fan -- not the fan's own blade-tip/outlet speed,
which is much higher. Actual air speed varies with fan size, distance,
and model, so treat these as reasonable middle-of-range starting points
for each setting rather than a measured reading.
"""

from dataclasses import dataclass
from typing import List, Tuple


@dataclass
class FanSpeedPreset:
    label: str
    air_speed_ms: float


class FanAirSpeed:
    """Vends low/medium/high fan-speed air speed presets, in m/s."""

    SETTINGS: List[FanSpeedPreset] = [
        FanSpeedPreset("Fan Low", 0.3),
        FanSpeedPreset("Fan Medium", 0.8),
        FanSpeedPreset("Fan High", 1.5),
    ]

    @classmethod
    def presets(cls) -> List[Tuple[str, float]]:
        """[(label, air_speed_m_s), ...] for the three fan settings."""
        return [(p.label, p.air_speed_ms) for p in cls.SETTINGS]

    @classmethod
    def speed_for(cls, setting: str) -> float:
        for p in cls.SETTINGS:
            if p.label == setting:
                return p.air_speed_ms
        valid = [p.label for p in cls.SETTINGS]
        raise ValueError(f"setting must be one of {valid}, got {setting!r}")


# Module-level export so callers can `from fan import FAN_SPEED_PRESETS`
# the same way pmv.py exposes MET_PRESETS / CLO_PRESETS.
FAN_SPEED_PRESETS = FanAirSpeed.presets()
