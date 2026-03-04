from fastapi import APIRouter, Depends, HTTPException, status

from app.dependencies import get_current_user, get_db
from app.schemas import SensorHistoryResponse, SensorListResponse, SensorReadingCreate, SensorReadingResponse
from app.services import (
    SENSOR_UNITS,
    VALID_SENSOR_TYPES,
    create_reading,
    get_device,
    get_latest_readings,
    get_sensor_history,
)

router = APIRouter(prefix="/devices/{device_id}/sensors", tags=["sensors"])


def _check_device(db, device_id: str):
    if get_device(db, device_id) is None:
        raise HTTPException(status_code=404, detail="Device not found")


def _check_sensor_type(sensor_type: str):
    if sensor_type not in VALID_SENSOR_TYPES:
        raise HTTPException(status_code=400, detail=f"Invalid sensor type. Must be one of: {', '.join(VALID_SENSOR_TYPES)}")


@router.get("", response_model=SensorListResponse)
def latest_readings(device_id: str, db=Depends(get_db), _user=Depends(get_current_user)):
    _check_device(db, device_id)
    readings = get_latest_readings(db, device_id)
    return SensorListResponse(device_id=device_id, readings=readings)


@router.get("/{sensor_type}", response_model=SensorHistoryResponse)
def sensor_history(
    device_id: str,
    sensor_type: str,
    start_time: str | None = None,
    end_time: str | None = None,
    limit: int = 100,
    aggregation: str | None = None,
    db=Depends(get_db),
    _user=Depends(get_current_user),
):
    _check_device(db, device_id)
    _check_sensor_type(sensor_type)
    readings, stats = get_sensor_history(db, device_id, sensor_type, start_time, end_time, limit, aggregation)
    return SensorHistoryResponse(
        device_id=device_id,
        sensor_type=sensor_type,
        unit=SENSOR_UNITS.get(sensor_type, ""),
        readings=readings,
        statistics=stats,
    )


@router.post("/{sensor_type}", response_model=SensorReadingResponse, status_code=status.HTTP_201_CREATED)
def add_reading(
    device_id: str,
    sensor_type: str,
    data: SensorReadingCreate,
    db=Depends(get_db),
    _user=Depends(get_current_user),
):
    _check_device(db, device_id)
    _check_sensor_type(sensor_type)
    return create_reading(db, device_id, sensor_type, data.model_dump())
