# Architecture

The project follows a small Clean Architecture split so the sensor transport and the web UI can change independently.

```text
Phone browser
    |
    | HTTP
    v
Presentation: FastAPI + HTML/JS
    |
    v
Application: ReadParSensorUseCase
    |
    v
Domain: ParSensorPort + ParReading
    ^
    |
Infrastructure: ParSensorClient (Modbus RTU over /dev/ttyUSB0)
    |
    v
USB-to-RS485 adapter -> S-PAR-02
```

## Dependency direction

- `domain` knows nothing about FastAPI, serial ports, Modbus, or Raspberry Pi.
- `application` depends only on the domain interface.
- `infrastructure` implements the domain interface using MinimalModbus/PySerial.
- `presentation` calls the application use case and exposes `/api/read` plus the one-page UI.
- `app/main.py` is the composition root that creates and connects the concrete objects.

## Request flow

1. The phone loads `/`.
2. Pressing **Read** sends `POST /api/read`.
3. The route invokes `ReadParSensorUseCase.execute()`.
4. `ParSensorClient` opens the configured serial device and performs one Modbus holding-register read.
5. The JSON response contains the PAR value and unit; the browser updates the page.

The serial port is opened lazily only when **Read** is pressed. This means the web page can still start and show an error cleanly if the sensor or USB adapter is temporarily unplugged.
