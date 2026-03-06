-- =========================
-- ENUM типы
-- =========================

CREATE TYPE connection_type_enum AS ENUM (
    'wifi',
    'gsm',
    'ethernet',
    'zigbee'
);

CREATE TYPE device_status_enum AS ENUM (
    'online',
    'offline'
);

CREATE TYPE actuator_status_enum AS ENUM (
    'on',
    'off'
);

CREATE TYPE command_enum AS ENUM (
    'on',
    'off',
    'set_value'
);

-- =========================
-- users
-- =========================

CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100),
    password VARCHAR(255)
);

-- =========================
-- greenhouses
-- =========================

CREATE TABLE greenhouses (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    name VARCHAR(100),
    location VARCHAR(255),

    FOREIGN KEY (user_id)
        REFERENCES users(id)
        ON DELETE CASCADE
);

-- =========================
-- devices
-- =========================

CREATE TABLE devices (
    id SERIAL PRIMARY KEY,
    greenhouse_id INTEGER NOT NULL,
    name VARCHAR(100),
    connection_type connection_type_enum,
    ip_address VARCHAR(50),
    status device_status_enum,

    FOREIGN KEY (greenhouse_id)
        REFERENCES greenhouses(id)
        ON DELETE CASCADE
);

-- =========================
-- sensor_types
-- =========================

CREATE TABLE sensor_types (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50)
);

-- =========================
-- sensors
-- =========================

CREATE TABLE sensors (
    id SERIAL PRIMARY KEY,
    device_id INTEGER NOT NULL,
    sensor_type_id INTEGER NOT NULL,
    name VARCHAR(100),
    unit VARCHAR(20),

    FOREIGN KEY (device_id)
        REFERENCES devices(id)
        ON DELETE CASCADE,

    FOREIGN KEY (sensor_type_id)
        REFERENCES sensor_types(id)
);

-- =========================
-- sensor_readings
-- =========================

CREATE TABLE sensor_readings (
    id SERIAL PRIMARY KEY,
    sensor_id INTEGER NOT NULL,
    value FLOAT,
    recorded_at TIMESTAMP,

    FOREIGN KEY (sensor_id)
        REFERENCES sensors(id)
        ON DELETE CASCADE
);

-- =========================
-- actuator_types
-- =========================

CREATE TABLE actuator_types (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50)
);

-- =========================
-- actuators
-- =========================

CREATE TABLE actuators (
    id SERIAL PRIMARY KEY,
    device_id INTEGER NOT NULL,
    actuator_type_id INTEGER NOT NULL,
    status actuator_status_enum,

    FOREIGN KEY (device_id)
        REFERENCES devices(id)
        ON DELETE CASCADE,

    FOREIGN KEY (actuator_type_id)
        REFERENCES actuator_types(id)
);

-- =========================
-- actuator_commands
-- =========================

CREATE TABLE actuator_commands (
    id SERIAL PRIMARY KEY,
    actuator_id INTEGER NOT NULL,
    command command_enum,
    value FLOAT,

    FOREIGN KEY (actuator_id)
        REFERENCES actuators(id)
        ON DELETE CASCADE
);

-- =========================
-- scripts
-- =========================

CREATE TABLE scripts (
    id SERIAL PRIMARY KEY,
    greenhouse_id INTEGER NOT NULL,
    name VARCHAR(100),
    script_code TEXT,
    enabled BOOLEAN DEFAULT TRUE,

    FOREIGN KEY (greenhouse_id)
        REFERENCES greenhouses(id)
        ON DELETE CASCADE
);