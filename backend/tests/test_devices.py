"""Tests for device CRUD endpoints."""

API = "/api/v1"


def _create_greenhouse(client, auth_headers):
    """Create a greenhouse and return its ID.

    Args:
        client: Test HTTP client.
        auth_headers: Authorization headers with valid JWT.

    Returns:
        int: The created greenhouse ID.
    """
    resp = client.post(
        f"{API}/greenhouses",
        json={"name": "Test GH", "location": "Lab"},
        headers=auth_headers,
    )
    return resp.json()["id"]


def test_create_device(client, auth_headers):
    """Create a device inside a greenhouse and verify 201.

    Args:
        client: Test HTTP client.
        auth_headers: Authorization headers with valid JWT.
    """
    gh_id = _create_greenhouse(client, auth_headers)

    response = client.post(
        f"{API}/greenhouses/{gh_id}/devices",
        json={"name": "Sensor Hub", "connection_type": "wifi"},
        headers=auth_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Sensor Hub"
    assert "id" in data


def test_list_devices(client, auth_headers):
    """Create two devices and verify the list returns total=2.

    Args:
        client: Test HTTP client.
        auth_headers: Authorization headers with valid JWT.
    """
    gh_id = _create_greenhouse(client, auth_headers)

    client.post(
        f"{API}/greenhouses/{gh_id}/devices",
        json={"name": "Device-1", "connection_type": "wifi"},
        headers=auth_headers,
    )
    client.post(
        f"{API}/greenhouses/{gh_id}/devices",
        json={"name": "Device-2", "connection_type": "ethernet"},
        headers=auth_headers,
    )

    response = client.get(
        f"{API}/greenhouses/{gh_id}/devices", headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2


def test_get_device_detail(client, auth_headers):
    """Retrieve a single device by ID.

    Args:
        client: Test HTTP client.
        auth_headers: Authorization headers with valid JWT.
    """
    gh_id = _create_greenhouse(client, auth_headers)

    create_resp = client.post(
        f"{API}/greenhouses/{gh_id}/devices",
        json={"name": "Detail Device", "connection_type": "zigbee"},
        headers=auth_headers,
    )
    dev_id = create_resp.json()["id"]

    response = client.get(
        f"{API}/greenhouses/{gh_id}/devices/{dev_id}", headers=auth_headers
    )
    assert response.status_code == 200
    assert response.json()["name"] == "Detail Device"


def test_delete_device(client, auth_headers):
    """Delete a device and verify 204 response.

    Args:
        client: Test HTTP client.
        auth_headers: Authorization headers with valid JWT.
    """
    gh_id = _create_greenhouse(client, auth_headers)

    create_resp = client.post(
        f"{API}/greenhouses/{gh_id}/devices",
        json={"name": "To Delete", "connection_type": "gsm"},
        headers=auth_headers,
    )
    dev_id = create_resp.json()["id"]

    response = client.delete(
        f"{API}/greenhouses/{gh_id}/devices/{dev_id}", headers=auth_headers
    )
    assert response.status_code == 204
