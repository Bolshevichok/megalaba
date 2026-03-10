"""Pydantic v2 request/response schemas for the Smart Greenhouse API.

Grouped by entity: User, Greenhouse, Device, Sensor, Actuator,
Script, Dashboard, Health, Auth, Error.
"""

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field

# --- Auth ---


class UserCreate(BaseModel):
    """Schema for user registration request.

    Attributes:
        name: User display name.
        email: Email address.
        password: Plain-text password (hashed on server).
        phone: Optional phone number.
    """

    name: str = Field(..., max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=6)
    phone: str | None = None


class UserResponse(BaseModel):
    """Schema for user profile response.

    Attributes:
        id: User ID.
        name: Display name.
        email: Email address.
        phone: Phone number.
        billing_address: Billing address.
        created_at: Not in DB but kept for API compatibility.
    """

    id: int
    name: str
    email: str
    phone: str | None = None
    billing_address: str | None = None

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    """Schema for JWT token response.

    Attributes:
        access_token: JWT access token.
        token_type: Token type (always 'bearer').
        expires_in: Token TTL in seconds.
        refresh_token: Optional refresh token.
    """

    access_token: str
    token_type: str = "bearer"
    expires_in: int
    refresh_token: str | None = None


class RefreshRequest(BaseModel):
    """Schema for token refresh request.

    Attributes:
        refresh_token: Valid refresh token.
    """

    refresh_token: str


class LoginRequest(BaseModel):
    """Schema for login request.

    Attributes:
        email: User email.
        password: User password.
    """

    email: EmailStr
    password: str


# --- Greenhouse ---


class GreenhouseCreate(BaseModel):
    """Schema for greenhouse creation.

    Attributes:
        name: Greenhouse name.
        location: Optional location string.
    """

    name: str = Field(..., max_length=100)
    location: str | None = None


class GreenhouseUpdate(BaseModel):
    """Schema for greenhouse update (all fields optional).

    Attributes:
        name: New name.
        location: New location.
    """

    name: str | None = None
    location: str | None = None


class GreenhouseResponse(BaseModel):
    """Schema for greenhouse in API responses.

    Attributes:
        id: Greenhouse ID.
        user_id: Owner user ID.
        name: Greenhouse name.
        location: Location string.
    """

    id: int
    user_id: int
    name: str | None = None
    location: str | None = None

    model_config = {"from_attributes": True}


class GreenhouseListResponse(BaseModel):
    """Schema for paginated greenhouse list.

    Attributes:
        total: Total count.
        greenhouses: List of greenhouses.
    """

    total: int
    greenhouses: list[GreenhouseResponse]


# --- Device ---


class DeviceCreate(BaseModel):
    """Schema for device creation.

    Attributes:
        name: Device name.
        connection_type: Connection type (wifi/gsm/ethernet/zigbee).
        ip_address: Optional IP address.
    """

    name: str = Field(..., max_length=100)
    connection_type: str | None = None
    ip_address: str | None = None


class DeviceUpdate(BaseModel):
    """Schema for device update.

    Attributes:
        name: New device name.
        connection_type: New connection type.
        ip_address: New IP address.
    """

    name: str | None = None
    connection_type: str | None = None
    ip_address: str | None = None


class DeviceResponse(BaseModel):
    """Schema for device in API responses.

    Attributes:
        id: Device ID.
        greenhouse_id: Parent greenhouse ID.
        name: Device name.
        connection_type: Connection type.
        ip_address: IP address.
        status: Online/offline status.
        last_seen: Last MQTT activity timestamp.
    """

    id: int
    greenhouse_id: int
    name: str | None = None
    connection_type: str | None = None
    ip_address: str | None = None
    status: str | None = None
    last_seen: datetime | None = None

    model_config = {"from_attributes": True}


class DeviceListResponse(BaseModel):
    """Schema for device list response.

    Attributes:
        total: Total device count.
        devices: List of devices.
    """

    total: int
    devices: list[DeviceResponse]


# --- Sensor ---


class SensorResponse(BaseModel):
    """Schema for sensor in API responses.

    Attributes:
        id: Sensor ID.
        device_id: Parent device ID.
        sensor_type_id: Sensor type FK.
        name: Sensor name.
        unit: Measurement unit.
    """

    id: int
    device_id: int
    sensor_type_id: int
    name: str | None = None
    unit: str | None = None

    model_config = {"from_attributes": True}


class SensorReadingCreate(BaseModel):
    """Schema for creating a manual sensor reading.

    Attributes:
        value: Sensor value.
        recorded_at: Optional timestamp (defaults to now).
    """

    value: float
    recorded_at: datetime | None = None


class SensorReadingResponse(BaseModel):
    """Schema for a single sensor reading.

    Attributes:
        id: Reading ID.
        sensor_id: Parent sensor ID.
        value: Measured value.
        recorded_at: Timestamp.
    """

    id: int
    sensor_id: int
    value: float | None = None
    recorded_at: datetime | None = None

    model_config = {"from_attributes": True}


class SensorStatistics(BaseModel):
    """Aggregated statistics for sensor readings.

    Attributes:
        min: Minimum value.
        max: Maximum value.
        avg: Average value.
        count: Number of readings.
    """

    min: float | None = None
    max: float | None = None
    avg: float | None = None
    count: int = 0


class SensorReadingsHistoryResponse(BaseModel):
    """Schema for historical sensor readings with statistics.

    Attributes:
        sensor_id: Sensor ID.
        sensor_type: Type name (temperature/humidity/light).
        unit: Measurement unit.
        readings: List of readings.
        statistics: Aggregated stats.
    """

    sensor_id: int
    sensor_type: str
    unit: str | None = None
    readings: list[SensorReadingResponse]
    statistics: SensorStatistics


# --- Actuator ---


class ActuatorResponse(BaseModel):
    """Schema for actuator in API responses.

    Attributes:
        id: Actuator ID.
        device_id: Parent device ID.
        actuator_type_id: Actuator type FK.
        status: Current on/off status.
    """

    id: int
    device_id: int
    actuator_type_id: int
    status: str | None = None

    model_config = {"from_attributes": True}


class ActuatorCommandCreate(BaseModel):
    """Schema for sending an actuator command.

    Attributes:
        command: Command type (on/off/set_value).
        value: Optional numeric value for set_value.
    """

    command: str = Field(..., pattern="^(on|off|set_value)$")
    value: float | None = None


class ActuatorCommandResponse(BaseModel):
    """Schema for actuator command in responses.

    Attributes:
        id: Command ID.
        actuator_id: Parent actuator ID.
        command: Command type.
        value: Optional parameter.
        status: Lifecycle status (pending/sent/confirmed/failed).
        created_at: Command creation time.
    """

    id: int
    actuator_id: int
    command: str
    value: float | None = None
    status: str | None = None
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


# --- Script ---


class ScriptCreate(BaseModel):
    """Schema for script creation.

    Attributes:
        name: Script name.
        script_code: Script source code.
        enabled: Whether the script is active.
    """

    name: str = Field(..., max_length=100)
    script_code: str | None = None
    enabled: bool = True


class ScriptUpdate(BaseModel):
    """Schema for script update.

    Attributes:
        name: New name.
        script_code: New code.
        enabled: New enabled state.
    """

    name: str | None = None
    script_code: str | None = None
    enabled: bool | None = None


class ScriptResponse(BaseModel):
    """Schema for script in API responses.

    Attributes:
        id: Script ID.
        greenhouse_id: Parent greenhouse ID.
        name: Script name.
        script_code: Source code.
        enabled: Active state.
    """

    id: int
    greenhouse_id: int
    name: str | None = None
    script_code: str | None = None
    enabled: bool | None = None

    model_config = {"from_attributes": True}


# --- Dashboard ---


class DashboardDeviceInfo(BaseModel):
    """Device info within dashboard overview.

    Attributes:
        id: Device ID.
        name: Device name.
        status: Online/offline.
        latest_readings: Dict of sensor_type -> latest value.
        actuator_statuses: Dict of actuator_type -> on/off.
    """

    id: int
    name: str | None = None
    status: str | None = None
    latest_readings: dict[str, float | None] = {}
    actuator_statuses: dict[str, str | None] = {}


class DashboardGreenhouseInfo(BaseModel):
    """Greenhouse info within dashboard overview.

    Attributes:
        id: Greenhouse ID.
        name: Greenhouse name.
        devices: List of device info.
    """

    id: int
    name: str | None = None
    devices: list[DashboardDeviceInfo] = []


class DashboardSummary(BaseModel):
    """Summary statistics for dashboard.

    Attributes:
        total_greenhouses: Count of greenhouses.
        total_devices: Count of all devices.
        online_devices: Count of online devices.
        offline_devices: Count of offline devices.
    """

    total_greenhouses: int = 0
    total_devices: int = 0
    online_devices: int = 0
    offline_devices: int = 0


class DashboardOverviewResponse(BaseModel):
    """Schema for dashboard overview endpoint.

    Attributes:
        summary: Aggregated counts.
        greenhouses: Detailed greenhouse info.
    """

    summary: DashboardSummary
    greenhouses: list[DashboardGreenhouseInfo] = []


# --- Health ---


class HealthResponse(BaseModel):
    """Schema for main health check response.

    Attributes:
        status: Overall service status.
        db: Database status.
        mqtt: MQTT broker status.
        timestamp: Current server time.
    """

    status: str
    db: str
    mqtt: str
    timestamp: datetime


class HealthDBResponse(BaseModel):
    """Schema for database health sub-endpoint.

    Attributes:
        status: DB connection status.
        latency_ms: Connection latency in milliseconds.
    """

    status: str
    latency_ms: float


class HealthMQTTResponse(BaseModel):
    """Schema for MQTT health sub-endpoint.

    Attributes:
        status: MQTT connection status.
        connected: Whether the client is connected.
    """

    status: str
    connected: bool


# --- Error ---


class ErrorDetail(BaseModel):
    """Standardized error detail.

    Attributes:
        code: Error code string.
        message: Human-readable message.
        timestamp: Error timestamp.
    """

    code: str
    message: str
    timestamp: datetime


class ErrorResponse(BaseModel):
    """Standardized error response wrapper.

    Attributes:
        error: Error detail object.
    """

    error: ErrorDetail
