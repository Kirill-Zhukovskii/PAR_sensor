from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.application.read_par_sensor import ReadParSensorUseCase
from app.domain.exceptions import SensorCommunicationError


BASE_DIR = Path(__file__).resolve().parent


def create_app(read_par_sensor: ReadParSensorUseCase) -> FastAPI:
    app = FastAPI(title="PAR Sensor", docs_url=None, redoc_url=None, openapi_url=None)
    templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
    app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

    @app.get("/", response_class=HTMLResponse)
    def index(request: Request):
        return templates.TemplateResponse(request=request, name="index.html")

    @app.post("/api/read")
    def read_sensor():
        try:
            reading = read_par_sensor.execute()
        except SensorCommunicationError as exc:
            return JSONResponse(status_code=503, content={"ok": False, "error": str(exc)})

        return {
            "ok": True,
            "value": reading.value,
            "unit": reading.unit,
            "measured_at": reading.measured_at.isoformat(),
        }

    @app.get("/health")
    def health():
        return {"status": "ok"}

    return app
