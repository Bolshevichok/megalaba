# API Specification

## Base URL
```
Development: http://localhost:8000/api/v1
```

## Authentication

### JWT Token Authentication
All protected endpoints require a Bearer token:
```http
Authorization: Bearer <jwt_token>
```

### POST /auth/register
Register a new user.

**Request:**
```json
{
  "name": "Ivan Petrov",
  "email": "ivan@example.com",
  "password": "SecurePass123!",
  "phone": "+79001234567"
}
```

**Response:** `201 Created`
```json
{
  "id": 1,
  "name": "Ivan Petrov",
  "email": "ivan@example.com",
  "created_at": "2026-03-07T10:00:00Z"
}
```

### POST /auth/login

**Request:**
```json
{
  "email": "ivan@example.com",
  "password": "SecurePass123!"
}
```

**Response:** `200 OK`
```json
{
  "access_token": "eyJhbGci...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

### POST /auth/refresh

**Request:**
```json
{
  "refresh_token": "eyJhbGci..."
}
```

**Response:** `200 OK`
```json
{
  "access_token": "eyJhbGci...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

### GET /auth/me

**Response:** `200 OK`
```json
{
  "id": 1,
  "name": "Ivan Petrov",
  "email": "ivan@example.com",
  "phone": "+79001234567",
  "billing_address": null,
  "created_at": "2026-03-07T10:00:00Z"
}
```

---

## Greenhouses

### GET /greenhouses
List all greenhouses for the authenticated user.

**Response:** `200 OK`
```json
{
  "total": 2,
  "greenhouses": [
    {
      "id": 1,
      "name": "Main Greenhouse",
      "location": "Building A, Section 1",
      "device_count": 3,
      "online_device_count": 2,
      "created_at": "2026-03-01T10:00:00Z"
    }
  ]
}
```

### GET /greenhouses/{greenhouse_id}
Get greenhouse details with devices summary.

**Response:** `200 OK`
```json
{
  "id": 1,
  "name": "Main Greenhouse",
  "location": "Building A, Section 1",
  "devices": [
    {
      "id": 1,
      "name": "Zone 1 Controller",
      "connection_type": "wifi",
      "ip_address": "192.168.1.10",
      "status": "online",
      "sensor_count": 4,
      "actuator_count": 4
    }
  ],
  "scripts": [
    {
      "id": 1,
      "name": "Auto watering",
      "enabled": true
    }
  ],
  "created_at": "2026-03-01T10:00:00Z"
}
```

### POST /greenhouses
Create a new greenhouse.

**Request:**
```json
{
  "name": "New Greenhouse",
  "location": "Building B"
}
```

**Response:** `201 Created`

### PUT /greenhouses/{greenhouse_id}
Update greenhouse.

**Request:**
```json
{
  "name": "Updated Name",
  "location": "Updated Location"
}
```

**Response:** `200 OK`

### DELETE /greenhouses/{greenhouse_id}

**Response:** `204 No Content`

---

## Devices

### GET /greenhouses/{greenhouse_id}/devices
List devices in a greenhouse.

**Query Parameters:**
- `status` (string): Filter by status (`online`, `offline`)

**Response:** `200 OK`
```json
{
  "total": 2,
  "devices": [
    {
      "id": 1,
      "name": "Zone 1 Controller",
      "connection_type": "wifi",
      "ip_address": "192.168.1.10",
      "status": "online",
      "created_at": "2026-03-01T10:00:00Z"
    }
  ]
}
```

### GET /greenhouses/{greenhouse_id}/devices/{device_id}
Get device details with sensors and actuators.

**Response:** `200 OK`
```json
{
  "id": 1,
  "name": "Zone 1 Controller",
  "connection_type": "wifi",
  "ip_address": "192.168.1.10",
  "status": "online",
  "sensors": [
    {
      "id": 1,
      "name": "Air Temperature",
      "sensor_type": "temperature",
      "unit": "°C",
      "latest_value": 22.5,
      "latest_recorded_at": "2026-03-07T14:30:00Z"
    }
  ],
  "actuators": [
    {
      "id": 1,
      "actuator_type": "irrigation",
      "status": "off"
    }
  ]
}
```

### POST /greenhouses/{greenhouse_id}/devices
Create a new device.

**Request:**
```json
{
  "name": "Zone 3 Controller",
  "connection_type": "wifi",
  "ip_address": "192.168.1.12"
}
```

**Response:** `201 Created`

### PUT /greenhouses/{greenhouse_id}/devices/{device_id}
Update device.

### DELETE /greenhouses/{greenhouse_id}/devices/{device_id}

**Response:** `204 No Content`

---

## Sensors

### GET /greenhouses/{greenhouse_id}/devices/{device_id}/sensors
List all sensors on a device with latest readings.

**Response:** `200 OK`
```json
{
  "sensors": [
    {
      "id": 1,
      "name": "Air Temperature",
      "sensor_type": "temperature",
      "unit": "°C",
      "latest_value": 22.5,
      "latest_recorded_at": "2026-03-07T14:30:00Z"
    },
    {
      "id": 2,
      "name": "Air Humidity",
      "sensor_type": "humidity",
      "unit": "%",
      "latest_value": 65.0,
      "latest_recorded_at": "2026-03-07T14:30:00Z"
    }
  ]
}
```

### GET /sensors/{sensor_id}/readings
Get historical readings for a sensor.

**Query Parameters:**
- `start_time` (ISO 8601): Start of time range
- `end_time` (ISO 8601): End of time range
- `limit` (integer): Number of readings (default: 100, max: 1000)
- `aggregation` (string): `none`, `hourly`, `daily`

**Response:** `200 OK`
```json
{
  "sensor_id": 1,
  "sensor_type": "temperature",
  "unit": "°C",
  "readings": [
    {"value": 22.5, "recorded_at": "2026-03-07T14:30:00Z"},
    {"value": 22.3, "recorded_at": "2026-03-07T14:25:00Z"}
  ],
  "statistics": {
    "min": 22.3,
    "max": 22.5,
    "avg": 22.4,
    "count": 2
  }
}
```

### POST /sensors/{sensor_id}/readings
Manually add a sensor reading (for testing).

**Request:**
```json
{
  "value": 23.5,
  "recorded_at": "2026-03-07T15:00:00Z"
}
```

**Response:** `201 Created`

---

## Actuators

### GET /greenhouses/{greenhouse_id}/devices/{device_id}/actuators
Get all actuators on a device.

**Response:** `200 OK`
```json
{
  "actuators": [
    {
      "id": 1,
      "actuator_type": "irrigation",
      "status": "off",
      "last_command": {
        "command": "off",
        "value": null,
        "created_at": "2026-03-07T12:00:00Z"
      }
    },
    {
      "id": 2,
      "actuator_type": "ventilation",
      "status": "on",
      "last_command": {
        "command": "on",
        "value": null,
        "created_at": "2026-03-07T14:30:00Z"
      }
    }
  ]
}
```

### POST /actuators/{actuator_id}/commands
Send a command to an actuator. The backend saves the command to `actuator_commands`, then publishes it to the MQTT topic `devices/{device_id}/commands/{actuator_type}` for the ESP32 device.

**Request:**
```json
{
  "command": "set_value",
  "value": 75.0
}
```

**Response:** `202 Accepted`
```json
{
  "id": 123,
  "actuator_id": 1,
  "command": "set_value",
  "value": 75.0,
  "created_at": "2026-03-07T15:00:00Z"
}
```

**Supported commands:**
- `on` — turn actuator on (value: null)
- `off` — turn actuator off (value: null)
- `set_value` — set specific level (value: float, e.g. intensity %)

**MQTT flow:** Backend publishes to `devices/{device_id}/commands/{type}` → Mosquitto → ESP32 executes → ESP32 publishes status to `devices/{device_id}/status/{type}` → Backend updates actuator status.

### GET /actuators/{actuator_id}/commands
Get command history for an actuator.

**Query Parameters:**
- `start_time` (ISO 8601)
- `end_time` (ISO 8601)
- `limit` (integer, default: 100)

**Response:** `200 OK`
```json
{
  "actuator_id": 1,
  "actuator_type": "irrigation",
  "commands": [
    {
      "id": 123,
      "command": "set_value",
      "value": 75.0,
      "created_at": "2026-03-07T15:00:00Z"
    },
    {
      "id": 122,
      "command": "on",
      "value": null,
      "created_at": "2026-03-07T14:00:00Z"
    }
  ]
}
```

---

## Scripts

### GET /greenhouses/{greenhouse_id}/scripts
List automation scripts for a greenhouse.

**Response:** `200 OK`
```json
{
  "scripts": [
    {
      "id": 1,
      "name": "Auto watering",
      "enabled": true,
      "script_code": "if soil_moisture < 40: irrigation.on()"
    }
  ]
}
```

### POST /greenhouses/{greenhouse_id}/scripts
Create a new script.

**Request:**
```json
{
  "name": "Night lighting off",
  "script_code": "if hour > 22: lighting.off()",
  "enabled": true
}
```

**Response:** `201 Created`

### PUT /scripts/{script_id}
Update a script.

### DELETE /scripts/{script_id}

**Response:** `204 No Content`

---

## Dashboard

### GET /dashboard/overview
Get dashboard overview for the authenticated user.

**Response:** `200 OK`
```json
{
  "summary": {
    "total_greenhouses": 2,
    "total_devices": 5,
    "online_devices": 3,
    "offline_devices": 2
  },
  "greenhouses": [
    {
      "id": 1,
      "name": "Main Greenhouse",
      "devices": [
        {
          "id": 1,
          "name": "Zone 1 Controller",
          "status": "online",
          "current_readings": {
            "temperature": {"value": 22.5, "unit": "°C"},
            "humidity": {"value": 65.0, "unit": "%"},
            "light": {"value": 8500, "unit": "lux"},
            "soil_moisture": {"value": 58.0, "unit": "%"}
          },
          "actuator_status": {
            "irrigation": "off",
            "ventilation": "on",
            "lighting": "off",
            "heating": "off"
          }
        }
      ]
    }
  ]
}
```

---

## Simulator Control

### POST /simulator/start
Start the IoT device simulator.

**Response:** `200 OK`
```json
{"status": "running", "devices_count": 3}
```

### POST /simulator/stop
Stop the simulator.

**Response:** `200 OK`
```json
{"status": "stopped"}
```

### GET /simulator/status
Get simulator status.

**Response:** `200 OK`
```json
{
  "status": "running",
  "uptime_seconds": 3600,
  "devices_count": 3,
  "readings_generated": 12500
}
```

---

## WebSocket (Real-time Updates)

### Connection
```
ws://localhost:8000/ws/greenhouse/{greenhouse_id}
```

### Authentication
Send token in first message:
```json
{"type": "auth", "token": "Bearer eyJhbGci..."}
```

### Message Types

**Sensor Update:**
```json
{
  "type": "sensor_update",
  "sensor_id": 1,
  "sensor_type": "temperature",
  "value": 22.5,
  "unit": "°C",
  "recorded_at": "2026-03-07T15:00:00Z"
}
```

**Actuator Status Update:**
```json
{
  "type": "actuator_update",
  "actuator_id": 1,
  "actuator_type": "irrigation",
  "status": "on",
  "timestamp": "2026-03-07T15:00:00Z"
}
```

**Device Status:**
```json
{
  "type": "device_status",
  "device_id": 1,
  "status": "online",
  "timestamp": "2026-03-07T15:00:00Z"
}
```

---

## Error Responses

### Standard Error Format
```json
{
  "error": {
    "code": "DEVICE_NOT_FOUND",
    "message": "Device with ID 99 not found",
    "timestamp": "2026-03-07T15:00:00Z"
  }
}
```

### HTTP Status Codes
- `200 OK` — successful request
- `201 Created` — resource created
- `202 Accepted` — async processing (actuator commands)
- `204 No Content` — successful deletion
- `400 Bad Request` — invalid request data
- `401 Unauthorized` — authentication required
- `403 Forbidden` — insufficient permissions
- `404 Not Found` — resource not found
- `422 Unprocessable Entity` — validation error
- `500 Internal Server Error` — server error

### Error Codes
- `INVALID_CREDENTIALS` — invalid email/password
- `TOKEN_EXPIRED` — JWT token expired
- `GREENHOUSE_NOT_FOUND` — greenhouse doesn't exist
- `DEVICE_NOT_FOUND` — device doesn't exist
- `SENSOR_NOT_FOUND` — sensor doesn't exist
- `ACTUATOR_NOT_FOUND` — actuator doesn't exist
- `INVALID_COMMAND` — unsupported actuator command
- `VALIDATION_ERROR` — request validation failed

## Pagination

For list endpoints:
```
GET /greenhouses?limit=20&offset=0
```

**Response includes:**
```json
{
  "total": 50,
  "limit": 20,
  "offset": 0,
  "data": [...]
}
```

## API Versioning

- Current version: `v1`
- Version in URL: `/api/v1/...`
