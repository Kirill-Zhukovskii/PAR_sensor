from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class ParReading:
    value: int
    measured_at: datetime

    @property
    def unit(self) -> str:
        return "µmol/m²·s"
