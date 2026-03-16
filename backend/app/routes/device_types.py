"""Routes for device type templates."""

from fastapi import APIRouter

from app.models import DEVICE_TYPE_TEMPLATES
from app.schemas import (
    DeviceTypeActuatorInfo,
    DeviceTypeResponse,
    DeviceTypeSensorInfo,
)

router = APIRouter(tags=["device-types"])


@router.get("/device-types", response_model=list[DeviceTypeResponse])
def list_device_types() -> list[dict]:
    """Return all available device type templates with their sensors and actuators."""
    result = []
    for name, tmpl in DEVICE_TYPE_TEMPLATES.items():
        result.append(
            {
                "name": name,
                "description": tmpl["description"],
                "sensors": [
                    DeviceTypeSensorInfo(type=s[0], unit=s[1]) for s in tmpl["sensors"]
                ],
                "actuators": [
                    DeviceTypeActuatorInfo(type=a[0]) for a in tmpl["actuators"]
                ],
            }
        )
    return result
