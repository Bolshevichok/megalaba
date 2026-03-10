# API Routes Contract

**Source**: `docs/api_specification.md`
**Base URL**: `/api/v1`

## Health

| Method | Path | Auth | Response | Description |
|--------|------|------|----------|-------------|
| GET | /health | No | 200 `{status, db, mqtt, timestamp}` | Service health check |
| GET | /health/db | No | 200 `{status, latency_ms}` | Database health |
| GET | /health/mqtt | No | 200 `{status, connected}` | MQTT broker health |

## Auth

| Method | Path | Auth | Request Body | Response | Description |
|--------|------|------|-------------|----------|-------------|
| POST | /auth/register | No | `{name, email, password, phone?}` | 201 `{id, name, email, created_at}` | Register user |
| POST | /auth/login | No | `{email, password}` | 200 `{access_token, token_type, expires_in}` | Login |
| POST | /auth/refresh | No | `{refresh_token}` | 200 `{access_token, token_type, expires_in}` | Refresh token |
| GET | /auth/me | Yes | — | 200 `{id, name, email, phone, billing_address}` | Current user profile |

## Greenhouses

| Method | Path | Auth | Request Body | Response | Description |
|--------|------|------|-------------|----------|-------------|
| GET | /greenhouses | Yes | — | 200 `{total, greenhouses[]}` | List user's greenhouses |
| GET | /greenhouses/{id} | Yes | — | 200 `Greenhouse` with devices[], scripts[] | Get greenhouse details |
| POST | /greenhouses | Yes | `{name, location?}` | 201 `Greenhouse` | Create greenhouse |
| PUT | /greenhouses/{id} | Yes | `{name?, location?}` | 200 `Greenhouse` | Update greenhouse |
| DELETE | /greenhouses/{id} | Yes | — | 204 | Delete greenhouse (cascade) |

## Devices

| Method | Path | Auth | Query Params | Response | Description |
|--------|------|------|-------------|----------|-------------|
| GET | /greenhouses/{id}/devices | Yes | status | 200 `{total, devices[]}` | List devices (filter by status) |
| GET | /greenhouses/{gid}/devices/{did} | Yes | — | 200 `Device` with sensors[], actuators[] | Device details |
| POST | /greenhouses/{id}/devices | Yes | `{name, connection_type?, ip_address?}` | 201 `Device` | Create device |
| PUT | /greenhouses/{gid}/devices/{did} | Yes | `{name?, connection_type?, ip_address?}` | 200 `Device` | Update device |
| DELETE | /greenhouses/{gid}/devices/{did} | Yes | — | 204 | Delete device (cascade) |

## Sensors

| Method | Path | Auth | Query Params | Response | Description |
|--------|------|------|-------------|----------|-------------|
| GET | /greenhouses/{gid}/devices/{did}/sensors | Yes | — | 200 `{sensors[]}` | List sensors with latest readings |
| GET | /sensors/{id}/readings | Yes | start_time, end_time, limit, aggregation | 200 `{sensor_id, sensor_type, unit, readings[], statistics}` | Historical readings |
| POST | /sensors/{id}/readings | Yes | `{value, recorded_at?}` | 201 `SensorReading` | Manual reading (testing) |

**sensor_type**: `temperature`, `humidity`, `light`

## Actuators

| Method | Path | Auth | Request Body | Response | Description |
|--------|------|------|-------------|----------|-------------|
| GET | /greenhouses/{gid}/devices/{did}/actuators | Yes | — | 200 `{actuators[]}` | All actuators with last_command |
| POST | /actuators/{id}/commands | Yes | `{command, value?}` | 202 `{id, actuator_id, command, value, status, created_at}` | Send command |
| GET | /actuators/{id}/commands | Yes | start_time, end_time, limit | 200 `{actuator_id, actuator_type, commands[]}` | Command history |

**actuator_type**: `lighting`, `heating`, `ventilation`, `watering`
**command**: `on`, `off`, `set_value`

## Scripts

| Method | Path | Auth | Request Body | Response | Description |
|--------|------|------|-------------|----------|-------------|
| GET | /greenhouses/{id}/scripts | Yes | — | 200 `{scripts[]}` | List scripts |
| POST | /greenhouses/{id}/scripts | Yes | `{name, script_code?, enabled?}` | 201 `Script` | Create script |
| PUT | /scripts/{id} | Yes | `{name?, script_code?, enabled?}` | 200 `Script` | Update script |
| DELETE | /scripts/{id} | Yes | — | 204 | Delete script |

## Dashboard

| Method | Path | Auth | Response | Description |
|--------|------|------|----------|-------------|
| GET | /dashboard/overview | Yes | 200 `{summary, greenhouses[]}` | System overview with readings & statuses |

## Simulator

| Method | Path | Auth | Response | Description |
|--------|------|------|----------|-------------|
| POST | /simulator/start | No | 200 `{status, devices_count}` | Start simulator |
| POST | /simulator/stop | No | 200 `{status}` | Stop simulator |
| GET | /simulator/status | No | 200 `{status, uptime_seconds, devices_count, readings_generated}` | Simulator status |

## WebSocket

| Path | Auth | Description |
|------|------|-------------|
| /ws/greenhouse/{id} | Token in first message | Real-time updates for greenhouse |

**Message types**: `sensor_update`, `actuator_update`, `device_status`

## MQTT Topics

| Direction | Topic Pattern | Payload |
|-----------|--------------|---------|
| ESP32 → Backend | `devices/{device_id}/sensors/{type}` | `{"value": float, "unit": str, "timestamp": ISO8601}` |
| Backend → ESP32 | `devices/{device_id}/commands/{type}` | `{"command": "on\|off\|set_value", "value": float\|null}` |
| ESP32 → Backend | `devices/{device_id}/status/{type}` | `{"status": "on\|off", "timestamp": ISO8601}` |

## Error Contract

All errors return:
```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable message",
    "timestamp": "ISO 8601"
  }
}
```

**Status codes**: 400, 401, 403, 404, 422, 500, 503
**Error codes**: INVALID_CREDENTIALS, TOKEN_EXPIRED, GREENHOUSE_NOT_FOUND, DEVICE_NOT_FOUND, SENSOR_NOT_FOUND, ACTUATOR_NOT_FOUND, INVALID_COMMAND, VALIDATION_ERROR
