# Data Model: Backend API Foundation

**Source**: `docs/database_design.md`

## Entities

### User

| Field | Type | Constraints |
|-------|------|-------------|
| id | Serial PK | auto-increment |
| username | VARCHAR(50) | UNIQUE, NOT NULL |
| email | VARCHAR(255) | UNIQUE, NOT NULL |
| password_hash | VARCHAR(255) | NOT NULL |
| is_active | BOOLEAN | DEFAULT true |
| is_superuser | BOOLEAN | DEFAULT false |
| created_at | TIMESTAMPTZ | DEFAULT CURRENT_TIMESTAMP |
| updated_at | TIMESTAMPTZ | DEFAULT CURRENT_TIMESTAMP |

**Indexes**: username, email

### Device

| Field | Type | Constraints |
|-------|------|-------------|
| id | Serial PK | auto-increment |
| device_id | VARCHAR(100) | UNIQUE, NOT NULL |
| name | VARCHAR(255) | NOT NULL |
| description | TEXT | nullable |
| location | VARCHAR(255) | nullable |
| device_type | VARCHAR(50) | DEFAULT 'greenhouse' |
| is_active | BOOLEAN | DEFAULT true |
| is_online | BOOLEAN | DEFAULT false |
| last_seen | TIMESTAMPTZ | nullable |
| mqtt_client_id | VARCHAR(100) | nullable |
| config | JSONB | nullable |
| created_at | TIMESTAMPTZ | DEFAULT CURRENT_TIMESTAMP |
| updated_at | TIMESTAMPTZ | DEFAULT CURRENT_TIMESTAMP |

**Indexes**: device_id, is_active, is_online

### SensorReading

| Field | Type | Constraints |
|-------|------|-------------|
| id | BigSerial PK | auto-increment |
| device_id | INTEGER FK | NOT NULL, references devices(id) ON DELETE CASCADE |
| sensor_type | VARCHAR(50) | NOT NULL; enum: temperature, humidity, light |
| value | NUMERIC(10,2) | NOT NULL |
| unit | VARCHAR(20) | NOT NULL; °C, %, lux |
| raw_data | JSONB | nullable |
| timestamp | TIMESTAMPTZ | DEFAULT CURRENT_TIMESTAMP |

**Indexes**: device_id, sensor_type, timestamp DESC,
composite (device_id, sensor_type, timestamp DESC)

### ActuatorCommand

| Field | Type | Constraints |
|-------|------|-------------|
| id | BigSerial PK | auto-increment |
| device_id | INTEGER FK | NOT NULL, references devices(id) ON DELETE CASCADE |
| actuator_type | VARCHAR(50) | NOT NULL; enum: lighting, heating, ventilation, watering |
| command | VARCHAR(50) | NOT NULL; on, off, toggle, set_level |
| parameters | JSONB | nullable |
| status | VARCHAR(20) | DEFAULT 'pending'; enum: pending, sent, confirmed, failed |
| error_message | TEXT | nullable |
| created_at | TIMESTAMPTZ | DEFAULT CURRENT_TIMESTAMP |
| executed_at | TIMESTAMPTZ | nullable |
| confirmed_at | TIMESTAMPTZ | nullable |

**Indexes**: device_id, status, created_at DESC

## State Transitions

### ActuatorCommand.status

```
pending → sent → confirmed
                → failed
```

- `pending`: команда создана через API
- `sent`: опубликована в MQTT (вне скоупа этой фичи)
- `confirmed`: устройство подтвердило выполнение
- `failed`: ошибка на устройстве или таймаут

## Relationships

- Device → SensorReading: 1:N (CASCADE delete)
- Device → ActuatorCommand: 1:N (CASCADE delete)
- User: standalone (нет FK к другим сущностям в MVP)
