# Data Model: Backend API — Умная Теплица

**Source**: `db_create.sql` + Constitution gaps (R6, R7 from research.md)

## ENUM Types

| Enum | Values |
|---|---|
| `connection_type_enum` | wifi, gsm, ethernet, zigbee |
| `device_status_enum` | online, offline |
| `actuator_status_enum` | on, off |
| `command_enum` | on, off, set_value |

## Entities

### User
| Field | Type | Constraints |
|---|---|---|
| id | SERIAL | PK |
| name | VARCHAR(100) | NOT NULL |
| email | VARCHAR(255) | UNIQUE, NOT NULL |
| password_hash | VARCHAR(255) | NOT NULL |
| billing_address | TEXT | nullable |
| phone | VARCHAR(20) | nullable |

### Greenhouse
| Field | Type | Constraints |
|---|---|---|
| id | SERIAL | PK |
| user_id | INTEGER | FK → users.id, ON DELETE CASCADE, NOT NULL |
| name | VARCHAR(100) | nullable |
| location | VARCHAR(255) | nullable |

### Device
| Field | Type | Constraints |
|---|---|---|
| id | SERIAL | PK |
| greenhouse_id | INTEGER | FK → greenhouses.id, ON DELETE CASCADE, NOT NULL |
| name | VARCHAR(100) | nullable |
| connection_type | connection_type_enum | nullable |
| ip_address | VARCHAR(50) | nullable |
| status | device_status_enum | nullable |
| last_seen | TIMESTAMPTZ | nullable *(Constitution VIII — added via migration)* |

### SensorType
| Field | Type | Constraints |
|---|---|---|
| id | SERIAL | PK |
| name | VARCHAR(50) | nullable |

**Seed data**: temperature, humidity, light

### Sensor
| Field | Type | Constraints |
|---|---|---|
| id | SERIAL | PK |
| device_id | INTEGER | FK → devices.id, ON DELETE CASCADE, NOT NULL |
| sensor_type_id | INTEGER | FK → sensor_types.id, NOT NULL |
| name | VARCHAR(100) | nullable |
| unit | VARCHAR(20) | nullable |

### SensorReading
| Field | Type | Constraints |
|---|---|---|
| id | SERIAL | PK |
| sensor_id | INTEGER | FK → sensors.id, ON DELETE CASCADE, NOT NULL |
| value | FLOAT | nullable |
| recorded_at | TIMESTAMPTZ | DEFAULT CURRENT_TIMESTAMP |

**Index**: (sensor_id, recorded_at DESC) — для быстрых запросов истории

### ActuatorType
| Field | Type | Constraints |
|---|---|---|
| id | SERIAL | PK |
| name | VARCHAR(50) | nullable |

**Seed data**: lighting, heating, ventilation, watering

### Actuator
| Field | Type | Constraints |
|---|---|---|
| id | SERIAL | PK |
| device_id | INTEGER | FK → devices.id, ON DELETE CASCADE, NOT NULL |
| actuator_type_id | INTEGER | FK → actuator_types.id, NOT NULL |
| status | actuator_status_enum | nullable |

### ActuatorCommand
| Field | Type | Constraints |
|---|---|---|
| id | SERIAL | PK |
| actuator_id | INTEGER | FK → actuators.id, ON DELETE CASCADE, NOT NULL |
| command | command_enum | NOT NULL |
| value | FLOAT | nullable |
| status | VARCHAR(20) | DEFAULT 'pending' *(Constitution IV — added via migration)* |
| created_at | TIMESTAMPTZ | DEFAULT CURRENT_TIMESTAMP |

**Lifecycle**: pending → sent → confirmed | failed

### Script
| Field | Type | Constraints |
|---|---|---|
| id | SERIAL | PK |
| greenhouse_id | INTEGER | FK → greenhouses.id, ON DELETE CASCADE, NOT NULL |
| name | VARCHAR(100) | nullable |
| script_code | TEXT | nullable |
| enabled | BOOLEAN | DEFAULT TRUE |

## Relationships

```
User (1) ──→ (N) Greenhouse
Greenhouse (1) ──→ (N) Device
Greenhouse (1) ──→ (N) Script
Device (1) ──→ (N) Sensor
Device (1) ──→ (N) Actuator
Sensor (N) ──→ (1) SensorType
Sensor (1) ──→ (N) SensorReading
Actuator (N) ──→ (1) ActuatorType
Actuator (1) ──→ (N) ActuatorCommand
```

## State Transitions

### Device Status
```
(created) → offline
offline → online  [MQTT message received from device]
online → offline  [LWT received OR last_seen > 60s]
```

### Actuator Status
```
off → on   [command "on" confirmed]
on → off   [command "off" confirmed]
```

### ActuatorCommand Lifecycle
```
pending → sent       [published to MQTT]
sent → confirmed     [status message from ESP32]
sent → failed        [timeout 30s without confirmation]
```

## Differences from db_create.sql

Two columns added via Alembic migration to satisfy Constitution:

1. `devices.last_seen` (TIMESTAMPTZ, nullable) — Constitution VIII: Device Resilience
2. `actuator_commands.status` (VARCHAR(20), DEFAULT 'pending') — Constitution IV: Data Integrity
