"""Tests for sensor and sensor reading endpoints."""

from app.models import Device, Greenhouse, Sensor

API = "/api/v1"


def _setup_greenhouse_device(db_session, user_id):
    """Create a greenhouse and device in the database.

    Args:
        db_session: Test database session.
        user_id: Owner user ID.

    Returns:
        tuple: (greenhouse_id, device_id).
    """
    gh = Greenhouse(user_id=user_id, name="Sensor GH", location="Lab")
    db_session.add(gh)
    db_session.commit()
    db_session.refresh(gh)

    device = Device(greenhouse_id=gh.id, name="Sensor Device")
    db_session.add(device)
    db_session.commit()
    db_session.refresh(device)

    return gh.id, device.id


def test_list_sensors(client, auth_headers, db_session):
    """Add a sensor directly in the DB and verify it appears in the list.

    Args:
        client: Test HTTP client.
        auth_headers: Authorization headers with valid JWT.
        db_session: Test database session.
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

    sensor = Sensor(
        device_id=device_id, sensor_type_id=1, name="Temp", unit="°C"
    )
    db_session.add(sensor)
    db_session.commit()

    response = client.get(
        f"{API}/greenhouses/{gh_id}/devices/{device_id}/sensors",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["sensors"]) >= 1


def test_create_reading(client, auth_headers, db_session):
    """Create a sensor reading via API and verify 201.

    Args:
        client: Test HTTP client.
        auth_headers: Authorization headers with valid JWT.
        db_session: Test database session.
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

    sensor = Sensor(
        device_id=device_id, sensor_type_id=1, name="Temp", unit="°C"
    )
    db_session.add(sensor)
    db_session.commit()
    db_session.refresh(sensor)

    response = client.post(
        f"{API}/sensors/{sensor.id}/readings",
        json={"value": 25.0},
        headers=auth_headers,
    )
    assert response.status_code == 201
    assert response.json()["value"] == 25.0


def test_get_readings_history(client, auth_headers, db_session):
    """Add readings and verify history endpoint returns statistics.

    Args:
        client: Test HTTP client.
        auth_headers: Authorization headers with valid JWT.
        db_session: Test database session.
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

    sensor = Sensor(
        device_id=device_id, sensor_type_id=1, name="Temp", unit="°C"
    )
    db_session.add(sensor)
    db_session.commit()
    db_session.refresh(sensor)

    # Add readings via API
    client.post(
        f"{API}/sensors/{sensor.id}/readings",
        json={"value": 20.0},
        headers=auth_headers,
    )
    client.post(
        f"{API}/sensors/{sensor.id}/readings",
        json={"value": 30.0},
        headers=auth_headers,
    )

    response = client.get(
        f"{API}/sensors/{sensor.id}/readings",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert "statistics" in data
    stats = data["statistics"]
    assert stats["min"] == 20.0
    assert stats["max"] == 30.0
    assert stats["avg"] == 25.0
