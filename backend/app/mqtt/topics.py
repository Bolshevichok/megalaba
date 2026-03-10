"""MQTT topic constants and helper functions."""

SENSOR_TOPIC_PATTERN = "devices/+/sensors/+"
STATUS_TOPIC_PATTERN = "devices/+/status/+"
LWT_TOPIC_PATTERN = "devices/+/lwt"


def command_topic(device_id: int, actuator_type: str) -> str:
    """Build MQTT command topic for an actuator.

    Args:
        device_id: Device ID.
        actuator_type: Actuator type name (lighting/heating/ventilation/watering).

    Returns:
        MQTT topic string.
    """
    return f"devices/{device_id}/commands/{actuator_type}"


def parse_topic(topic: str) -> tuple[str, str, str]:
    """Parse an MQTT topic into components.

    Args:
        topic: Full MQTT topic string like 'devices/1/sensors/temperature'.

    Returns:
        Tuple of (device_id, category, type_name).

    Raises:
        ValueError: If topic format is invalid.
    """
    parts = topic.split("/")
    if len(parts) != 4 or parts[0] != "devices":
        raise ValueError(f"Invalid topic format: {topic}")
    return parts[1], parts[2], parts[3]
