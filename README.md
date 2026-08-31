# Raspberry Pi Analog PAR Sensor

A local web application for the Seeed PAR-2.5V analog sensor connected through
the Seeed 4-Channel 16-Bit ADS1115 ADC for Raspberry Pi.

Open the application at:

`http://par-sensor.local:8000`

The sensor is read only when **Read** is pressed.

## Sensor conversion

The PAR-2.5V datasheet specifies:

- Analog output: `0..2.5 V`
- PAR range: `0..2500 µmol/m²·s`
- Conversion: `PAR = voltage × 1000`
- Sensor supply: `5..24 V DC`

The application reads the voltage with the ADS1115, averages five samples by
default, applies the conversion, and clamps the result to `0..2500`.

## 1. Connect and configure the ADS1115

Mount the ADS1115 board on the Raspberry Pi. With power disconnected, connect:

- The sensor's analog output to ADS1115 **A0**.
- The sensor power-supply ground to ADS1115 **GND**.
- The sensor power wires to a suitable `5..24 V DC` supply according to its label.

Do not connect the sensor's 5-24 V supply line to an ADC input.

Enable I2C and ADS1115 channel A0 in single-ended mode. Add these lines to
`/boot/firmware/config.txt` (or `/boot/config.txt` on older Raspberry Pi OS):

```ini
dtparam=i2c_arm=on
dtoverlay=ads1115,cha_enable,cha_cfg=4,cha_gain=1
```

`cha_gain=1` selects a 4.096 V full-scale range, which can measure the sensor's
complete 0-2.5 V output. Reboot after changing the file:

```bash
sudo reboot
```

Verify that Linux created the ADC device and A0 input:

```bash
cat /sys/bus/iio/devices/iio:device*/name
ls /sys/bus/iio/devices/iio:device*/in_voltage0_raw
```

## 2. Configure the application

The default `.env` uses ADS1115 input A0:

```dotenv
ADC_IIO_DEVICE=auto
ADC_CHANNEL=0
ADC_SAMPLES=5
PAR_SENSOR_MAX_VOLTAGE=2.5
PAR_SENSOR_MAX_VALUE=2500
WEB_HOST=0.0.0.0
WEB_PORT=8000
DEVICE_HOSTNAME=par-sensor
```

`ADC_IIO_DEVICE=auto` finds the ADS1115 even when Linux assigns a device number
other than `iio:device0`.

## 3. Install and start automatically

For a complete first-time installation:

```bash
chmod +x scripts/*.sh
./scripts/install_on_pi.sh
```

If Python and the virtual environment are already installed, register only the
boot-time service:

```bash
bash scripts/enable_autostart.sh
```

Useful service commands:

```bash
sudo systemctl status par-sensor.service
sudo systemctl restart par-sensor.service
sudo systemctl stop par-sensor.service
journalctl -u par-sensor.service -f
```

## 4. Optional iPhone hotspot setup

Connect once and enable automatic reconnection:

```bash
nmcli device wifi connect "YOUR IPHONE HOTSPOT NAME" password "YOUR HOTSPOT PASSWORD"
nmcli connection modify "YOUR IPHONE HOTSPOT NAME" connection.autoconnect yes connection.autoconnect-priority 100
```

When the Pi and phone are connected, open `http://par-sensor.local:8000`.

## Read the ADC without the web application

Stop the service and inspect the kernel's direct ADC readings:

```bash
sudo systemctl stop par-sensor.service
cat /sys/bus/iio/devices/iio:device*/in_voltage0_raw
cat /sys/bus/iio/devices/iio:device*/in_voltage_scale
```

Run only the application's sensor client:

```bash
.venv/bin/python - <<'PY'
from app.infrastructure.config import Settings
from app.infrastructure.par_sensor_client import ParSensorClient

print(ParSensorClient(Settings.from_env()).read())
PY
```

Restart the service afterward:

```bash
sudo systemctl start par-sensor.service
```

## API

- `GET /` — mobile web interface.
- `POST /api/read` — takes an ADC reading and returns the converted PAR value.
- `GET /health` — checks the web service without reading the ADC.

Example response:

```json
{"ok":true,"value":1203,"unit":"µmol/m²·s","measured_at":"2026-08-31T09:00:00+00:00"}
```

## Tests

```bash
.venv/bin/python -m unittest discover -s tests -v
```

## Troubleshooting

### ADS1115 IIO device was not found

- Confirm the active `config.txt` contains the I2C and ADS1115 lines above.
- Reboot after changing `config.txt`.
- Run `cat /sys/bus/iio/devices/iio:device*/name`; it should include `ads1115`
  or `ads1015` (both names use the same Linux driver).

### Reading is always zero or incorrect

- Confirm the analog output is connected to A0.
- Confirm sensor ground, power-supply ground, and ADC ground are common.
- Measure the sensor output with a multimeter; it must remain between 0 and 2.5 V.
- Confirm `in_voltage0_raw` changes when the light level changes.

## Security scope

The application has no login because it is intended for a private Pi/phone
network. Anyone on the same network may be able to access it.
