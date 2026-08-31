# Raspberry Pi PAR Sensor

A minimal local IoT service for the Seeed S-PAR-02 RS485 PAR sensor. The Raspberry Pi joins your iPhone Personal Hotspot automatically, serves one small local web page, and reads the sensor only when you press **Read**.

The stable address is a Bonjour/mDNS hostname rather than a fixed DHCP number:

`http://par-sensor.local:8000`

The Pi's numeric IP may be assigned by the iPhone, but the `.local` name stays the same.

## What the supplied sensor datasheet says

For the RS485 S-PAR-02 model:

- Output: Modbus-RTU over RS485.
- Serial settings: 9600 baud, 8 data bits, no parity, 1 stop bit.
- The datasheet query example uses slave address `1`; this project uses `1` as its initial setting. If your sensor was re-addressed, change `.env`.
- Read command: function `0x03`, start register `0x0000`, quantity `1`.
- The returned 16-bit register is the PAR value directly in `µmol/m²·s`. The datasheet example `0x04B3` is `1203 µmol/m²·s`.
- Measurement range: `0..2500 µmol/m²·s`, resolution `1 µmol/m²·s`.

The page-1 wiring diagram for the RS485 model shows:

- Red -> VIN (5-24 V DC)
- Yellow -> RS485 A
- White -> RS485 B
- Black -> GND

Use a USB-to-RS485 adapter between the Pi and the A/B pair. Wire the sensor with power disconnected. Check your adapter labels because some manufacturers label A/B or +/- differently.

## Project structure

```text
app/
  domain/           # entities, port/interface, domain exception
  application/      # read-sensor use case
  infrastructure/   # .env configuration + par_sensor_client.py
  presentation/     # FastAPI backend + HTML/JS UI
  main.py            # composition root
scripts/
  start.sh
  install_on_pi.sh   # venv + packages + mDNS hostname + systemd autostart
  uninstall_service.sh
tests/
docs/ARCHITECTURE.md
.env
requirements.txt
```

## 1. Prepare the Raspberry Pi

Use Raspberry Pi OS Lite or Desktop. Connect the USB-to-RS485 adapter; it will commonly appear as `/dev/ttyUSB0` or `/dev/ttyACM0`.

Check it with:

```bash
ls -l /dev/ttyUSB* /dev/ttyACM* 2>/dev/null
```

Edit `.env` if necessary:

```dotenv
SERIAL_PORT=/dev/ttyUSB0
MODBUS_SLAVE_ADDRESS=1
MODBUS_BAUDRATE=9600
MODBUS_TIMEOUT_SECONDS=1.0
WEB_HOST=0.0.0.0
WEB_PORT=8000
DEVICE_HOSTNAME=par-sensor
```

If you have previously changed the sensor's Modbus slave address, set `MODBUS_SLAVE_ADDRESS` to that value.

## 2. Make the Pi automatically join your iPhone hotspot

Turn on **Personal Hotspot** on the iPhone. On the Pi, connect once using NetworkManager:

```bash
nmcli device wifi connect "YOUR IPHONE HOTSPOT NAME" password "YOUR HOTSPOT PASSWORD"
```

Then make sure that saved connection is allowed to autoconnect:

```bash
nmcli connection show
nmcli connection modify "YOUR IPHONE HOTSPOT NAME" connection.autoconnect yes connection.autoconnect-priority 100
```

After this, when your hotspot is available the Pi should reconnect to it automatically. If an older Pi cannot see the iPhone hotspot, enabling **Maximize Compatibility** on the iPhone can help because it makes the hotspot friendlier to 2.4 GHz-only clients.

## 3. Install the service

From the project directory:

```bash
chmod +x scripts/*.sh
./scripts/install_on_pi.sh
```

The installer:

1. installs Python venv support and Avahi/mDNS;
2. creates `.venv`;
3. installs `requirements.txt`;
4. adds your Pi user to the `dialout` group for serial-port access;
5. sets the hostname from `DEVICE_HOSTNAME`;
6. installs and enables a `systemd` service;
7. starts the web server immediately.

A reboot after the first installation is recommended so the hostname and serial group membership are unquestionably active:

```bash
sudo reboot
```

If Python, the virtual environment, dependencies, and serial permissions are
already set up, enable boot-time startup without reinstalling anything:

```bash
bash scripts/enable_autostart.sh
```

Run that command once. It starts the application immediately and registers it
to start automatically after every reboot.

## 4. Use it from the iPhone

1. Turn on iPhone Personal Hotspot.
2. Power the Raspberry Pi.
3. Wait for the Pi to join the hotspot.
4. Open Safari and visit `http://par-sensor.local:8000`.
5. Press **Read**.

The browser sends `POST /api/read`; the Pi performs exactly one Modbus read and displays the returned PAR value.

You can bookmark the URL or add it to the iPhone Home Screen.

## Backend/API

`GET /` - mobile UI.

`POST /api/read` - triggers one physical sensor read. Example response:

```json
{"ok":true,"value":1203,"unit":"µmol/m²·s","measured_at":"2026-08-31T09:00:00+00:00"}
```

`GET /health` - verifies that the web service is running; it does not touch the sensor.

## Service commands

```bash
sudo systemctl status par-sensor.service
sudo systemctl restart par-sensor.service
journalctl -u par-sensor.service -f
```

The service starts automatically at boot. It does not need the iPhone hotspot to exist at boot time: the server listens locally and becomes reachable as soon as Wi-Fi connects later.

## Manual development run

After dependencies have been installed:

```bash
./scripts/start.sh
```

Then open `http://<pi-ip>:8000` or `http://par-sensor.local:8000`.

## Tests

The application layer can be tested without sensor hardware:

```bash
.venv/bin/python -m unittest discover -s tests -v
```

## Troubleshooting

### UI loads, but Read reports permission denied

Check the serial device and groups:

```bash
ls -l /dev/ttyUSB0
id
```

The running user should be in `dialout`. Reboot once after `install_on_pi.sh` if needed.

### No response / CRC / timeout

Check:

- A/B wiring (and try swapping A/B only if your adapter's labels use the opposite convention).
- Sensor power is within the datasheet's 5-24 V DC range.
- `.env` uses the correct serial device.
- `MODBUS_SLAVE_ADDRESS` matches the sensor.
- Baud rate is 9600.
- Only the intended sensor is attached while debugging.

### `par-sensor.local` does not resolve

Confirm Avahi and the hostname:

```bash
systemctl status avahi-daemon
hostname
```

The installer sets the hostname to `DEVICE_HOSTNAME`. A reboot after changing it is the simplest fix. As a temporary diagnostic, `hostname -I` shows the current numeric IP.

### Why not force a static iPhone-hotspot IP?

The iPhone controls its tethering subnet and DHCP allocation. A manually chosen numeric address can collide or stop working if iOS changes network details. mDNS gives the device a stable human-readable address while still allowing DHCP to do its job.

## Security scope

This project intentionally has no login because it is designed for your own Pi and phone on your Personal Hotspot. Anyone who is allowed onto that same hotspot may be able to reach the page, so keep the hotspot password private.
