"""Routes for actuators."""

import json
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.dependencies import get_current_user
from app.models import (
    Actuator,
    ActuatorCommand,
    Device,
    DeviceStatus,
    Greenhouse,
    User,
)
from app.mqtt.client import mqtt_client
from app.mqtt.topics import command_topic
from app.schemas import ActuatorCommandCreate, ActuatorCommandResponse, ActuatorResponse

router = APIRouter(tags=["actuators"])


@router.get("/greenhouses/{greenhouse_id}/devices/{device_id}/actuators")
def list_actuators(
    greenhouse_id: int,
    device_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """List actuators for a device with their last command.

    Args:
        greenhouse_id: Greenhouse ID from path.
        device_id: Device ID from path.
        db: Database session.
        current_user: Authenticated user.

    Returns:
        Dict with list of actuators.

    Raises:
        HTTPException: 404 if greenhouse or device not found or ownership mismatch.
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

    actuators = (
        db.query(Actuator)
        .options(joinedload(Actuator.actuator_type), joinedload(Actuator.commands))
        .filter(Actuator.device_id == device_id)
        .all()
    )

    return {"actuators": [ActuatorResponse.model_validate(a) for a in actuators]}


@router.post("/actuators/{actuator_id}/commands", status_code=status.HTTP_202_ACCEPTED)
def send_actuator_command(
    actuator_id: int,
    data: ActuatorCommandCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Send a command to an actuator.

    Args:
        actuator_id: Actuator ID from path.
        data: Command payload with command type and optional value.
        db: Database session.
        current_user: Authenticated user.

    Returns:
        Dict with command ID and status.

    Raises:
        HTTPException: 404 if actuator not found or ownership mismatch.
        HTTPException: 409 if device is offline.
    """
    actuator = (
        db.query(Actuator)
        .options(
            joinedload(Actuator.device).joinedload(Device.greenhouse),
            joinedload(Actuator.actuator_type),
        )
        .filter(Actuator.id == actuator_id)
        .first()
    )
    if not actuator:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Actuator not found",
        )

    if actuator.device.greenhouse.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Actuator not found",
        )

    if actuator.device.status == DeviceStatus.offline:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Device is offline",
        )

    cmd = ActuatorCommand(
        actuator_id=actuator_id,
        command=data.command,
        value=data.value,
        status="pending",
    )
    db.add(cmd)
    db.flush()

    actuator_type_name = actuator.actuator_type.name
    mqtt_client.publish(
        command_topic(actuator.device_id, actuator_type_name),
        json.dumps({"command": data.command, "value": data.value}),
    )

    cmd.status = "sent"
    db.commit()
    db.refresh(cmd)

    return {"command_id": cmd.id, "status": cmd.status}


@router.get("/actuators/{actuator_id}/commands")
def get_command_history(
    actuator_id: int,
    start_time: datetime | None = None,
    end_time: datetime | None = None,
    limit: int = Query(100, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Get command history for an actuator.

    Args:
        actuator_id: Actuator ID from path.
        start_time: Optional start of time range filter.
        end_time: Optional end of time range filter.
        limit: Maximum number of commands to return (max 1000).
        db: Database session.
        current_user: Authenticated user.

    Returns:
        Dict with actuator info and list of commands.

    Raises:
        HTTPException: 404 if actuator not found or ownership mismatch.
    """
    actuator = (
        db.query(Actuator)
        .options(
            joinedload(Actuator.device).joinedload(Device.greenhouse),
            joinedload(Actuator.actuator_type),
        )
        .filter(Actuator.id == actuator_id)
        .first()
    )
    if not actuator:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Actuator not found",
        )

    if actuator.device.greenhouse.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Actuator not found",
        )

    query = db.query(ActuatorCommand).filter(ActuatorCommand.actuator_id == actuator_id)

    if start_time:
        query = query.filter(ActuatorCommand.created_at >= start_time)
    if end_time:
        query = query.filter(ActuatorCommand.created_at <= end_time)

    commands = (
        query.order_by(ActuatorCommand.created_at.desc())
        .limit(limit)
        .all()
    )

    return {
        "actuator_id": actuator_id,
        "actuator_type": actuator.actuator_type.name,
        "commands": [ActuatorCommandResponse.model_validate(c) for c in commands],
    }
