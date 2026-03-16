"""Tests for greenhouse CRUD endpoints."""

API = "/api/v1"


def test_create_greenhouse(client, auth_headers):
    """Create a greenhouse and verify 201 response.

    Args:
        client: Test HTTP client.
        auth_headers: Authorization headers with valid JWT.
    """
    response = client.post(
        f"{API}/greenhouses",
        json={"name": "My Greenhouse", "location": "Backyard"},
        headers=auth_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "My Greenhouse"
    assert data["location"] == "Backyard"
    assert "id" in data


def test_list_greenhouses(client, auth_headers):
    """Create two greenhouses and verify the list returns total=2.

    Args:
        client: Test HTTP client.
        auth_headers: Authorization headers with valid JWT.
    """
    client.post(
        f"{API}/greenhouses",
        json={"name": "GH-1", "location": "North"},
        headers=auth_headers,
    )
    client.post(
        f"{API}/greenhouses",
        json={"name": "GH-2", "location": "South"},
        headers=auth_headers,
    )

    response = client.get(f"{API}/greenhouses", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2


def test_get_greenhouse(client, auth_headers):
    """Retrieve a single greenhouse by ID.

    Args:
        client: Test HTTP client.
        auth_headers: Authorization headers with valid JWT.
    """
    create_resp = client.post(
        f"{API}/greenhouses",
        json={"name": "Detail GH", "location": "East"},
        headers=auth_headers,
    )
    gh_id = create_resp.json()["id"]

    response = client.get(f"{API}/greenhouses/{gh_id}", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["name"] == "Detail GH"


def test_update_greenhouse(client, auth_headers):
    """Update a greenhouse name and verify the change.

    Args:
        client: Test HTTP client.
        auth_headers: Authorization headers with valid JWT.
    """
    create_resp = client.post(
        f"{API}/greenhouses",
        json={"name": "Old Name", "location": "West"},
        headers=auth_headers,
    )
    gh_id = create_resp.json()["id"]

    response = client.put(
        f"{API}/greenhouses/{gh_id}",
        json={"name": "New Name"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["name"] == "New Name"


def test_delete_greenhouse(client, auth_headers):
    """Delete a greenhouse and verify 204 response.

    Args:
        client: Test HTTP client.
        auth_headers: Authorization headers with valid JWT.
    """
    create_resp = client.post(
        f"{API}/greenhouses",
        json={"name": "To Delete", "location": "Nowhere"},
        headers=auth_headers,
    )
    gh_id = create_resp.json()["id"]

    response = client.delete(f"{API}/greenhouses/{gh_id}", headers=auth_headers)
    assert response.status_code == 204
