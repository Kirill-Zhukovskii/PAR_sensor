from app.domain.models import ParReading
from app.domain.ports import ParSensorPort


class ReadParSensorUseCase:
    def __init__(self, sensor: ParSensorPort) -> None:
        self._sensor = sensor

    def execute(self) -> ParReading:
        return self._sensor.read()
