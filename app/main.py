from app.application.read_par_sensor import ReadParSensorUseCase
from app.infrastructure.config import Settings
from app.infrastructure.par_sensor_client import ParSensorClient
from app.presentation.web import create_app


settings = Settings.from_env()
sensor_client = ParSensorClient(settings)
read_par_sensor = ReadParSensorUseCase(sensor_client)
app = create_app(read_par_sensor)
