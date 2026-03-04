# Database Design

## Database Schema

### Entity Relationship Diagram

```
┌─────────────┐         ┌──────────────┐         ┌─────────────────┐
│   Users     │         │   Devices    │         │  SensorReadings │
├─────────────┤         ├──────────────┤         ├─────────────────┤
│ id (PK)     │         │ id (PK)      │────────<│ id (PK)         │
│ username    │         │ name         │         │ device_id (FK)  │
│ email       │         │ device_id    │         │ sensor_type     │
│ password    │         │ location     │         │ value           │
│ created_at  │         │ is_active    │         │ unit            │
│ updated_at  │         │ created_at   │         │ timestamp       │
└─────────────┘         │ updated_at   │         └─────────────────┘
                        └──────────────┘
                               │
                               │
                               │
                        ┌──────▼────────┐
                        │ActuatorCommands│
                        ├───────────────┤
                        │ id (PK)       │
                        │ device_id (FK)│
                        │ actuator_type │
                        │ command       │
                        │ status        │
                        │ executed_at   │
                        │ created_at    │
                        └───────────────┘
```

## Table Definitions

### 1. Users Table
Stores user authentication and profile information.

```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT true,
    is_superuser BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_email ON users(email);
```

**Columns:**
- `id`: Primary key (auto-increment)
- `username`: Unique username for login
- `email`: User email address
- `password_hash`: Hashed password (bcrypt/argon2)
- `is_active`: Account activation status
- `is_superuser`: Admin privileges flag
- `created_at`: Account creation timestamp
- `updated_at`: Last update timestamp

### 2. Devices Table
Stores IoT device information and metadata.

```sql
CREATE TABLE devices (
    id SERIAL PRIMARY KEY,
    device_id VARCHAR(100) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    location VARCHAR(255),
    device_type VARCHAR(50) DEFAULT 'greenhouse',
    is_active BOOLEAN DEFAULT true,
    is_online BOOLEAN DEFAULT false,
    last_seen TIMESTAMP WITH TIME ZONE,
    mqtt_client_id VARCHAR(100),
    config JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_devices_device_id ON devices(device_id);
CREATE INDEX idx_devices_is_active ON devices(is_active);
CREATE INDEX idx_devices_is_online ON devices(is_online);
```

**Columns:**
- `id`: Primary key (auto-increment)
- `device_id`: Unique device identifier (e.g., "greenhouse_01")
- `name`: Human-readable device name
- `description`: Device description
- `location`: Physical location
- `device_type`: Type of device (greenhouse, garden, etc.)
- `is_active`: Device activation status
- `is_online`: Current connectivity status
- `last_seen`: Last communication timestamp
- `mqtt_client_id`: MQTT client identifier
- `config`: Device-specific configuration (JSON)
- `created_at`: Device registration timestamp
- `updated_at`: Last update timestamp

### 3. SensorReadings Table
Stores historical sensor data (time-series data).

```sql
CREATE TABLE sensor_readings (
    id BIGSERIAL PRIMARY KEY,
    device_id INTEGER NOT NULL REFERENCES devices(id) ON DELETE CASCADE,
    sensor_type VARCHAR(50) NOT NULL,
    value NUMERIC(10, 2) NOT NULL,
    unit VARCHAR(20) NOT NULL,
    raw_data JSONB,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_sensor_readings_device_id ON sensor_readings(device_id);
CREATE INDEX idx_sensor_readings_sensor_type ON sensor_readings(sensor_type);
CREATE INDEX idx_sensor_readings_timestamp ON sensor_readings(timestamp DESC);
CREATE INDEX idx_sensor_readings_device_sensor_time
    ON sensor_readings(device_id, sensor_type, timestamp DESC);
```

**Columns:**
- `id`: Primary key (auto-increment, bigint for large datasets)
- `device_id`: Foreign key to devices table
- `sensor_type`: Type of sensor (light, temperature, humidity)
- `value`: Sensor reading value
- `unit`: Unit of measurement (°C, %, lux)
- `raw_data`: Additional sensor data (JSON)
- `timestamp`: Reading timestamp

**Sensor Types:**
- `light` - Light intensity (lux)
- `temperature` - Temperature (°C)
- `humidity` - Relative humidity (%)

### 4. ActuatorCommands Table
Stores actuator command history and execution status.

```sql
CREATE TABLE actuator_commands (
    id BIGSERIAL PRIMARY KEY,
    device_id INTEGER NOT NULL REFERENCES devices(id) ON DELETE CASCADE,
    actuator_type VARCHAR(50) NOT NULL,
    command VARCHAR(50) NOT NULL,
    parameters JSONB,
    status VARCHAR(20) DEFAULT 'pending',
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    executed_at TIMESTAMP WITH TIME ZONE,
    confirmed_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_actuator_commands_device_id ON actuator_commands(device_id);
CREATE INDEX idx_actuator_commands_status ON actuator_commands(status);
CREATE INDEX idx_actuator_commands_created_at ON actuator_commands(created_at DESC);
```

**Columns:**
- `id`: Primary key (auto-increment)
- `device_id`: Foreign key to devices table
- `actuator_type`: Type of actuator (lighting, heating, ventilation, watering)
- `command`: Command to execute (on, off, set_level)
- `parameters`: Additional command parameters (JSON)
- `status`: Execution status (pending, sent, confirmed, failed)
- `error_message`: Error details if failed
- `created_at`: Command creation timestamp
- `executed_at`: When command was sent to device
- `confirmed_at`: When device confirmed execution

**Actuator Types:**
- `lighting` - Lighting control
- `heating` - Heating control
- `ventilation` - Ventilation control
- `watering` - Irrigation control

**Command Status Flow:**
1. `pending` - Command created, not yet sent
2. `sent` - Published to MQTT, awaiting confirmation
3. `confirmed` - Device confirmed execution
4. `failed` - Execution failed

### 5. DeviceThresholds Table (Optional)
Stores threshold configurations for automated control.

```sql
CREATE TABLE device_thresholds (
    id SERIAL PRIMARY KEY,
    device_id INTEGER NOT NULL REFERENCES devices(id) ON DELETE CASCADE,
    sensor_type VARCHAR(50) NOT NULL,
    threshold_type VARCHAR(20) NOT NULL, -- 'min' or 'max'
    threshold_value NUMERIC(10, 2) NOT NULL,
    actuator_action JSONB NOT NULL,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(device_id, sensor_type, threshold_type)
);

CREATE INDEX idx_thresholds_device_id ON device_thresholds(device_id);
CREATE INDEX idx_thresholds_is_active ON device_thresholds(is_active);
```

**Example:**
- If temperature < 15°C → Turn on heating
- If humidity < 40% → Turn on watering
- If light > 10000 lux → Turn off lighting

## Sample Data

### Devices
```sql
INSERT INTO devices (device_id, name, location, is_active, is_online) VALUES
('greenhouse_01', 'Main Greenhouse', 'Building A, Section 1', true, true),
('greenhouse_02', 'Secondary Greenhouse', 'Building A, Section 2', true, false),
('greenhouse_03', 'Test Environment', 'Lab', true, true);
```

### Sensor Readings
```sql
INSERT INTO sensor_readings (device_id, sensor_type, value, unit) VALUES
(1, 'temperature', 22.5, '°C'),
(1, 'humidity', 65.0, '%'),
(1, 'light', 8500, 'lux');
```

### Actuator Commands
```sql
INSERT INTO actuator_commands (device_id, actuator_type, command, status) VALUES
(1, 'heating', 'on', 'confirmed'),
(1, 'lighting', 'off', 'confirmed'),
(1, 'watering', 'on', 'pending');
```

## Data Retention & Archival

### Sensor Readings Retention
- **Real-time data**: Keep last 7 days in full detail
- **Historical data**: Aggregate to hourly averages after 7 days
- **Long-term storage**: Monthly aggregates after 90 days

```sql
-- Create aggregated table for historical data
CREATE TABLE sensor_readings_hourly (
    id BIGSERIAL PRIMARY KEY,
    device_id INTEGER NOT NULL REFERENCES devices(id),
    sensor_type VARCHAR(50) NOT NULL,
    avg_value NUMERIC(10, 2),
    min_value NUMERIC(10, 2),
    max_value NUMERIC(10, 2),
    reading_count INTEGER,
    hour_timestamp TIMESTAMP WITH TIME ZONE NOT NULL
);

CREATE INDEX idx_sensor_hourly_device_time
    ON sensor_readings_hourly(device_id, hour_timestamp DESC);
```

### Cleanup Strategy
- Archive sensor readings older than 90 days
- Delete actuator commands older than 30 days (keep only aggregated stats)
- Implement automated cleanup job (cron/scheduled task)

## Performance Optimization

### Indexing Strategy
- Composite indexes for common query patterns
- Partial indexes for frequently filtered data
- Time-based partitioning for sensor_readings (future optimization)

### Query Optimization
- Use `EXPLAIN ANALYZE` for slow queries
- Materialized views for complex aggregations
- Connection pooling in application layer

### Scaling Considerations
- Table partitioning by time (monthly partitions for sensor_readings)
- Read replicas for analytics queries
- Consider TimescaleDB extension for time-series optimization

## Migration Strategy

### Using Alembic
```bash
# Create migration
alembic revision --autogenerate -m "Initial schema"

# Apply migration
alembic upgrade head

# Rollback
alembic downgrade -1
```

### Version Control
- All schema changes tracked in migrations
- Seed data scripts for development
- Database backup before migrations
