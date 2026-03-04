# API Routes Contract

**Source**: `docs/api_specification.md`
**Base URL**: `/api/v1`

## Health

| Method | Path | Auth | Response | Description |
|--------|------|------|----------|-------------|
| GET | /health | No | 200 `{status, db, timestamp}` | Service health check |

## Auth

| Method | Path | Auth | Request Body | Response | Description |
|--------|------|------|-------------|----------|-------------|
| POST | /auth/register | No | `{username, email, password}` | 201 `{id, username, email, is_active, created_at}` | Register user |
| POST | /auth/login | No | `{username, password}` | 200 `{access_token, token_type, expires_in}` | Login |
| POST | /auth/refresh | No | `{refresh_token}` | 200 `{access_token, token_type, expires_in}` | Refresh token |

## Devices

| Method | Path | Auth | Request Body | Response | Description |
|--------|------|------|-------------|----------|-------------|
| GET | /devices | Yes | — | 200 `{total, limit, offset, devices[]}` | List devices (pagination: limit, offset; filters: is_active, is_online) |
| GET | /devices/{device_id} | Yes | — | 200 `Device` | Get single device |
| POST | /devices | Yes | `{device_id, name, description?, location?, device_type?}` | 201 `Device` | Create device |
| PUT | /devices/{device_id} | Yes | `{name?, location?, is_active?}` | 200 `Device` | Update device |
| DELETE | /devices/{device_id} | Yes | — | 204 | Deactivate device |

## Sensors

| Method | Path | Auth | Query Params | Response | Description |
|--------|------|------|-------------|----------|-------------|
| GET | /devices/{device_id}/sensors | Yes | — | 200 `{device_id, readings[]}` | Latest readings all sensors |
| GET | /devices/{device_id}/sensors/{sensor_type} | Yes | start_time, end_time, limit, aggregation | 200 `{device_id, sensor_type, unit, readings[], statistics}` | Historical sensor data |
| POST | /devices/{device_id}/sensors/{sensor_type} | Yes | — | 201 `SensorReading` | Manual sensor entry |

**sensor_type**: `temperature`, `humidity`, `light`

## Actuators

| Method | Path | Auth | Request Body | Response | Description |
|--------|------|------|-------------|----------|-------------|
| GET | /devices/{device_id}/actuators | Yes | — | 200 `{device_id, actuators[]}` | All actuator statuses |
| POST | /devices/{device_id}/actuators/{actuator_type} | Yes | `{command, parameters?}` | 202 `{command_id, device_id, actuator_type, command, status, created_at}` | Send command |
| GET | /devices/{device_id}/actuators/{actuator_type}/history | Yes | start_time, end_time, status, limit | 200 `{device_id, actuator_type, commands[]}` | Command history |

**actuator_type**: `lighting`, `heating`, `ventilation`, `watering`
**command**: `on`, `off`, `toggle`, `set_level`

## Dashboard

| Method | Path | Auth | Response | Description |
|--------|------|------|----------|-------------|
| GET | /dashboard/overview | Yes | 200 `{summary, devices[]}` | System overview |

## Error Contract

All errors return:
```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable message",
    "details": {},
    "timestamp": "ISO 8601"
  }
}
```

**Status codes**: 400, 401, 403, 404, 409, 422, 500, 503
