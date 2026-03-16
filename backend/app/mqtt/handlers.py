"""MQTT message handlers for incoming device telemetry.

Routes incoming MQTT messages to the appropriate handler based on
topic category (sensors, status, lwt) and persists data to the database.
"""

import json
import logging
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import (
    Actuator,
    ActuatorCommand,
    ActuatorType,
    Device,
    DeviceStatus,
    Sensor,
    SensorReading,
    SensorType,
)

logger = logging.getLogger("greenhouse.mqtt")


def on_message(client, userdata, message) -> None:
    """Route an incoming MQTT message to the appropriate handler.

    Parses the topic to determine message category and delegates to
    handle_sensor_message, handle_status_message, or handle_lwt_message.

    Args:
        client: MQTT client instance.
        userdata: User data set on the client.
        message: MQTT message with topic and payload attributes.
    """
    topic = message.topic
    payload_str = message.payload.decode("utf-8", errors="replace")

    parts = topic.split("/")
    if len(parts) < 3 or parts[0] != "devices":
        logger.warning("Unknown topic format: %s", topic)
        return

    device_id_str = parts[1]
    category = parts[2]

    if category == "sensors" and len(parts) == 4:
        sensor_type_name = parts[3]
        handle_sensor_message(device_id_str, sensor_type_name, payload_str)
    elif category == "status" and len(parts) == 4:
        actuator_type_name = parts[3]
        handle_status_message(device_id_str, actuator_type_name, payload_str)
    elif category == "lwt":
        handle_lwt_message(device_id_str)
    else:
        logger.warning("Unhandled topic category '%s' in topic: %s", category, topic)


def handle_sensor_message(
    device_id_str: str, sensor_type_name: str, payload_str: str
) -> None:
    """Handle an incoming sensor data message.

    Parses the JSON payload, looks up the sensor by device ID and
    sensor type name, creates a SensorReading, and updates the
    device last_seen timestamp.

    Args:
        device_id_str: Device ID as a string from the MQTT topic.
        sensor_type_name: Sensor type name (e.g. 'temperature').
        payload_str: JSON-encoded payload string with a 'value' key.
    """
    db: Session = SessionLocal()
    try:
        payload = json.loads(payload_str)
        device_id = int(device_id_str)

        sensor_type = (
            db.query(SensorType).filter(SensorType.name == sensor_type_name).first()
        )
        if sensor_type is None:
            logger.warning("Unknown sensor type: %s", sensor_type_name)
            return

        sensor = (
            db.query(Sensor)
            .filter(
                Sensor.device_id == device_id,
                Sensor.sensor_type_id == sensor_type.id,
            )
            .first()
        )
        if sensor is None:
            logger.warning(
                "Sensor not found for device %s type %s",
                device_id_str,
                sensor_type_name,
            )
            return

        reading = SensorReading(
            sensor_id=sensor.id,
            value=payload.get("value"),
            recorded_at=datetime.now(timezone.utc),
        )
        db.add(reading)

        device = db.query(Device).filter(Device.id == device_id).first()
        if device:
            device.last_seen = datetime.now(timezone.utc)

        db.commit()
        logger.info(
            "Sensor reading saved: device=%s type=%s value=%s",
            device_id_str,
            sensor_type_name,
            payload.get("value"),
        )
    except Exception:
        db.rollback()
        logger.exception(
            "Error handling sensor message for device %s", device_id_str
        )
    finally:
        db.close()


def handle_status_message(
    device_id_str: str, actuator_type_name: str, payload_str: str
) -> None:
    """Handle an incoming actuator status message.

    Parses the JSON payload, finds the actuator by device ID and
    actuator type name, updates actuator status, and confirms the
    latest pending or sent command.

    Args:
        device_id_str: Device ID as a string from the MQTT topic.
        actuator_type_name: Actuator type name (e.g. 'heating').
        payload_str: JSON-encoded payload string with a 'status' key.
    """
    db: Session = SessionLocal()
    try:
        payload = json.loads(payload_str)
        device_id = int(device_id_str)

        actuator_type = (
            db.query(ActuatorType)
            .filter(ActuatorType.name == actuator_type_name)
            .first()
        )
        if actuator_type is None:
            logger.warning("Unknown actuator type: %s", actuator_type_name)
            return

        actuator = (
            db.query(Actuator)
            .filter(
                Actuator.device_id == device_id,
                Actuator.actuator_type_id == actuator_type.id,
            )
            .first()
        )
        if actuator is None:
            logger.warning(
                "Actuator not found for device %s type %s",
                device_id_str,
                actuator_type_name,
            )
            return

        new_status = payload.get("status")
        if new_status:
            actuator.status = new_status

        # Confirm the latest pending or sent command
        latest_command = (
            db.query(ActuatorCommand)
            .filter(
                ActuatorCommand.actuator_id == actuator.id,
                ActuatorCommand.status.in_(["pending", "sent"]),
            )
            .order_by(ActuatorCommand.created_at.desc())
            .first()
        )
        if latest_command:
            latest_command.status = "confirmed"

        db.commit()
        logger.info(
            "Actuator status updated: device=%s type=%s status=%s",
            device_id_str,
            actuator_type_name,
            new_status,
        )
    except Exception:
        db.rollback()
        logger.exception(
            "Error handling status message for device %s", device_id_str
        )
    finally:
        db.close()


def handle_lwt_message(device_id_str: str) -> None:
    """Handle a Last Will and Testament (LWT) message.

    Sets the device status to offline when the MQTT broker publishes
    the device's LWT message (indicating unexpected disconnection).

    Args:
        device_id_str: Device ID as a string from the MQTT topic.
    """
    db: Session = SessionLocal()
    try:
        device_id = int(device_id_str)
        device = db.query(Device).filter(Device.id == device_id).first()
        if device is None:
            logger.warning("Device not found for LWT: %s", device_id_str)
            return

        device.status = DeviceStatus.offline
        db.commit()
        logger.info("Device %s marked as offline via LWT", device_id_str)
    except Exception:
        db.rollback()
        logger.exception("Error handling LWT message for device %s", device_id_str)
    finally:
        db.close()
