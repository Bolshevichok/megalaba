"""Routes for devices."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.dependencies import get_current_user
from app.models import Actuator, Device, Greenhouse, Sensor, User
from app.schemas import DeviceCreate, DeviceListResponse, DeviceResponse, DeviceUpdate

router = APIRouter(tags=["devices"])


def _get_greenhouse_or_404(
    greenhouse_id: int, user: User, db: Session
) -> Greenhouse:
    """Return greenhouse if it exists and is owned by the current user.

    Args:
        greenhouse_id: The greenhouse ID to look up.
        user: The authenticated user.
        db: Database session.

    Returns:
        The greenhouse instance.

    Raises:
        HTTPException: 404 if the greenhouse does not exist or is not owned by the user.
    """
    greenhouse = (
        db.query(Greenhouse)
        .filter(Greenhouse.id == greenhouse_id, Greenhouse.user_id == user.id)
        .first()
    )
    if not greenhouse:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Greenhouse not found",
        )
    return greenhouse


@router.get(
    "/greenhouses/{greenhouse_id}/devices",
    response_model=DeviceListResponse,
)
def list_devices(
    greenhouse_id: int,
    status_filter: str | None = Query(None, alias="status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """List all devices in a greenhouse.

    Args:
        greenhouse_id: The parent greenhouse ID.
        status_filter: Optional device status filter (online/offline).
        db: Database session.
        current_user: The authenticated user.

    Returns:
        Dict with total count and list of devices.
    """
    greenhouse = _get_greenhouse_or_404(greenhouse_id, current_user, db)

    query = db.query(Device).filter(Device.greenhouse_id == greenhouse.id)
    if status_filter is not None:
        query = query.filter(Device.status == status_filter)

    devices = query.all()
    return {"total": len(devices), "devices": devices}


@router.get(
    "/greenhouses/{greenhouse_id}/devices/{device_id}",
    response_model=DeviceResponse,
)
def get_device(
    greenhouse_id: int,
    device_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Device:
    """Get a single device with eager-loaded sensors and actuators.

    Args:
        greenhouse_id: The parent greenhouse ID.
        device_id: The device ID.
        db: Database session.
        current_user: The authenticated user.

    Returns:
        The device instance.

    Raises:
        HTTPException: 404 if the device is not found in the greenhouse.
    """
    greenhouse = _get_greenhouse_or_404(greenhouse_id, current_user, db)

    device = (
        db.query(Device)
        .options(
            joinedload(Device.sensors).joinedload(Sensor.sensor_type),
            joinedload(Device.actuators).joinedload(Actuator.actuator_type),
        )
        .filter(Device.id == device_id, Device.greenhouse_id == greenhouse.id)
        .first()
    )
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found",
        )
    return device


@router.post(
    "/greenhouses/{greenhouse_id}/devices",
    response_model=DeviceResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_device(
    greenhouse_id: int,
    device_in: DeviceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Device:
    """Create a new device in a greenhouse.

    Automatically provisions sensors and actuators based on device_type.

    Args:
        greenhouse_id: The parent greenhouse ID.
        device_in: Device creation payload (must include device_type).
        db: Database session.
        current_user: The authenticated user.

    Returns:
        The newly created device.
    """
    greenhouse = _get_greenhouse_or_404(greenhouse_id, current_user, db)

    data = device_in.model_dump()
    device_type = data.pop("device_type")

    device = Device(greenhouse_id=greenhouse.id, **data)
    db.add(device)
    db.flush()  # get device.id without committing

    device.provision_by_type(device_type, db)

    db.commit()
    db.refresh(device)
    return device


@router.put(
    "/greenhouses/{greenhouse_id}/devices/{device_id}",
    response_model=DeviceResponse,
)
def update_device(
    greenhouse_id: int,
    device_id: int,
    device_in: DeviceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Device:
    """Update an existing device.

    Args:
        greenhouse_id: The parent greenhouse ID.
        device_id: The device ID.
        device_in: Device update payload.
        db: Database session.
        current_user: The authenticated user.

    Returns:
        The updated device.

    Raises:
        HTTPException: 404 if the device is not found in the greenhouse.
    """
    greenhouse = _get_greenhouse_or_404(greenhouse_id, current_user, db)

    device = (
        db.query(Device)
        .filter(Device.id == device_id, Device.greenhouse_id == greenhouse.id)
        .first()
    )
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found",
        )

    update_data = device_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(device, field, value)

    db.commit()
    db.refresh(device)
    return device


@router.delete(
    "/greenhouses/{greenhouse_id}/devices/{device_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_device(
    greenhouse_id: int,
    device_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """Delete a device and its associated sensors/actuators (cascade).

    Args:
        greenhouse_id: The parent greenhouse ID.
        device_id: The device ID.
        db: Database session.
        current_user: The authenticated user.

    Raises:
        HTTPException: 404 if the device is not found in the greenhouse.
    """
    greenhouse = _get_greenhouse_or_404(greenhouse_id, current_user, db)

    device = (
        db.query(Device)
        .filter(Device.id == device_id, Device.greenhouse_id == greenhouse.id)
        .first()
    )
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found",
        )

    db.delete(device)
    db.commit()
