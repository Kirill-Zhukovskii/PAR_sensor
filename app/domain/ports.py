from typing import Protocol

from app.domain.models import ParReading


class ParSensorPort(Protocol):
    def read(self) -> ParReading:
        """Read one PAR measurement from the sensor."""
