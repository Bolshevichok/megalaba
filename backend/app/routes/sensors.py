"""Routes for sensors."""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.dependencies import get_current_user
from app.models import Device, Greenhouse, Sensor, SensorReading, User
from app.schemas import (
    SensorReadingCreate,
    SensorReadingResponse,
    SensorReadingsHistoryResponse,
    SensorResponse,
    SensorStatistics,
)

router = APIRouter(tags=["sensors"])


@router.get(
    "/greenhouses/{greenhouse_id}/devices/{device_id}/sensors",
    response_model=dict,
)
def list_sensors(
    greenhouse_id: int,
    device_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """List all sensors belonging to a device.

    Verifies that the greenhouse belongs to the current user and that
    the device belongs to the specified greenhouse.

    Args:
        greenhouse_id: ID of the greenhouse.
        device_id: ID of the device.
        db: Database session.
        current_user: Authenticated user.

    Returns:
        Dictionary with a ``sensors`` key containing a list of sensors.

    Raises:
        HTTPException: 404 if greenhouse or device not found, or ownership
            check fails.
    """
    greenhouse = (
        db.query(Greenhouse)
        .filter(Greenhouse.id == greenhouse_id, Greenhouse.user_id == current_user.id)
        .first()
    )
    if not greenhouse:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Greenhouse not found",
        )

    device = (
        db.query(Device)
        .filter(Device.id == device_id, Device.greenhouse_id == greenhouse_id)
        .first()
    )
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found",
        )

    sensors = db.query(Sensor).filter(Sensor.device_id == device_id).all()

    return {"sensors": [SensorResponse.model_validate(s) for s in sensors]}


@router.get(
    "/sensors/{sensor_id}/readings",
    response_model=SensorReadingsHistoryResponse,
)
def get_sensor_readings(
    sensor_id: int,
    start_time: datetime | None = None,
    end_time: datetime | None = None,
    limit: int = Query(100, le=1000),
    aggregation: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SensorReadingsHistoryResponse:
    """Get historical readings for a sensor with statistics.

    Supports optional time-range filtering and a result limit. Returns
    aggregated statistics (min, max, avg, count) computed over the
    filtered set.

    Args:
        sensor_id: ID of the sensor.
        start_time: Optional lower bound for ``recorded_at``.
        end_time: Optional upper bound for ``recorded_at``.
        limit: Maximum number of readings to return (max 1000).
        aggregation: Reserved for future aggregation modes.
        db: Database session.
        current_user: Authenticated user.

    Returns:
        ``SensorReadingsHistoryResponse`` containing the sensor metadata,
        readings list, and computed statistics.

    Raises:
        HTTPException: 404 if sensor not found or user does not own the
            greenhouse chain.
    """
    sensor = (
        db.query(Sensor)
        .options(joinedload(Sensor.sensor_type), joinedload(Sensor.device).joinedload(Device.greenhouse))
        .filter(Sensor.id == sensor_id)
        .first()
    )
    if not sensor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sensor not found",
        )

    if sensor.device.greenhouse.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sensor not found",
        )

    readings_query = db.query(SensorReading).filter(SensorReading.sensor_id == sensor_id)

    if start_time is not None:
        readings_query = readings_query.filter(SensorReading.recorded_at >= start_time)
    if end_time is not None:
        readings_query = readings_query.filter(SensorReading.recorded_at <= end_time)

    # Compute statistics over the filtered set.
    stats_query = readings_query.with_entities(
        func.min(SensorReading.value).label("min"),
        func.max(SensorReading.value).label("max"),
        func.avg(SensorReading.value).label("avg"),
        func.count(SensorReading.id).label("count"),
    )
    stats_row = stats_query.one()

    statistics = SensorStatistics(
        min=float(stats_row.min) if stats_row.min is not None else None,
        max=float(stats_row.max) if stats_row.max is not None else None,
        avg=round(float(stats_row.avg), 2) if stats_row.avg is not None else None,
        count=stats_row.count,
    )

    readings = (
        readings_query.order_by(SensorReading.recorded_at.desc())
        .limit(limit)
        .all()
    )

    sensor_type_name = sensor.sensor_type.name if sensor.sensor_type else "unknown"

    return SensorReadingsHistoryResponse(
        sensor_id=sensor.id,
        sensor_type=sensor_type_name,
        unit=sensor.unit,
        readings=[SensorReadingResponse.model_validate(r) for r in readings],
        statistics=statistics,
    )


@router.post(
    "/sensors/{sensor_id}/readings",
    response_model=SensorReadingResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_sensor_reading(
    sensor_id: int,
    body: SensorReadingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SensorReadingResponse:
    """Create a manual sensor reading (useful for testing).

    Args:
        sensor_id: ID of the sensor.
        body: Reading payload with ``value`` and optional ``recorded_at``.
        db: Database session.
        current_user: Authenticated user.

    Returns:
        The newly created ``SensorReadingResponse``.

    Raises:
        HTTPException: 404 if sensor not found or user does not own the
            greenhouse chain.
    """
    sensor = (
        db.query(Sensor)
        .options(joinedload(Sensor.device).joinedload(Device.greenhouse))
        .filter(Sensor.id == sensor_id)
        .first()
    )
    if not sensor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sensor not found",
        )

    if sensor.device.greenhouse.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sensor not found",
        )

    reading = SensorReading(
        sensor_id=sensor_id,
        value=body.value,
        recorded_at=body.recorded_at if body.recorded_at else func.now(),
    )
    db.add(reading)
    db.commit()
    db.refresh(reading)

    return SensorReadingResponse.model_validate(reading)
