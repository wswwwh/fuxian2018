"""Physical and normalized constants used by the reproduction scripts."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CR3BPSystem:
    """Normalized circular restricted three-body system."""

    key: str
    name: str
    mu: float
    primary: str
    secondary: str
    length_unit_km: float | None = None
    time_unit_days: float | None = None


SYSTEMS: dict[str, CR3BPSystem] = {
    "earth_moon": CR3BPSystem(
        key="earth_moon",
        name="Earth-Moon",
        mu=0.012150585609624,
        primary="Earth",
        secondary="Moon",
        length_unit_km=384400.0,
        time_unit_days=4.342,
    ),
    "sun_earth": CR3BPSystem(
        key="sun_earth",
        name="Sun-Earth",
        mu=3.0035e-6,
        primary="Sun",
        secondary="Earth",
        length_unit_km=149597870.7,
        time_unit_days=58.132,
    ),
    "saturn_titan": CR3BPSystem(
        key="saturn_titan",
        name="Saturn-Titan",
        mu=0.0002366,
        primary="Saturn",
        secondary="Titan",
    ),
    "jupiter_europa": CR3BPSystem(
        key="jupiter_europa",
        name="Jupiter-Europa",
        mu=2.528e-5,
        primary="Jupiter",
        secondary="Europa",
    ),
}
