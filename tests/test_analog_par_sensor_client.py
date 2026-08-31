import tempfile
import unittest
from pathlib import Path

from app.domain.exceptions import SensorCommunicationError
from app.infrastructure.config import Settings
from app.infrastructure.par_sensor_client import ParSensorClient


def make_settings(**overrides) -> Settings:
    values = {
        "adc_iio_device": "auto",
        "adc_channel": 0,
        "adc_samples": 5,
        "par_sensor_max_voltage": 2.5,
        "par_sensor_max_value": 2500,
        "web_host": "0.0.0.0",
        "web_port": 8000,
        "device_hostname": "par-sensor",
    }
    values.update(overrides)
    return Settings(**values)


class AnalogParSensorClientTest(unittest.TestCase):
    def create_adc(self, root: Path, raw: str, scale: str = "0.125") -> Path:
        device = root / "adc"
        device.mkdir()
        (device / "name").write_text("ads1115\n", encoding="ascii")
        (device / "in_voltage0_raw").write_text(raw, encoding="ascii")
        (device / "in_voltage_scale").write_text(scale, encoding="ascii")
        return device

    def test_converts_1_25_volts_to_1250_par(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.create_adc(root, raw="10000\n")

            settings = make_settings(adc_iio_device=str(root / "adc"))
            reading = ParSensorClient(settings, iio_root=root).read()

            self.assertEqual(reading.value, 1250)

    def test_clamps_voltage_above_sensor_range(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.create_adc(root, raw="24000\n")  # 3.0 V

            settings = make_settings(adc_iio_device=str(root / "adc"))
            reading = ParSensorClient(settings, iio_root=root).read()

            self.assertEqual(reading.value, 2500)

    def test_reports_missing_ads1115(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(SensorCommunicationError, "ADS1115 IIO device"):
                ParSensorClient(make_settings(), iio_root=Path(directory)).read()


if __name__ == "__main__":
    unittest.main()
