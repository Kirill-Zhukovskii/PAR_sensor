from dataclasses import dataclass
import os
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True, slots=True)
class Settings:
    adc_iio_device: str
    adc_channel: int
    adc_samples: int
    par_sensor_max_voltage: float
    par_sensor_max_value: int
    web_host: str
    web_port: int
    device_hostname: str

    @classmethod
    def from_env(cls) -> "Settings":
        load_dotenv(PROJECT_ROOT / ".env")
        return cls(
            adc_iio_device=os.getenv("ADC_IIO_DEVICE", "auto"),
            adc_channel=int(os.getenv("ADC_CHANNEL", "0")),
            adc_samples=int(os.getenv("ADC_SAMPLES", "5")),
            par_sensor_max_voltage=float(os.getenv("PAR_SENSOR_MAX_VOLTAGE", "2.5")),
            par_sensor_max_value=int(os.getenv("PAR_SENSOR_MAX_VALUE", "2500")),
            web_host=os.getenv("WEB_HOST", "0.0.0.0"),
            web_port=int(os.getenv("WEB_PORT", "8000")),
            device_hostname=os.getenv("DEVICE_HOSTNAME", "par-sensor"),
        )
