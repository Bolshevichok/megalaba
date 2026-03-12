"""Routes for health."""

import time
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database import get_db
from app.mqtt.client import mqtt_client
from app.schemas import HealthDBResponse, HealthMQTTResponse, HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health_check(db: Session = Depends(get_db)) -> HealthResponse:
    """Return overall health status of the application.

    Checks database connectivity by running a simple query and
    checks MQTT broker connection status.

    Args:
        db: Database session injected by FastAPI dependency.

    Returns:
        HealthResponse with db, mqtt, and timestamp fields.
    """
    db_status = "available"
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        db_status = "unavailable"

    mqtt_status = "connected" if mqtt_client.connected else "disconnected"

    return HealthResponse(
        status="ok",
        db=db_status,
        mqtt=mqtt_status,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


@router.get("/health/db", response_model=HealthDBResponse)
def health_db(db: Session = Depends(get_db)) -> HealthDBResponse:
    """Check database availability and measure query latency.

    Executes a ``SELECT 1`` query and records the round-trip time
    in milliseconds.

    Args:
        db: Database session injected by FastAPI dependency.

    Returns:
        HealthDBResponse with status and latency_ms fields.
    """
    try:
        start = time.perf_counter()
        db.execute(text("SELECT 1"))
        latency_ms = (time.perf_counter() - start) * 1000
        return HealthDBResponse(status="available", latency_ms=latency_ms)
    except Exception:
        return HealthDBResponse(status="unavailable", latency_ms=0.0)


@router.get("/health/mqtt", response_model=HealthMQTTResponse)
def health_mqtt() -> HealthMQTTResponse:
    """Check MQTT broker connection status.

    Returns:
        HealthMQTTResponse with status and connected fields.
    """
    connected = mqtt_client.connected
    status = "connected" if connected else "disconnected"
    return HealthMQTTResponse(status=status, connected=connected)
