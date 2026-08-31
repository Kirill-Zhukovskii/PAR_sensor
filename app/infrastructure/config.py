from dataclasses import dataclass
import os
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True, slots=True)
class Settings:
    serial_port: str
    modbus_slave_address: int
    modbus_baudrate: int
    modbus_timeout_seconds: float
    web_host: str
    web_port: int
    device_hostname: str

    @classmethod
    def from_env(cls) -> "Settings":
        load_dotenv(PROJECT_ROOT / ".env")
        return cls(
            serial_port=os.getenv("SERIAL_PORT", "/dev/ttyUSB0"),
            modbus_slave_address=int(os.getenv("MODBUS_SLAVE_ADDRESS", "1")),
            modbus_baudrate=int(os.getenv("MODBUS_BAUDRATE", "9600")),
            modbus_timeout_seconds=float(os.getenv("MODBUS_TIMEOUT_SECONDS", "1.0")),
            web_host=os.getenv("WEB_HOST", "0.0.0.0"),
            web_port=int(os.getenv("WEB_PORT", "8000")),
            device_hostname=os.getenv("DEVICE_HOSTNAME", "par-sensor"),
        )
