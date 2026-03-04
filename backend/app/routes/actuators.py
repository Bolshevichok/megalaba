from fastapi import APIRouter, Depends, HTTPException, status

from app.dependencies import get_current_user, get_db
from app.schemas import (
    ActuatorCommandCreate,
    ActuatorCommandResponse,
    ActuatorHistoryResponse,
    ActuatorListResponse,
)
from app.services import (
    VALID_ACTUATOR_TYPES,
    get_actuator_statuses,
    get_command_history,
    get_device,
    send_command,
)

router = APIRouter(prefix="/devices/{device_id}/actuators", tags=["actuators"])


def _check_device(db, device_id: str):
    if get_device(db, device_id) is None:
        raise HTTPException(status_code=404, detail="Device not found")


def _check_actuator_type(actuator_type: str):
    if actuator_type not in VALID_ACTUATOR_TYPES:
        raise HTTPException(status_code=400, detail=f"Invalid actuator type. Must be one of: {', '.join(VALID_ACTUATOR_TYPES)}")


@router.get("", response_model=ActuatorListResponse)
def list_actuators(device_id: str, db=Depends(get_db), _user=Depends(get_current_user)):
    _check_device(db, device_id)
    statuses = get_actuator_statuses(db, device_id)
    return ActuatorListResponse(device_id=device_id, actuators=statuses)


@router.post("/{actuator_type}", response_model=ActuatorCommandResponse, status_code=status.HTTP_202_ACCEPTED)
def command(
    device_id: str,
    actuator_type: str,
    data: ActuatorCommandCreate,
    db=Depends(get_db),
    _user=Depends(get_current_user),
):
    _check_device(db, device_id)
    _check_actuator_type(actuator_type)
    return send_command(db, device_id, actuator_type, data.command, data.parameters)


@router.get("/{actuator_type}/history", response_model=ActuatorHistoryResponse)
def history(
    device_id: str,
    actuator_type: str,
    start_time: str | None = None,
    end_time: str | None = None,
    cmd_status: str | None = None,
    limit: int = 100,
    db=Depends(get_db),
    _user=Depends(get_current_user),
):
    _check_device(db, device_id)
    _check_actuator_type(actuator_type)
    cmds = get_command_history(db, device_id, actuator_type, start_time, end_time, cmd_status, limit)
    return ActuatorHistoryResponse(device_id=device_id, actuator_type=actuator_type, commands=cmds)
