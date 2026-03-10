"""FastAPI application entry point.

Configures CORS, logging, error handlers, lifespan events,
and includes all API routers under /api/v1 prefix.
"""

import asyncio
import logging
import time
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone

from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.config import settings

logger = logging.getLogger("greenhouse")


def setup_logging():
    """Configure structured JSON logging for the application."""
    from pythonjsonlogger.json import JsonFormatter

    handler = logging.StreamHandler()
    formatter = JsonFormatter(
        fmt="%(asctime)s %(name)s %(levelname)s %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )
    handler.setFormatter(formatter)

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(logging.INFO)


setup_logging()


def _seed_reference_data():
    """Insert seed data for sensor types and actuator types if not present."""
    from app.database import SessionLocal
    from app.models import ActuatorType, SensorType

    try:
        db = SessionLocal()
        try:
            if db.query(SensorType).count() == 0:
                for name in ["temperature", "humidity", "light"]:
                    db.add(SensorType(name=name))
                db.commit()
                logger.info("Seeded sensor types")
            if db.query(ActuatorType).count() == 0:
                for name in ["lighting", "heating", "ventilation", "watering"]:
                    db.add(ActuatorType(name=name))
                db.commit()
                logger.info("Seeded actuator types")
        finally:
            db.close()
    except Exception as e:
        logger.warning("Seed data skipped (DB not available): %s", e)


async def _device_status_checker():
    """Periodic task to mark devices as offline if last_seen > 60s ago.

    Runs every 60 seconds (Constitution VIII).
    """
    from app.database import SessionLocal
    from app.models import Device, DeviceStatus

    while True:
        await asyncio.sleep(60)
        db = SessionLocal()
        try:
            threshold = datetime.now(timezone.utc) - timedelta(seconds=60)
            stale = (
                db.query(Device)
                .filter(Device.status == DeviceStatus.online, Device.last_seen < threshold)
                .all()
            )
            for device in stale:
                device.status = DeviceStatus.offline
                logger.info("Device %s marked offline (last_seen stale)", device.id)
            if stale:
                db.commit()
        except Exception as e:
            logger.error("Device status check failed: %s", e)
        finally:
            db.close()


async def _data_retention_cleanup():
    """Daily cleanup of old sensor readings and actuator commands.

    Constitution IV: raw readings > 7 days, commands > 30 days.
    """
    from app.database import SessionLocal
    from app.models import ActuatorCommand, SensorReading

    while True:
        await asyncio.sleep(86400)  # 24 hours
        db = SessionLocal()
        try:
            readings_cutoff = datetime.now(timezone.utc) - timedelta(days=7)
            deleted_readings = (
                db.query(SensorReading)
                .filter(SensorReading.recorded_at < readings_cutoff)
                .delete()
            )
            commands_cutoff = datetime.now(timezone.utc) - timedelta(days=30)
            deleted_commands = (
                db.query(ActuatorCommand)
                .filter(ActuatorCommand.created_at < commands_cutoff)
                .delete()
            )
            db.commit()
            logger.info("Retention cleanup: %d readings, %d commands deleted", deleted_readings, deleted_commands)
        except Exception as e:
            logger.error("Retention cleanup failed: %s", e)
        finally:
            db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: seed data, MQTT client, background tasks.

    Args:
        app: FastAPI application instance.
    """
    from app.mqtt.client import mqtt_client

    _seed_reference_data()

    mqtt_client.connect()
    logger.info("MQTT client connected")

    status_task = asyncio.create_task(_device_status_checker())
    retention_task = asyncio.create_task(_data_retention_cleanup())

    yield

    status_task.cancel()
    retention_task.cancel()
    mqtt_client.disconnect()
    logger.info("MQTT client disconnected")


app = FastAPI(
    title="Smart Greenhouse API",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log every HTTP request with method, path, status, and duration.

    Args:
        request: Incoming request.
        call_next: Next middleware/handler.

    Returns:
        Response from the handler.
    """
    start = time.time()
    response = await call_next(request)
    duration_ms = (time.time() - start) * 1000
    logger.info(
        "request",
        extra={
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration_ms": round(duration_ms, 2),
        },
    )
    return response


# Error handlers
def _error_response(status_code: int, code: str, message: str) -> JSONResponse:
    """Build a standardized error response.

    Args:
        status_code: HTTP status code.
        code: Application error code.
        message: Human-readable error message.

    Returns:
        JSONResponse with error body.
    """
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": code,
                "message": message,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError):
    """Handle Pydantic validation errors with 422 response.

    Args:
        request: Incoming request.
        exc: Validation error.

    Returns:
        Standardized 422 error response.
    """
    return _error_response(422, "VALIDATION_ERROR", str(exc.errors()))


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Handle HTTP exceptions with standardized error format.

    Args:
        request: Incoming request.
        exc: HTTP exception.

    Returns:
        Standardized error response.
    """
    code_map = {
        401: "INVALID_CREDENTIALS",
        403: "FORBIDDEN",
        404: "NOT_FOUND",
        409: "CONFLICT",
        500: "INTERNAL_ERROR",
        503: "SERVICE_UNAVAILABLE",
    }
    code = code_map.get(exc.status_code, "ERROR")
    message = exc.detail if isinstance(exc.detail, str) else str(exc.detail)
    return _error_response(exc.status_code, code, message)


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions with 500 response.

    Args:
        request: Incoming request.
        exc: Unexpected exception.

    Returns:
        Standardized 500 error response.
    """
    logger.error("Unhandled exception", exc_info=exc)
    return _error_response(500, "INTERNAL_ERROR", "Internal server error")


# Include routers
from app.routes.actuators import router as actuators_router  # noqa: E402
from app.routes.auth import router as auth_router  # noqa: E402
from app.routes.dashboard import router as dashboard_router  # noqa: E402
from app.routes.devices import router as devices_router  # noqa: E402
from app.routes.greenhouses import router as greenhouses_router  # noqa: E402
from app.routes.health import router as health_router  # noqa: E402
from app.routes.scripts import router as scripts_router  # noqa: E402
from app.routes.sensors import router as sensors_router  # noqa: E402
from app.routes.simulator import router as simulator_router  # noqa: E402
from app.websocket import ws_manager  # noqa: E402

app.include_router(health_router, prefix="/api/v1")
app.include_router(auth_router, prefix="/api/v1")
app.include_router(greenhouses_router, prefix="/api/v1")
app.include_router(devices_router, prefix="/api/v1")
app.include_router(sensors_router, prefix="/api/v1")
app.include_router(actuators_router, prefix="/api/v1")
app.include_router(scripts_router, prefix="/api/v1")
app.include_router(dashboard_router, prefix="/api/v1")
app.include_router(simulator_router, prefix="/api/v1")


@app.websocket("/ws/greenhouse/{greenhouse_id}")
async def websocket_endpoint(websocket: WebSocket, greenhouse_id: int):
    """WebSocket endpoint for real-time greenhouse updates.

    Client must send auth token as first message:
    {"token": "<jwt_access_token>"}

    Then receives events: sensor_update, actuator_update, device_status.

    Args:
        websocket: WebSocket connection.
        greenhouse_id: Greenhouse to subscribe to.
    """
    authenticated = await ws_manager.connect(websocket, greenhouse_id)
    if not authenticated:
        return

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket, greenhouse_id)
