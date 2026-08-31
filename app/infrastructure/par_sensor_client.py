from datetime import datetime, timezone
from pathlib import Path
from statistics import fmean
import threading

from app.domain.exceptions import SensorCommunicationError
from app.domain.models import ParReading
from app.infrastructure.config import Settings


DEFAULT_IIO_ROOT = Path("/sys/bus/iio/devices")
SUPPORTED_ADC_NAMES = {"ads1015", "ads1115"}


class ParSensorClient:
    """Read a 0-2.5 V PAR sensor through the Linux ADS1115 IIO driver."""

    def __init__(self, settings: Settings, iio_root: Path = DEFAULT_IIO_ROOT) -> None:
        self._settings = settings
        self._iio_root = iio_root
        self._lock = threading.Lock()

    def _find_adc_device(self) -> Path:
        configured = self._settings.adc_iio_device.strip()
        if configured.lower() != "auto":
            device = Path(configured)
            if not device.is_absolute():
                device = self._iio_root / configured
            if not device.is_dir():
                raise SensorCommunicationError(f"ADC IIO device does not exist: {device}")
            return device

        discovered: list[str] = []
        for device in sorted(self._iio_root.glob("iio:device*")):
            try:
                name = (device / "name").read_text(encoding="ascii").strip().lower()
            except OSError:
                continue
            discovered.append(f"{device.name} ({name})")
            if name in SUPPORTED_ADC_NAMES:
                return device

        found = ", ".join(discovered) if discovered else "none"
        raise SensorCommunicationError(
            "ADS1115 IIO device was not found under "
            f"{self._iio_root} (found: {found}). Enable I2C and the ads1115 overlay."
        )

    @staticmethod
    def _read_number(path: Path) -> float:
        return float(path.read_text(encoding="ascii").strip())

    def _read_voltage(self, device: Path) -> float:
        channel = self._settings.adc_channel
        raw_path = device / f"in_voltage{channel}_raw"
        scale_path = device / f"in_voltage{channel}_scale"
        if not scale_path.is_file():
            scale_path = device / "in_voltage_scale"

        if not raw_path.is_file():
            raise SensorCommunicationError(
                f"ADC channel A{channel} is unavailable ({raw_path}). "
                "Configure that ADS1115 channel in single-ended mode."
            )
        if not scale_path.is_file():
            raise SensorCommunicationError(f"ADC scale file is unavailable: {scale_path}")

        sample_count = self._settings.adc_samples
        if sample_count < 1:
            raise SensorCommunicationError("ADC_SAMPLES must be at least 1")

        raw_average = fmean(self._read_number(raw_path) for _ in range(sample_count))
        scale_mv = self._read_number(scale_path)

        offset_path = device / f"in_voltage{channel}_offset"
        if not offset_path.is_file():
            offset_path = device / "in_voltage_offset"
        offset = self._read_number(offset_path) if offset_path.is_file() else 0.0

        return (raw_average + offset) * scale_mv / 1000.0

    def read(self) -> ParReading:
        try:
            with self._lock:
                voltage = self._read_voltage(self._find_adc_device())
        except SensorCommunicationError:
            raise
        except (OSError, ValueError) as exc:
            raise SensorCommunicationError(
                f"Could not read the PAR sensor through the ADS1115: {exc}"
            ) from exc

        if self._settings.par_sensor_max_voltage <= 0:
            raise SensorCommunicationError("PAR_SENSOR_MAX_VOLTAGE must be greater than zero")
        if self._settings.par_sensor_max_value <= 0:
            raise SensorCommunicationError("PAR_SENSOR_MAX_VALUE must be greater than zero")

        value = round(
            voltage
            * self._settings.par_sensor_max_value
            / self._settings.par_sensor_max_voltage
        )
        value = max(0, min(value, self._settings.par_sensor_max_value))
        return ParReading(value=value, measured_at=datetime.now(timezone.utc))
