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
Infrastructure: ParSensorClient (Linux IIO ADC reader)
    |
    v
ADS1115 A0 input -> PAR-2.5V analog sensor
```

## Dependency direction

- `domain` knows nothing about FastAPI, I2C, ADC hardware, or Raspberry Pi.
- `application` depends only on the domain interface.
- `infrastructure` implements the domain interface using the Linux ADS1115 IIO files.
- `presentation` calls the application use case and exposes `/api/read` plus the one-page UI.
- `app/main.py` is the composition root that creates and connects the concrete objects.

## Request flow

1. The phone loads `/`.
2. Pressing **Read** sends `POST /api/read`.
3. The route invokes `ReadParSensorUseCase.execute()`.
4. `ParSensorClient` discovers the ADS1115, averages the configured number of A0 samples, and converts voltage to PAR.
5. The JSON response contains the PAR value and unit; the browser updates the page.

The ADC is read only when **Read** is pressed. This means the web page can still start and show an error cleanly if the ADC is not configured.
