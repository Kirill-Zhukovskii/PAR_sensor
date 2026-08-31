import unittest
from datetime import datetime, timezone

from app.application.read_par_sensor import ReadParSensorUseCase
from app.domain.models import ParReading


class FakeParSensor:
    def read(self) -> ParReading:
        return ParReading(value=1203, measured_at=datetime.now(timezone.utc))


class ReadParSensorUseCaseTest(unittest.TestCase):
    def test_returns_sensor_reading(self):
        use_case = ReadParSensorUseCase(FakeParSensor())
        reading = use_case.execute()
        self.assertEqual(reading.value, 1203)
        self.assertEqual(reading.unit, "µmol/m²·s")


if __name__ == "__main__":
    unittest.main()
