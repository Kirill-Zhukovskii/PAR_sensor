from datetime import datetime, timezone
import threading

import minimalmodbus
import serial

from app.domain.exceptions import SensorCommunicationError
from app.domain.models import ParReading
from app.infrastructure.config import Settings


PAR_REGISTER_ADDRESS = 0
PAR_FUNCTION_CODE = 3


class ParSensorClient:
    """Modbus-RTU client for the S-PAR-02 PAR sensor.

    Datasheet protocol used here:
    - RTU, 9600 baud, 8 data bits, no parity, 1 stop bit
    - Holding-register read (function 0x03)
    - Start register 0x0000, quantity 1
    - Register value is the PAR value in µmol/m²·s
    """

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._lock = threading.Lock()

    def _build_instrument(self) -> minimalmodbus.Instrument:
        instrument = minimalmodbus.Instrument(
            self._settings.serial_port,
            self._settings.modbus_slave_address,
            mode=minimalmodbus.MODE_RTU,
        )
        instrument.serial.baudrate = self._settings.modbus_baudrate
        instrument.serial.bytesize = 8
        instrument.serial.parity = serial.PARITY_NONE
        instrument.serial.stopbits = 1
        instrument.serial.timeout = self._settings.modbus_timeout_seconds
        instrument.clear_buffers_before_each_transaction = True
        instrument.close_port_after_each_call = True
        return instrument

    def read(self) -> ParReading:
        try:
            with self._lock:
                instrument = self._build_instrument()
                raw_value = instrument.read_register(
                    registeraddress=PAR_REGISTER_ADDRESS,
                    number_of_decimals=0,
                    functioncode=PAR_FUNCTION_CODE,
                    signed=False,
                )
        except (OSError, ValueError, minimalmodbus.ModbusException, serial.SerialException) as exc:
            raise SensorCommunicationError(
                f"Could not read PAR sensor on {self._settings.serial_port}: {exc}"
            ) from exc

        return ParReading(value=int(raw_value), measured_at=datetime.now(timezone.utc))
