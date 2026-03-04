from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


# ── Error ──────────────────────────────────────────────────────────


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: dict = {}
    timestamp: datetime


class ErrorResponse(BaseModel):
    error: ErrorDetail


# ── Health ─────────────────────────────────────────────────────────


class HealthResponse(BaseModel):
    status: str
    db: str
    timestamp: datetime


# ── Auth / Token ───────────────────────────────────────────────────


class UserCreate(BaseModel):
    username: str = Field(min_length=1, max_length=50)
    email: EmailStr
    password: str = Field(min_length=6)


class UserLogin(BaseModel):
    username: str
    password: str


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenRefresh(BaseModel):
    refresh_token: str


# ── Device ─────────────────────────────────────────────────────────


class DeviceCreate(BaseModel):
    device_id: str = Field(min_length=1, max_length=100)
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    location: str | None = None
    device_type: str = "greenhouse"


class DeviceUpdate(BaseModel):
    name: str | None = None
    location: str | None = None
    is_active: bool | None = None


class DeviceResponse(BaseModel):
    id: int
    device_id: str
    name: str
    description: str | None = None
    location: str | None = None
    device_type: str
    is_active: bool
    is_online: bool
    last_seen: datetime | None = None
    mqtt_client_id: str | None = None
    config: dict | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DeviceList(BaseModel):
    total: int
    limit: int
    offset: int
    devices: list[DeviceResponse]


# ── Sensor Reading ─────────────────────────────────────────────────


class SensorReadingCreate(BaseModel):
    value: float
    timestamp: datetime | None = None


class SensorReadingResponse(BaseModel):
    id: int | None = None
    device_id: str | None = None
    sensor_type: str
    value: float
    unit: str
    timestamp: datetime

    model_config = {"from_attributes": True}


class SensorStatistics(BaseModel):
    min: float
    max: float
    avg: float
    count: int


class SensorListResponse(BaseModel):
    device_id: str
    readings: list[SensorReadingResponse]


class SensorHistoryResponse(BaseModel):
    device_id: str
    sensor_type: str
    unit: str
    readings: list[SensorReadingResponse]
    statistics: SensorStatistics | None = None


# ── Actuator Command ───────────────────────────────────────────────


class ActuatorCommandCreate(BaseModel):
    command: str = Field(pattern=r"^(on|off|toggle|set_level)$")
    parameters: dict | None = None


class ActuatorStatusResponse(BaseModel):
    actuator_type: str
    status: str
    last_command: datetime | None = None
    last_update: datetime | None = None


class ActuatorCommandResponse(BaseModel):
    command_id: int | None = Field(None, alias="id")
    device_id: str
    actuator_type: str
    command: str
    status: str
    created_at: datetime
    executed_at: datetime | None = None
    confirmed_at: datetime | None = None

    model_config = {"from_attributes": True, "populate_by_name": True}


class ActuatorListResponse(BaseModel):
    device_id: str
    actuators: list[ActuatorStatusResponse]


class ActuatorHistoryResponse(BaseModel):
    device_id: str
    actuator_type: str
    commands: list[ActuatorCommandResponse]


# ── Dashboard ──────────────────────────────────────────────────────


class DashboardSummary(BaseModel):
    total_devices: int
    online_devices: int
    offline_devices: int
    active_alerts: int


class DeviceOverview(BaseModel):
    device_id: str
    name: str
    is_online: bool
    current_readings: dict
    actuator_status: dict


class DashboardOverview(BaseModel):
    summary: DashboardSummary
    devices: list[DeviceOverview]
