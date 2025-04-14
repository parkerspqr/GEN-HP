from dataclasses import dataclass
from typing import Dict, Optional
from pathlib import Path


@dataclass
class Region:
    left: int
    top: int
    width: int
    height: int

    def validate(self) -> bool:
        return all(isinstance(v, int) and v >= 0 for v in [self.left, self.top, self.width, self.height])


@dataclass
class Settings:
    hp_threshold: float = 90.0
    check_interval_stable: float = 0.2
    check_interval_healing: float = 0.1
    check_interval_idle: float = 0.1
    slot_delays: Dict[int, float] = None

    def __post_init__(self):
        if self.slot_delays is None:
            self.slot_delays = {5: 1.0, 6: 1.0}
        self.validate()

    def validate(self) -> bool:
        if not (0 <= self.hp_threshold <= 150):
            raise ValueError("hp_threshold must be between 0 and 150")
        if not all(x > 0 for x in [self.check_interval_stable, self.check_interval_healing, self.check_interval_idle]):
            raise ValueError("Intervals must be positive")
        if not all(slot in [5, 6] and delay > 0 for slot, delay in self.slot_delays.items()):
            raise ValueError("Invalid slot or delay")
        return True


@dataclass
class Config:
    settings: Settings
    regions: Dict[str, Region]
    base_path: Path

    def validate(self) -> bool:
        return (
            self.settings.validate()
            and all(region.validate() for region in self.regions.values())
            and all(key in ["hp", "slot_5", "slot_6"] for key in self.regions)
        )