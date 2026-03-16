"""Routes for dashboard overview."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.dependencies import get_current_user
from app.models import (
    Actuator,
    Device,
    DeviceStatus,
    Greenhouse,
    Sensor,
    User,
)
from app.schemas import (
    DashboardDeviceInfo,
    DashboardGreenhouseInfo,
    DashboardOverviewResponse,
    DashboardSummary,
)

router = APIRouter(tags=["dashboard"])


@router.get("/dashboard/overview", response_model=DashboardOverviewResponse)
def dashboard_overview(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DashboardOverviewResponse:
    """Return aggregated dashboard data for the current user.

    Queries all greenhouses owned by the user with their devices,
    sensors, and actuators. Builds summary counts and per-device
    latest sensor readings and actuator statuses.

    Args:
        db: Database session.
        current_user: Authenticated user.

    Returns:
        Dashboard overview with summary counts and greenhouse details.
    """
    greenhouses = (
        db.query(Greenhouse)
        .filter(Greenhouse.user_id == current_user.id)
        .options(
            joinedload(Greenhouse.devices)
            .joinedload(Device.sensors)
            .joinedload(Sensor.sensor_type),
            joinedload(Greenhouse.devices)
            .joinedload(Device.sensors)
            .joinedload(Sensor.readings),
            joinedload(Greenhouse.devices)
            .joinedload(Device.actuators)
            .joinedload(Actuator.actuator_type),
        )
        .all()
    )

    total_greenhouses = len(greenhouses)
    total_devices = 0
    online_devices = 0
    offline_devices = 0
    greenhouse_infos: list[DashboardGreenhouseInfo] = []

    for gh in greenhouses:
        device_infos: list[DashboardDeviceInfo] = []
        for device in gh.devices:
            total_devices += 1
            if device.status == DeviceStatus.online:
                online_devices += 1
            else:
                offline_devices += 1

            latest_readings: dict[str, float | None] = {}
            for sensor in device.sensors:
                type_name = sensor.sensor_type.name if sensor.sensor_type else "unknown"
                most_recent = None
                for reading in sensor.readings:
                    if most_recent is None or (
                        reading.recorded_at is not None
                        and (most_recent.recorded_at is None or reading.recorded_at > most_recent.recorded_at)
                    ):
                        most_recent = reading
                latest_readings[type_name] = most_recent.value if most_recent else None

            actuator_statuses: dict[str, str | None] = {}
            for actuator in device.actuators:
                type_name = actuator.actuator_type.name if actuator.actuator_type else "unknown"
                actuator_statuses[type_name] = actuator.status.value if actuator.status is not None else None

            device_infos.append(
                DashboardDeviceInfo(
                    id=device.id,
                    name=device.name,
                    status=device.status.value if device.status else None,
                    latest_readings=latest_readings,
                    actuator_statuses=actuator_statuses,
                )
            )

        greenhouse_infos.append(
            DashboardGreenhouseInfo(
                id=gh.id,
                name=gh.name,
                devices=device_infos,
            )
        )

    return DashboardOverviewResponse(
        summary=DashboardSummary(
            total_greenhouses=total_greenhouses,
            total_devices=total_devices,
            online_devices=online_devices,
            offline_devices=offline_devices,
        ),
        greenhouses=greenhouse_infos,
    )
