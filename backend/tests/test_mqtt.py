"""Tests for MQTT topic parsing utilities."""

import pytest

from app.mqtt.topics import command_topic, parse_topic


def test_parse_sensor_topic():
    """Parse a valid sensor topic into device_id, category, and type_name."""
    device_id, category, type_name = parse_topic("devices/42/sensors/temperature")
    assert device_id == "42"
    assert category == "sensors"
    assert type_name == "temperature"


def test_command_topic():
    """Build a command topic string from device ID and actuator type."""
    assert command_topic(1, "heating") == "devices/1/commands/heating"


def test_parse_invalid_topic():
    """Verify that an invalid topic raises ValueError."""
    with pytest.raises(ValueError):
        parse_topic("invalid/topic")
