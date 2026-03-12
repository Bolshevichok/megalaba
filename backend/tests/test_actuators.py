"""Tests for actuator and actuator command endpoints."""

from unittest.mock import patch

from app.models import Actuator, Device, DeviceStatus

API = "/api/v1"


def _setup_actuator(client, auth_headers, db_session, device_status=None):
    """Create greenhouse, device, and actuator for testing.

    Args:
        client: Test HTTP client.
        auth_headers: Authorization headers with valid JWT.
        db_session: Test database session.
        device_status: Optional device status to set.

    Returns:
        tuple: (greenhouse_id, device_id, actuator_id).
    """
    resp = client.post(
        f"{API}/greenhouses",
        json={"name": "GH", "location": "Lab"},
        headers=auth_headers,
    )
    gh_id = resp.json()["id"]

    resp = client.post(
        f"{API}/greenhouses/{gh_id}/devices",
        json={"name": "Dev", "connection_type": "wifi"},
        headers=auth_headers,
    )
    device_id = resp.json()["id"]

    if device_status is not None:
        device = db_session.get(Device, device_id)
        device.status = device_status
        db_session.commit()

    actuator = Actuator(device_id=device_id, actuator_type_id=1)
    db_session.add(actuator)
    db_session.commit()
    db_session.refresh(actuator)

    return gh_id, device_id, actuator.id


def test_list_actuators(client, auth_headers, db_session):
    """Add an actuator and verify it appears in the list.

    Args:
        client: Test HTTP client.
        auth_headers: Authorization headers with valid JWT.
        db_session: Test database session.
    """
    gh_id, device_id, _ = _setup_actuator(client, auth_headers, db_session)

    response = client.get(
        f"{API}/greenhouses/{gh_id}/devices/{device_id}/actuators",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["actuators"]) >= 1


@patch("app.routes.actuators.mqtt_client")
def test_send_command(mock_mqtt, client, auth_headers, db_session):
    """Send a command to an online device and verify 202.

    Args:
        mock_mqtt: Mocked MQTT client.
        client: Test HTTP client.
        auth_headers: Authorization headers with valid JWT.
        db_session: Test database session.
    """
    _, _, actuator_id = _setup_actuator(
        client, auth_headers, db_session, device_status=DeviceStatus.online
    )

    response = client.post(
        f"{API}/actuators/{actuator_id}/commands",
        json={"command": "on"},
        headers=auth_headers,
    )
    assert response.status_code == 202
    data = response.json()
    assert "command_id" in data
    assert data["status"] == "sent"


def test_reject_command_offline_device(client, auth_headers, db_session):
    """Verify command is rejected with 409 when device is offline.

    Args:
        client: Test HTTP client.
        auth_headers: Authorization headers with valid JWT.
        db_session: Test database session.
    """
    _, _, actuator_id = _setup_actuator(
        client, auth_headers, db_session, device_status=DeviceStatus.offline
    )

    response = client.post(
        f"{API}/actuators/{actuator_id}/commands",
        json={"command": "on"},
        headers=auth_headers,
    )
    assert response.status_code == 409


@patch("app.routes.actuators.mqtt_client")
def test_command_history(mock_mqtt, client, auth_headers, db_session):
    """Send a command and verify it appears in the history.

    Args:
        mock_mqtt: Mocked MQTT client.
        client: Test HTTP client.
        auth_headers: Authorization headers with valid JWT.
        db_session: Test database session.
    """
    _, _, actuator_id = _setup_actuator(
        client, auth_headers, db_session, device_status=DeviceStatus.online
    )

    # Send a command first
    client.post(
        f"{API}/actuators/{actuator_id}/commands",
        json={"command": "on"},
        headers=auth_headers,
    )

    response = client.get(
        f"{API}/actuators/{actuator_id}/commands",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert "commands" in data
    assert len(data["commands"]) >= 1
