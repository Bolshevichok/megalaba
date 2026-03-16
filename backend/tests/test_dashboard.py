"""Tests for dashboard overview endpoint."""

from app.models import Sensor, SensorReading

API = "/api/v1"


def test_dashboard_overview(client, auth_headers, db_session):
    """Create greenhouse with device, sensor, and reading, then verify dashboard.

    Args:
        client: Test HTTP client.
        auth_headers: Authorization headers with valid JWT.
        db_session: Test database session.
    """
    resp = client.post(
        f"{API}/greenhouses",
        json={"name": "Dashboard GH", "location": "Lab"},
        headers=auth_headers,
    )
    gh_id = resp.json()["id"]

    resp = client.post(
        f"{API}/greenhouses/{gh_id}/devices",
        json={"name": "Dash Device", "connection_type": "wifi"},
        headers=auth_headers,
    )
    device_id = resp.json()["id"]

    sensor = Sensor(
        device_id=device_id, sensor_type_id=1, name="Temp", unit="°C"
    )
    db_session.add(sensor)
    db_session.commit()
    db_session.refresh(sensor)

    reading = SensorReading(sensor_id=sensor.id, value=22.5)
    db_session.add(reading)
    db_session.commit()

    response = client.get(
        f"{API}/dashboard/overview", headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert "summary" in data
    assert "greenhouses" in data
    assert len(data["greenhouses"]) >= 1
