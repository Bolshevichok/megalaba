"""SQLAlchemy ORM models for the Smart Greenhouse system.

Defines all 10 database entities with relationships, enums, indexes,
and cascade rules matching db_create.sql + Constitution gaps.
"""

import enum

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Session, relationship

from app.database import Base


# ── Device type templates ──────────────────────────────────────
# Each type defines which sensors and actuators are auto-created.
# sensor entries: (sensor_type_name, unit)
# actuator entries: (actuator_type_name,)

DEVICE_TYPE_TEMPLATES: dict[str, dict] = {
    "climate-sensor": {
        "description": "DHT22 — temperature + humidity",
        "sensors": [("temperature", "°C"), ("humidity", "%")],
        "actuators": [],
    },
    "light-controller": {
        "description": "LDR + LED — light sensing and control",
        "sensors": [("light", "lux")],
        "actuators": [("lighting",)],
    },
    "full-greenhouse": {
        "description": "DHT22 + LDR + LED — all sensors and actuators",
        "sensors": [("temperature", "°C"), ("humidity", "%"), ("light", "lux")],
        "actuators": [("lighting",)],
    },
}


class ConnectionType(str, enum.Enum):
    """Device connection type options."""

    wifi = "wifi"
    gsm = "gsm"
    ethernet = "ethernet"
    zigbee = "zigbee"


class DeviceStatus(str, enum.Enum):
    """Device online/offline status."""

    online = "online"
    offline = "offline"


class ActuatorStatus(str, enum.Enum):
    """Actuator on/off status."""

    on = "on"
    off = "off"


class CommandType(str, enum.Enum):
    """Actuator command types."""

    on = "on"
    off = "off"
    set_value = "set_value"


class User(Base):
    """User account model.

    Attributes:
        id: Primary key.
        name: User display name.
        email: Unique email address.
        password_hash: Bcrypt-hashed password.
        billing_address: Optional billing address.
        phone: Optional phone number.
        greenhouses: Related greenhouses.
    """

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    billing_address = Column(Text, nullable=True)
    phone = Column(String(20), nullable=True)

    greenhouses = relationship("Greenhouse", back_populates="user", cascade="all, delete-orphan")


class Greenhouse(Base):
    """Greenhouse model belonging to a user.

    Attributes:
        id: Primary key.
        user_id: FK to users.
        name: Greenhouse name.
        location: Optional location description.
        user: Parent user relationship.
        devices: Child devices.
        scripts: Child automation scripts.
    """

    __tablename__ = "greenhouses"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), nullable=True)
    location = Column(String(255), nullable=True)

    user = relationship("User", back_populates="greenhouses")
    devices = relationship("Device", back_populates="greenhouse", cascade="all, delete-orphan")
    scripts = relationship("Script", back_populates="greenhouse", cascade="all, delete-orphan")


class Device(Base):
    """IoT device model within a greenhouse.

    Attributes:
        id: Primary key.
        greenhouse_id: FK to greenhouses.
        name: Device name.
        connection_type: wifi/gsm/ethernet/zigbee.
        ip_address: Device IP address.
        status: online/offline.
        last_seen: Timestamp of last MQTT message (Constitution VIII).
        greenhouse: Parent greenhouse.
        sensors: Child sensors.
        actuators: Child actuators.
    """

    __tablename__ = "devices"

    id = Column(Integer, primary_key=True, autoincrement=True)
    greenhouse_id = Column(Integer, ForeignKey("greenhouses.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), nullable=True)
    connection_type = Column(Enum(ConnectionType), nullable=True)
    ip_address = Column(String(50), nullable=True)
    status = Column(Enum(DeviceStatus), nullable=True)
    last_seen = Column(DateTime(timezone=True), nullable=True)

    greenhouse = relationship("Greenhouse", back_populates="devices")
    sensors = relationship("Sensor", back_populates="device", cascade="all, delete-orphan")
    actuators = relationship("Actuator", back_populates="device", cascade="all, delete-orphan")

    def provision_by_type(self, device_type: str, db: Session) -> None:
        """Create sensors and actuators according to the device type template.

        Args:
            device_type: Key from DEVICE_TYPE_TEMPLATES.
            db: Active database session (caller is responsible for commit).

        Raises:
            ValueError: If device_type is unknown.
        """
        template = DEVICE_TYPE_TEMPLATES.get(device_type)
        if template is None:
            raise ValueError(f"Unknown device type: {device_type}")

        # Build name->id lookup for sensor/actuator types
        sensor_type_map = {st.name: st.id for st in db.query(SensorType).all()}
        actuator_type_map = {at.name: at.id for at in db.query(ActuatorType).all()}

        for type_name, unit in template["sensors"]:
            type_id = sensor_type_map.get(type_name)
            if type_id is None:
                continue
            db.add(Sensor(device_id=self.id, sensor_type_id=type_id, unit=unit))

        for (type_name,) in template["actuators"]:
            type_id = actuator_type_map.get(type_name)
            if type_id is None:
                continue
            db.add(Actuator(device_id=self.id, actuator_type_id=type_id, status=ActuatorStatus.off))


class SensorType(Base):
    """Sensor type reference table.

    Seed data: temperature, humidity, light.

    Attributes:
        id: Primary key.
        name: Sensor type name.
    """

    __tablename__ = "sensor_types"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=True)


class Sensor(Base):
    """Sensor attached to a device.

    Attributes:
        id: Primary key.
        device_id: FK to devices.
        sensor_type_id: FK to sensor_types.
        name: Sensor display name.
        unit: Measurement unit (e.g. '°C', '%', 'lux').
        device: Parent device.
        sensor_type: Related sensor type.
        readings: Child sensor readings.
    """

    __tablename__ = "sensors"

    id = Column(Integer, primary_key=True, autoincrement=True)
    device_id = Column(Integer, ForeignKey("devices.id", ondelete="CASCADE"), nullable=False)
    sensor_type_id = Column(Integer, ForeignKey("sensor_types.id"), nullable=False)
    name = Column(String(100), nullable=True)
    unit = Column(String(20), nullable=True)

    device = relationship("Device", back_populates="sensors")
    sensor_type = relationship("SensorType")
    readings = relationship("SensorReading", back_populates="sensor", cascade="all, delete-orphan")


class SensorReading(Base):
    """Individual sensor measurement record.

    Attributes:
        id: Primary key.
        sensor_id: FK to sensors.
        value: Measured value.
        recorded_at: Timestamp of the reading.
        sensor: Parent sensor.
    """

    __tablename__ = "sensor_readings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    sensor_id = Column(Integer, ForeignKey("sensors.id", ondelete="CASCADE"), nullable=False)
    value = Column(Float, nullable=True)
    recorded_at = Column(DateTime(timezone=True), server_default=func.now())

    sensor = relationship("Sensor", back_populates="readings")

    __table_args__ = (Index("ix_sensor_readings_sensor_recorded", "sensor_id", recorded_at.desc()),)


class ActuatorType(Base):
    """Actuator type reference table.

    Seed data: lighting, heating, ventilation, watering.

    Attributes:
        id: Primary key.
        name: Actuator type name.
    """

    __tablename__ = "actuator_types"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=True)


class Actuator(Base):
    """Actuator attached to a device.

    Attributes:
        id: Primary key.
        device_id: FK to devices.
        actuator_type_id: FK to actuator_types.
        status: Current on/off state.
        device: Parent device.
        actuator_type: Related actuator type.
        commands: Child command history.
    """

    __tablename__ = "actuators"

    id = Column(Integer, primary_key=True, autoincrement=True)
    device_id = Column(Integer, ForeignKey("devices.id", ondelete="CASCADE"), nullable=False)
    actuator_type_id = Column(Integer, ForeignKey("actuator_types.id"), nullable=False)
    status = Column(Enum(ActuatorStatus), nullable=True)

    device = relationship("Device", back_populates="actuators")
    actuator_type = relationship("ActuatorType")
    commands = relationship("ActuatorCommand", back_populates="actuator", cascade="all, delete-orphan")


class ActuatorCommand(Base):
    """Command sent to an actuator.

    Lifecycle: pending -> sent -> confirmed | failed (Constitution IV).

    Attributes:
        id: Primary key.
        actuator_id: FK to actuators.
        command: Command type (on/off/set_value).
        value: Optional numeric parameter for set_value.
        status: Lifecycle status (pending/sent/confirmed/failed).
        created_at: Command creation timestamp.
        actuator: Parent actuator.
    """

    __tablename__ = "actuator_commands"

    id = Column(Integer, primary_key=True, autoincrement=True)
    actuator_id = Column(Integer, ForeignKey("actuators.id", ondelete="CASCADE"), nullable=False)
    command = Column(Enum(CommandType), nullable=False)
    value = Column(Float, nullable=True)
    status = Column(String(20), default="pending")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    actuator = relationship("Actuator", back_populates="commands")


class Script(Base):
    """Automation script for a greenhouse.

    Attributes:
        id: Primary key.
        greenhouse_id: FK to greenhouses.
        name: Script name.
        script_code: Script source code.
        enabled: Whether the script is active.
        greenhouse: Parent greenhouse.
    """

    __tablename__ = "scripts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    greenhouse_id = Column(Integer, ForeignKey("greenhouses.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), nullable=True)
    script_code = Column(Text, nullable=True)
    enabled = Column(Boolean, default=True)

    greenhouse = relationship("Greenhouse", back_populates="scripts")
