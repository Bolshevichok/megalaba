from fastapi import APIRouter, Depends, HTTPException, Response, status

from app.dependencies import get_current_user, get_db
from app.schemas import DeviceCreate, DeviceList, DeviceResponse, DeviceUpdate
from app.services import (
    create_device,
    delete_device,
    get_device,
    list_devices,
    update_device,
)

router = APIRouter(prefix="/devices", tags=["devices"])


@router.get("", response_model=DeviceList)
def list_all(
    limit: int = 100,
    offset: int = 0,
    is_active: bool | None = None,
    is_online: bool | None = None,
    db=Depends(get_db),
    _user=Depends(get_current_user),
):
    devices, total = list_devices(db, limit, offset, is_active, is_online)
    return DeviceList(total=total, limit=limit, offset=offset, devices=devices)


@router.get("/{device_id}", response_model=DeviceResponse)
def get_one(device_id: str, db=Depends(get_db), _user=Depends(get_current_user)):
    device = get_device(db, device_id)
    if device is None:
        raise HTTPException(status_code=404, detail="Device not found")
    return device


@router.post("", response_model=DeviceResponse, status_code=status.HTTP_201_CREATED)
def create(data: DeviceCreate, db=Depends(get_db), _user=Depends(get_current_user)):
    return create_device(db, data.model_dump())


@router.put("/{device_id}", response_model=DeviceResponse)
def update(device_id: str, data: DeviceUpdate, db=Depends(get_db), _user=Depends(get_current_user)):
    device = update_device(db, device_id, data.model_dump(exclude_unset=True))
    if device is None:
        raise HTTPException(status_code=404, detail="Device not found")
    return device


@router.delete("/{device_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete(device_id: str, db=Depends(get_db), _user=Depends(get_current_user)):
    if not delete_device(db, device_id):
        raise HTTPException(status_code=404, detail="Device not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
