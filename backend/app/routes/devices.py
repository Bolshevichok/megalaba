"""Routes for devices."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.dependencies import get_current_user
from app.models import Actuator, Device, Greenhouse, Sensor, User
from app.schemas import DeviceCreate, DeviceListResponse, DeviceResponse, DeviceUpdate

router = APIRouter(tags=["devices"])


def _serialize_device(device: Device) -> dict:
    """Serialize device with capability counts used by frontend automation UI."""
    return {
        "id": device.id,
        "greenhouse_id": device.greenhouse_id,
        "name": device.name,
        "connection_type": device.connection_type.value if device.connection_type else None,
        "ip_address": device.ip_address,
        "status": device.status.value if device.status else None,
        "last_seen": device.last_seen,
        "sensor_count": len(device.sensors or []),
        "actuator_count": len(device.actuators or []),
        "sensors": [
            {
                "id": s.id,
                "device_id": s.device_id,
                "sensor_type_id": s.sensor_type_id,
                "name": s.name,
                "unit": s.unit,
                "type_name": s.sensor_type.name if s.sensor_type else None
            }
            for s in (device.sensors or [])
        ],
        "actuators": [
            {
                "id": a.id,
                "device_id": a.device_id,
                "actuator_type_id": a.actuator_type_id,
                "status": a.status.value if a.status else None,
                "type_name": a.actuator_type.name if a.actuator_type else None
            }
            for a in (device.actuators or [])
        ]
    }


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
    "/devices/unassigned",
    response_model=DeviceListResponse,
)
def list_unassigned_devices(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """List all devices that are not assigned to any greenhouse."""
    # We might want to restrict this to admins, but for now any authenticated user can pull them
    devices = (
        db.query(Device)
        .options(
            joinedload(Device.sensors).joinedload(Sensor.sensor_type),
            joinedload(Device.actuators).joinedload(Actuator.actuator_type),
        )
        .filter(Device.greenhouse_id == None)
        .all()
    )
    return {"total": len(devices), "devices": [_serialize_device(d) for d in devices]}


@router.patch(
    "/devices/{device_id}/assign",
    response_model=DeviceResponse,
)
def assign_device(
    device_id: int,
    greenhouse_id: int | None = Query(None, description="Greenhouse to assign to, or null to unassign"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Device:
    """Assign or unassign a device to a greenhouse."""
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found",
        )
        
    if greenhouse_id is not None:
        _get_greenhouse_or_404(greenhouse_id, current_user, db)

    device.greenhouse_id = greenhouse_id
    db.commit()
    db.refresh(device)
    db.refresh(device)
    return _serialize_device(device)


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

    query = (
        db.query(Device)
        .options(
            joinedload(Device.sensors).joinedload(Sensor.sensor_type),
            joinedload(Device.actuators).joinedload(Actuator.actuator_type),
        )
        .filter(Device.greenhouse_id == greenhouse.id)
    )
    if status_filter is not None:
        query = query.filter(Device.status == status_filter)

    devices = query.all()
    return {"total": len(devices), "devices": [_serialize_device(d) for d in devices]}


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
    return _serialize_device(device)


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
    return _serialize_device(device)


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
    return _serialize_device(device)


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
