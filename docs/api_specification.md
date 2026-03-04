# API Specification

## Base URL
```
Development: http://localhost:8000/api/v1
Production: https://api.greenhouse.example.com/api/v1
```

## Authentication

### JWT Token Authentication
All protected endpoints require a Bearer token in the Authorization header:

```http
Authorization: Bearer <jwt_token>
```

### Auth Endpoints

#### POST /auth/register
Register a new user account.

**Request:**
```json
{
  "username": "user123",
  "email": "user@example.com",
  "password": "SecurePass123!"
}
```

**Response:** `201 Created`
```json
{
  "id": 1,
  "username": "user123",
  "email": "user@example.com",
  "is_active": true,
  "created_at": "2025-01-15T10:00:00Z"
}
```

#### POST /auth/login
Authenticate and receive JWT token.

**Request:**
```json
{
  "username": "user123",
  "password": "SecurePass123!"
}
```

**Response:** `200 OK`
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

#### POST /auth/refresh
Refresh JWT token.

**Request:**
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response:** `200 OK`
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

## Device Management

#### GET /devices
List all devices.

**Query Parameters:**
- `is_active` (boolean): Filter by activation status
- `is_online` (boolean): Filter by online status
- `limit` (integer): Number of results (default: 100)
- `offset` (integer): Pagination offset (default: 0)

**Response:** `200 OK`
```json
{
  "total": 3,
  "limit": 100,
  "offset": 0,
  "devices": [
    {
      "id": 1,
      "device_id": "greenhouse_01",
      "name": "Main Greenhouse",
      "description": "Primary growing area",
      "location": "Building A, Section 1",
      "device_type": "greenhouse",
      "is_active": true,
      "is_online": true,
      "last_seen": "2025-01-15T14:30:00Z",
      "created_at": "2025-01-01T10:00:00Z",
      "updated_at": "2025-01-15T14:30:00Z"
    }
  ]
}
```

#### GET /devices/{device_id}
Get specific device details.

**Response:** `200 OK`
```json
{
  "id": 1,
  "device_id": "greenhouse_01",
  "name": "Main Greenhouse",
  "description": "Primary growing area",
  "location": "Building A, Section 1",
  "device_type": "greenhouse",
  "is_active": true,
  "is_online": true,
  "last_seen": "2025-01-15T14:30:00Z",
  "mqtt_client_id": "esp32_greenhouse_01",
  "config": {
    "wifi_strength": -45,
    "firmware_version": "1.0.0"
  },
  "created_at": "2025-01-01T10:00:00Z",
  "updated_at": "2025-01-15T14:30:00Z"
}
```

#### POST /devices
Register a new device.

**Request:**
```json
{
  "device_id": "greenhouse_03",
  "name": "Test Greenhouse",
  "description": "Testing environment",
  "location": "Lab",
  "device_type": "greenhouse"
}
```

**Response:** `201 Created`
```json
{
  "id": 3,
  "device_id": "greenhouse_03",
  "name": "Test Greenhouse",
  "is_active": true,
  "is_online": false,
  "created_at": "2025-01-15T15:00:00Z"
}
```

#### PUT /devices/{device_id}
Update device information.

**Request:**
```json
{
  "name": "Updated Greenhouse Name",
  "location": "New Location",
  "is_active": true
}
```

**Response:** `200 OK`
```json
{
  "id": 1,
  "device_id": "greenhouse_01",
  "name": "Updated Greenhouse Name",
  "location": "New Location",
  "updated_at": "2025-01-15T15:30:00Z"
}
```

#### DELETE /devices/{device_id}
Deactivate a device.

**Response:** `204 No Content`

## Sensor Data

#### GET /devices/{device_id}/sensors
Get latest sensor readings for all sensors on a device.

**Response:** `200 OK`
```json
{
  "device_id": "greenhouse_01",
  "readings": [
    {
      "sensor_type": "temperature",
      "value": 22.5,
      "unit": "°C",
      "timestamp": "2025-01-15T14:30:00Z"
    },
    {
      "sensor_type": "humidity",
      "value": 65.0,
      "unit": "%",
      "timestamp": "2025-01-15T14:30:00Z"
    },
    {
      "sensor_type": "light",
      "value": 8500,
      "unit": "lux",
      "timestamp": "2025-01-15T14:30:00Z"
    }
  ]
}
```

#### GET /devices/{device_id}/sensors/{sensor_type}
Get specific sensor readings.

**Query Parameters:**
- `start_time` (ISO 8601 datetime): Start of time range
- `end_time` (ISO 8601 datetime): End of time range
- `limit` (integer): Number of readings (default: 100, max: 1000)
- `aggregation` (string): Aggregation type (none, hourly, daily)

**Response:** `200 OK`
```json
{
  "device_id": "greenhouse_01",
  "sensor_type": "temperature",
  "unit": "°C",
  "readings": [
    {
      "value": 22.5,
      "timestamp": "2025-01-15T14:30:00Z"
    },
    {
      "value": 22.3,
      "timestamp": "2025-01-15T14:25:00Z"
    },
    {
      "value": 22.1,
      "timestamp": "2025-01-15T14:20:00Z"
    }
  ],
  "statistics": {
    "min": 22.1,
    "max": 22.5,
    "avg": 22.3,
    "count": 3
  }
}
```

#### POST /devices/{device_id}/sensors/{sensor_type}
Manually add a sensor reading (for testing/manual input).

**Request:**
```json
{
  "value": 23.5,
  "timestamp": "2025-01-15T15:00:00Z"
}
```

**Response:** `201 Created`
```json
{
  "id": 12345,
  "device_id": "greenhouse_01",
  "sensor_type": "temperature",
  "value": 23.5,
  "unit": "°C",
  "timestamp": "2025-01-15T15:00:00Z"
}
```

## Actuator Control

#### GET /devices/{device_id}/actuators
Get current status of all actuators.

**Response:** `200 OK`
```json
{
  "device_id": "greenhouse_01",
  "actuators": [
    {
      "actuator_type": "lighting",
      "status": "on",
      "last_command": "2025-01-15T14:00:00Z",
      "last_update": "2025-01-15T14:00:05Z"
    },
    {
      "actuator_type": "heating",
      "status": "off",
      "last_command": "2025-01-15T13:00:00Z",
      "last_update": "2025-01-15T13:00:03Z"
    },
    {
      "actuator_type": "ventilation",
      "status": "on",
      "last_command": "2025-01-15T14:30:00Z",
      "last_update": "2025-01-15T14:30:02Z"
    },
    {
      "actuator_type": "watering",
      "status": "off",
      "last_command": "2025-01-15T12:00:00Z",
      "last_update": "2025-01-15T12:00:04Z"
    }
  ]
}
```

#### POST /devices/{device_id}/actuators/{actuator_type}
Send command to an actuator.

**Request:**
```json
{
  "command": "on",
  "parameters": {
    "duration": 300,
    "intensity": 80
  }
}
```

**Response:** `202 Accepted`
```json
{
  "command_id": 5678,
  "device_id": "greenhouse_01",
  "actuator_type": "heating",
  "command": "on",
  "status": "pending",
  "created_at": "2025-01-15T15:00:00Z"
}
```

**Supported Commands:**
- `on` - Turn actuator on
- `off` - Turn actuator off
- `toggle` - Toggle current state
- `set_level` - Set specific level (with parameters)

#### GET /devices/{device_id}/actuators/{actuator_type}/history
Get actuator command history.

**Query Parameters:**
- `start_time` (ISO 8601 datetime): Start of time range
- `end_time` (ISO 8601 datetime): End of time range
- `status` (string): Filter by status (pending, sent, confirmed, failed)
- `limit` (integer): Number of commands (default: 100)

**Response:** `200 OK`
```json
{
  "device_id": "greenhouse_01",
  "actuator_type": "heating",
  "commands": [
    {
      "id": 5678,
      "command": "on",
      "status": "confirmed",
      "created_at": "2025-01-15T15:00:00Z",
      "executed_at": "2025-01-15T15:00:01Z",
      "confirmed_at": "2025-01-15T15:00:03Z"
    },
    {
      "id": 5677,
      "command": "off",
      "status": "confirmed",
      "created_at": "2025-01-15T14:00:00Z",
      "executed_at": "2025-01-15T14:00:01Z",
      "confirmed_at": "2025-01-15T14:00:02Z"
    }
  ]
}
```

## Dashboard & Analytics

#### GET /dashboard/overview
Get dashboard overview with current status of all devices.

**Response:** `200 OK`
```json
{
  "summary": {
    "total_devices": 3,
    "online_devices": 2,
    "offline_devices": 1,
    "active_alerts": 0
  },
  "devices": [
    {
      "device_id": "greenhouse_01",
      "name": "Main Greenhouse",
      "is_online": true,
      "current_readings": {
        "temperature": {"value": 22.5, "unit": "°C"},
        "humidity": {"value": 65.0, "unit": "%"},
        "light": {"value": 8500, "unit": "lux"}
      },
      "actuator_status": {
        "lighting": "on",
        "heating": "off",
        "ventilation": "on",
        "watering": "off"
      }
    }
  ]
}
```

#### GET /devices/{device_id}/analytics
Get analytics and statistics for a device.

**Query Parameters:**
- `metric` (string): temperature, humidity, light, all
- `period` (string): 24h, 7d, 30d, 90d
- `aggregation` (string): hourly, daily

**Response:** `200 OK`
```json
{
  "device_id": "greenhouse_01",
  "period": "24h",
  "metrics": {
    "temperature": {
      "current": 22.5,
      "min": 18.2,
      "max": 26.8,
      "avg": 22.1,
      "trend": "stable",
      "data_points": [
        {"timestamp": "2025-01-15T00:00:00Z", "value": 20.5},
        {"timestamp": "2025-01-15T01:00:00Z", "value": 20.1}
      ]
    },
    "humidity": {
      "current": 65.0,
      "min": 55.0,
      "max": 75.0,
      "avg": 64.5,
      "trend": "increasing"
    }
  }
}
```

## WebSocket (Real-time Updates)

### Connection
```javascript
ws://localhost:8000/ws/devices/{device_id}
```

### Authentication
Send token in first message:
```json
{
  "type": "auth",
  "token": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

### Message Types

#### Sensor Update
```json
{
  "type": "sensor_update",
  "device_id": "greenhouse_01",
  "sensor_type": "temperature",
  "value": 22.5,
  "unit": "°C",
  "timestamp": "2025-01-15T15:00:00Z"
}
```

#### Actuator Status Update
```json
{
  "type": "actuator_update",
  "device_id": "greenhouse_01",
  "actuator_type": "heating",
  "status": "on",
  "timestamp": "2025-01-15T15:00:00Z"
}
```

#### Device Connection Status
```json
{
  "type": "device_status",
  "device_id": "greenhouse_01",
  "is_online": true,
  "timestamp": "2025-01-15T15:00:00Z"
}
```

## Error Responses

### Standard Error Format
```json
{
  "error": {
    "code": "DEVICE_NOT_FOUND",
    "message": "Device with ID 'greenhouse_99' not found",
    "details": {},
    "timestamp": "2025-01-15T15:00:00Z"
  }
}
```

### HTTP Status Codes
- `200 OK` - Successful request
- `201 Created` - Resource created
- `202 Accepted` - Request accepted (async processing)
- `204 No Content` - Successful deletion
- `400 Bad Request` - Invalid request data
- `401 Unauthorized` - Authentication required
- `403 Forbidden` - Insufficient permissions
- `404 Not Found` - Resource not found
- `409 Conflict` - Resource conflict
- `422 Unprocessable Entity` - Validation error
- `500 Internal Server Error` - Server error
- `503 Service Unavailable` - Service temporarily unavailable

### Common Error Codes
- `INVALID_CREDENTIALS` - Invalid username/password
- `TOKEN_EXPIRED` - JWT token expired
- `DEVICE_NOT_FOUND` - Device doesn't exist
- `DEVICE_OFFLINE` - Device not connected
- `INVALID_COMMAND` - Unsupported actuator command
- `VALIDATION_ERROR` - Request validation failed
- `MQTT_ERROR` - MQTT communication error

## Rate Limiting

- **Default**: 100 requests per minute per IP
- **Authenticated**: 1000 requests per minute per user
- **WebSocket**: 100 messages per minute per connection

**Headers:**
```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 995
X-RateLimit-Reset: 1642252800
```

## Pagination

For list endpoints, use `limit` and `offset`:
```
GET /devices?limit=20&offset=40
```

**Response includes:**
```json
{
  "total": 150,
  "limit": 20,
  "offset": 40,
  "data": [...]
}
```

## API Versioning

- Current version: `v1`
- Version specified in URL: `/api/v1/...`
- Breaking changes require new version
