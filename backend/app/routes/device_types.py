"""Device types endpoint — returns available device type templates."""

from fastapi import APIRouter
from pydantic import BaseModel

from app.models import DEVICE_TYPE_TEMPLATES

router = APIRouter(tags=["device-types"])


class SensorInfo(BaseModel):
    name: str
    unit: str


class ActuatorInfo(BaseModel):
    name: str


class DeviceTypeResponse(BaseModel):
    type: str
    description: str
    sensors: list[SensorInfo]
    actuators: list[ActuatorInfo]


@router.get("/device-types", response_model=list[DeviceTypeResponse])
def list_device_types():
    result = []
    for type_key, tmpl in DEVICE_TYPE_TEMPLATES.items():
        result.append(
            DeviceTypeResponse(
                type=type_key,
                description=tmpl["description"],
                sensors=[SensorInfo(name=s[0], unit=s[1]) for s in tmpl["sensors"]],
                actuators=[ActuatorInfo(name=a[0]) for a in tmpl["actuators"]],
            )
        )
    return result
