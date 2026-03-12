# Проектирование базы данных

## Диаграмма сущностей

Схема основана на [ERD в Miro](https://miro.com/app/board/uXjVG71pso8=/?moveToWidget=3458764662603494169) с учётом выявленных исправлений.

```
┌──────────────┐       ┌───────────────┐       ┌──────────────┐
│    users     │       │  greenhouses  │       │   devices    │
├──────────────┤       ├───────────────┤       ├──────────────┤
│ id (PK)      │──1:N─►│ id (PK)       │──1:N─►│ id (PK)      │
│ name         │       │ name          │       │ greenhouse_id│
│ email        │       │ location      │       │ name         │
│ password_hash│       │ user_id (FK)  │       │ conn_type    │
│ billing_addr │       │ created_at    │       │ ip_address   │
│ phone        │       │ updated_at    │       │ status       │
│ created_at   │       └───────────────┘       │ created_at   │
│ updated_at   │              │                │ updated_at   │
└──────────────┘              │                └──────┬───────┘
                              │                   ┌───┴───┐
                              │                   │       │
                       ┌──────▼──────┐    ┌───────▼──┐  ┌─▼──────────┐
                       │  scripts    │    │ sensors  │  │ actuators  │
                       ├─────────────┤    ├──────────┤  ├────────────┤
                       │ id (PK)     │    │ id (PK)  │  │ id (PK)    │
                       │ greenhouse_ │    │ device_id│  │ device_id  │
                       │   id (FK)   │    │ type_id  │  │ type_id    │
                       │ name        │    │ name     │  │ status     │
                       │ script_code │    │ unit     │  └─────┬──────┘
                       │ enabled     │    └────┬─────┘        │
                       └─────────────┘         │              │
                                               │              │
┌────────────────┐                    ┌────────▼───────┐ ┌────▼──────────────┐
│  sensor_types  │───1:N──► sensors   │sensor_readings │ │actuator_commands  │
├────────────────┤                    ├────────────────┤ ├───────────────────┤
│ id (PK)        │                    │ id (PK)        │ │ id (PK)           │
│ name           │                    │ sensor_id (FK) │ │ actuator_id (FK)  │
└────────────────┘                    │ value          │ │ command           │
                                      │ recorded_at    │ │ value             │
┌────────────────┐                    └────────────────┘ │ created_at        │
│actuator_types  │───1:N──► actuators                    └───────────────────┘
├────────────────┤
│ id (PK)        │
│ name           │
└────────────────┘
```

## ENUM-типы

```sql
CREATE TYPE connection_type_enum AS ENUM ('wifi', 'gsm', 'ethernet', 'zigbee');
CREATE TYPE device_status_enum AS ENUM ('online', 'offline');
CREATE TYPE actuator_status_enum AS ENUM ('on', 'off');
CREATE TYPE command_enum AS ENUM ('on', 'off', 'set_value');
```

## Определения таблиц

### 1. users — Пользователи

```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    billing_address TEXT,
    phone VARCHAR(20),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_users_email ON users(email);
```

| Поле | Тип | Описание |
|---|---|---|
| `id` | SERIAL PK | Первичный ключ |
| `name` | VARCHAR(100) | Имя пользователя |
| `email` | VARCHAR(255) UNIQUE | Email (для аутентификации) |
| `password_hash` | VARCHAR(255) | Хеш пароля (bcrypt/argon2) |
| `billing_address` | TEXT | Адрес выставления счетов |
| `phone` | VARCHAR(20) | Телефон |
| `created_at` | TIMESTAMPTZ | Дата создания |
| `updated_at` | TIMESTAMPTZ | Дата обновления |

> **Исправление Miro**: поле `password` переименовано в `password_hash`, добавлено поле `email`.

### 2. greenhouses — Теплицы

```sql
CREATE TABLE greenhouses (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    location VARCHAR(255),
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_greenhouses_user_id ON greenhouses(user_id);
```

| Поле | Тип | Описание |
|---|---|---|
| `id` | SERIAL PK | Первичный ключ |
| `name` | VARCHAR(255) | Название теплицы |
| `location` | VARCHAR(255) | Местоположение |
| `user_id` | INTEGER FK | Владелец (→ users) |

### 3. devices — Устройства

```sql
CREATE TABLE devices (
    id SERIAL PRIMARY KEY,
    greenhouse_id INTEGER NOT NULL REFERENCES greenhouses(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    connection_type connection_type_enum NOT NULL,
    ip_address VARCHAR(45),
    status device_status_enum NOT NULL DEFAULT 'offline',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_devices_greenhouse_id ON devices(greenhouse_id);
CREATE INDEX idx_devices_status ON devices(status);
```

| Поле | Тип | Описание |
|---|---|---|
| `id` | SERIAL PK | Первичный ключ |
| `greenhouse_id` | INTEGER FK | Теплица (→ greenhouses) |
| `name` | VARCHAR(255) | Название устройства |
| `connection_type` | ENUM | Тип подключения (wifi, gsm, ethernet, zigbee) |
| `ip_address` | VARCHAR(45) | IP-адрес устройства |
| `status` | ENUM | Статус (online, offline) |

### 4. sensor_types — Справочник типов датчиков

```sql
CREATE TABLE sensor_types (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL
);
```

**Начальные данные:**
```sql
INSERT INTO sensor_types (name) VALUES
('temperature'), ('humidity'), ('soil_moisture'),
('light'), ('ph'), ('co2');
```

### 5. sensors — Датчики

```sql
CREATE TABLE sensors (
    id SERIAL PRIMARY KEY,
    device_id INTEGER NOT NULL REFERENCES devices(id) ON DELETE CASCADE,
    sensor_type_id INTEGER NOT NULL REFERENCES sensor_types(id),
    name VARCHAR(255) NOT NULL,
    unit VARCHAR(20) NOT NULL
);

CREATE INDEX idx_sensors_device_id ON sensors(device_id);
CREATE INDEX idx_sensors_type_id ON sensors(sensor_type_id);
```

| Поле | Тип | Описание |
|---|---|---|
| `id` | SERIAL PK | Первичный ключ |
| `device_id` | INTEGER FK | Устройство (→ devices) |
| `sensor_type_id` | INTEGER FK | Тип датчика (→ sensor_types) |
| `name` | VARCHAR(255) | Название датчика |
| `unit` | VARCHAR(20) | Единица измерения (°C, %, lux, ppm, pH) |

### 6. sensor_readings — Показания датчиков

```sql
CREATE TABLE sensor_readings (
    id BIGSERIAL PRIMARY KEY,
    sensor_id INTEGER NOT NULL REFERENCES sensors(id) ON DELETE CASCADE,
    value NUMERIC(10, 2) NOT NULL,
    recorded_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_readings_sensor_id ON sensor_readings(sensor_id);
CREATE INDEX idx_readings_recorded_at ON sensor_readings(recorded_at DESC);
CREATE INDEX idx_readings_sensor_time ON sensor_readings(sensor_id, recorded_at DESC);
```

| Поле | Тип | Описание |
|---|---|---|
| `id` | BIGSERIAL PK | Первичный ключ (bigint для таймсерий) |
| `sensor_id` | INTEGER FK | Датчик (→ sensors) |
| `value` | NUMERIC(10,2) | Значение показания |
| `recorded_at` | TIMESTAMPTZ | Время записи |

> **Исправление Miro**: тип `TIME` заменён на `TIMESTAMP`. Связь с sensors — **one-to-many** (не one-to-one).

### 7. actuator_types — Справочник типов актуаторов

```sql
CREATE TABLE actuator_types (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL
);
```

**Начальные данные:**
```sql
INSERT INTO actuator_types (name) VALUES
('irrigation'), ('ventilation'), ('lighting'), ('heating');
```

### 8. actuators — Актуаторы

```sql
CREATE TABLE actuators (
    id SERIAL PRIMARY KEY,
    device_id INTEGER NOT NULL REFERENCES devices(id) ON DELETE CASCADE,
    actuator_type_id INTEGER NOT NULL REFERENCES actuator_types(id),
    status actuator_status_enum NOT NULL DEFAULT 'off'
);

CREATE INDEX idx_actuators_device_id ON actuators(device_id);
CREATE INDEX idx_actuators_type_id ON actuators(actuator_type_id);
```

| Поле | Тип | Описание |
|---|---|---|
| `id` | SERIAL PK | Первичный ключ |
| `device_id` | INTEGER FK | Устройство (→ devices) |
| `actuator_type_id` | INTEGER FK | Тип актуатора (→ actuator_types) |
| `status` | ENUM | Текущий статус (on, off) |

### 9. actuator_commands — Команды актуаторов

```sql
CREATE TABLE actuator_commands (
    id BIGSERIAL PRIMARY KEY,
    actuator_id INTEGER NOT NULL REFERENCES actuators(id) ON DELETE CASCADE,
    command command_enum NOT NULL,
    value FLOAT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_commands_actuator_id ON actuator_commands(actuator_id);
CREATE INDEX idx_commands_created_at ON actuator_commands(created_at DESC);
```

| Поле | Тип | Описание |
|---|---|---|
| `id` | BIGSERIAL PK | Первичный ключ |
| `actuator_id` | INTEGER FK | Актуатор (→ actuators) |
| `command` | ENUM | Команда (on, off, set_value) |
| `value` | FLOAT NULL | Значение для set_value (nullable) |
| `created_at` | TIMESTAMPTZ | Время создания команды |

> **Исправление Miro**: добавлено поле `created_at`. `value` сделано nullable. Связь с actuators — **one-to-many** (не one-to-one).

### 10. scripts — Скрипты автоматизации

```sql
CREATE TABLE scripts (
    id SERIAL PRIMARY KEY,
    greenhouse_id INTEGER NOT NULL REFERENCES greenhouses(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    script_code TEXT NOT NULL,
    enabled BOOLEAN DEFAULT true
);

CREATE INDEX idx_scripts_greenhouse_id ON scripts(greenhouse_id);
```

| Поле | Тип | Описание |
|---|---|---|
| `id` | SERIAL PK | Первичный ключ |
| `greenhouse_id` | INTEGER FK | Теплица (→ greenhouses) |
| `name` | VARCHAR(255) | Название скрипта |
| `script_code` | TEXT | Код скрипта |
| `enabled` | BOOLEAN | Включён/выключен |

## Связи между таблицами

| Связь | Кардинальность | ON DELETE |
|---|---|---|
| users → greenhouses | one-to-many | CASCADE |
| greenhouses → devices | one-to-many | CASCADE |
| greenhouses → scripts | one-to-many | CASCADE |
| devices → sensors | one-to-many | CASCADE |
| devices → actuators | one-to-many | CASCADE |
| sensor_types → sensors | one-to-many | — |
| actuator_types → actuators | one-to-many | — |
| sensors → sensor_readings | **one-to-many** | CASCADE |
| actuators → actuator_commands | **one-to-many** | CASCADE |

## Тестовые данные

```sql
-- Пользователь
INSERT INTO users (name, email, password_hash, phone) VALUES
('Иван Петров', 'ivan@example.com', '$2b$12$...', '+79001234567');

-- Теплицы
INSERT INTO greenhouses (name, location, user_id) VALUES
('Основная теплица', 'Корпус А, Секция 1', 1),
('Экспериментальная', 'Лаборатория', 1);

-- Устройства
INSERT INTO devices (greenhouse_id, name, connection_type, ip_address, status) VALUES
(1, 'Контроллер зоны 1', 'wifi', '192.168.1.10', 'online'),
(1, 'Контроллер зоны 2', 'ethernet', '192.168.1.11', 'online'),
(2, 'Тестовый контроллер', 'wifi', '192.168.1.20', 'offline');

-- Датчики
INSERT INTO sensors (device_id, sensor_type_id, name, unit) VALUES
(1, 1, 'Температура воздуха', '°C'),
(1, 2, 'Влажность воздуха', '%'),
(1, 4, 'Освещённость', 'lux'),
(1, 3, 'Влажность почвы', '%');

-- Показания
INSERT INTO sensor_readings (sensor_id, value) VALUES
(1, 22.5), (2, 65.0), (3, 8500), (4, 58.0);

-- Актуаторы
INSERT INTO actuators (device_id, actuator_type_id, status) VALUES
(1, 1, 'off'), (1, 2, 'on'), (1, 3, 'off'), (1, 4, 'off');

-- Команды
INSERT INTO actuator_commands (actuator_id, command, value) VALUES
(2, 'on', NULL), (1, 'set_value', 75.0);
```

## Хранение и архивация данных

### Стратегия ретеншена для sensor_readings
- **Детальные данные**: хранить последние 7 дней
- **Почасовые агрегаты**: после 7 дней
- **Суточные агрегаты**: после 90 дней

### Оптимизация производительности
- Составные индексы для частых запросов (sensor_id + recorded_at)
- BIGSERIAL для таблиц с большим объёмом данных
- Партиционирование по времени (на будущее)
- TimescaleDB как опция для таймсерий

## Миграции (Alembic)

```bash
cd backend
alembic revision --autogenerate -m "Initial schema with Miro ERD"
alembic upgrade head
alembic downgrade -1   # откат
```
