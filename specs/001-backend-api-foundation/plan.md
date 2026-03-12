# Implementation Plan: Backend API — Умная Теплица

**Branch**: `001-backend-api-foundation` | **Date**: 2026-03-10 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-backend-api-foundation/spec.md`

## Summary

Полная реализация бэкенда IoT-системы умной теплицы: REST API (auth, CRUD теплиц/устройств/датчиков/актуаторов, дашборд, скрипты), MQTT-клиент (Paho-MQTT) для двустороннего обмена с ESP32-устройствами, WebSocket для real-time обновлений фронтенда, программный эмулятор IoT-устройств, контейнеризация через Docker Compose (PostgreSQL + Mosquitto + backend).

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: FastAPI, SQLAlchemy 2.0, Pydantic v2, Paho-MQTT, Alembic, uvicorn, passlib[bcrypt], python-jose[cryptography]
**Storage**: PostgreSQL 16 (Docker), 10 таблиц, 4 ENUM-типа
**Testing**: pytest + httpx (AsyncClient) + pytest-asyncio
**Target Platform**: Linux server (Docker container)
**Project Type**: web-service (REST API + WebSocket + MQTT client)
**Performance Goals**: health < 100ms, startup < 5s, MQTT latency < 2s, command response < 1s
**Constraints**: Без избыточного кода, умеренное разделение по пакетам, Google docstring на всё
**Scale/Scope**: 10+ устройств, 3 типа датчиков (temperature, humidity, light), 4 типа актуаторов (lighting, heating, ventilation, watering)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|---|---|---|
| I. Layered Architecture | ✅ PASS | Backend-only, communicates via MQTT (devices), REST/WS (frontend), SQL (DB) |
| II. MQTT-First Device Communication | ✅ PASS | Topics: `devices/{device_id}/{category}/{type}`, QoS 0/1 as specified |
| III. Containerized Services | ✅ PASS | Docker Compose: PostgreSQL + Mosquitto + backend, health checks |
| IV. Data Integrity & Persistence | ⚠️ GAP | DB schema lacks `status` field on actuator_commands (lifecycle: pending→sent→confirmed\|failed). Devices lack `last_seen`. Data retention policy deferred to P2. |
| V. Security by Default | ✅ PASS | JWT, bcrypt, Pydantic validation, ORM, CORS |
| VI. Simplicity & Pragmatism | ✅ PASS | No unnecessary abstractions, stdlib-first |
| VII. Observability & Monitoring | ⚠️ GAP | Need structured JSON logging, request logging middleware, MQTT event logging, health sub-endpoints |
| VIII. Device Resilience | ⚠️ GAP | Need `last_seen` on devices, reject commands to offline devices, LWT handling |
| IX. Contract Stability | ✅ PASS | Follows `docs/api_specification.md`, URL versioning `/api/v1/` |

### Gap Resolution

1. **Actuator command lifecycle** — добавить колонку `status VARCHAR(20) DEFAULT 'pending'` в `actuator_commands` через Alembic-миграцию. Lifecycle: pending → sent → confirmed | failed
2. **Device `last_seen`** — добавить колонку `last_seen TIMESTAMP WITH TIME ZONE` в `devices` через миграцию. Обновляется при получении MQTT-сообщения от устройства
3. **Structured logging** — настроить JSON-логирование через `logging.config.dictConfig`, middleware для request logging
4. **Health sub-endpoints** — `/health`, `/health/db`, `/health/mqtt`
5. **Data retention** — deferred to P2 (автоматическая очистка старых данных)

## Project Structure

### Documentation (this feature)

```text
specs/001-backend-api-foundation/
├── plan.md              # This file
├── spec.md              # Feature specification
├── research.md          # Phase 0: research findings
├── data-model.md        # Phase 1: entity model
├── quickstart.md        # Phase 1: dev setup guide
├── contracts/
│   └── api-routes.md    # Phase 1: API route contracts
└── checklists/
    └── requirements.md  # Spec quality checklist
```

### Source Code (repository root)

```text
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app, lifespan, middleware
│   ├── config.py            # Pydantic Settings
│   ├── database.py          # SQLAlchemy engine, session
│   ├── models.py            # All 10 ORM models
│   ├── schemas.py           # Pydantic request/response schemas
│   ├── dependencies.py      # get_db, get_current_user
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── auth.py          # register, login, refresh, me
│   │   ├── greenhouses.py   # CRUD теплиц
│   │   ├── devices.py       # CRUD устройств
│   │   ├── sensors.py       # датчики + показания
│   │   ├── actuators.py     # актуаторы + команды
│   │   ├── scripts.py       # скрипты автоматизации
│   │   ├── dashboard.py     # overview
│   │   ├── simulator.py     # start/stop/status
│   │   └── health.py        # health, health/db, health/mqtt
│   ├── mqtt/
│   │   ├── __init__.py
│   │   ├── client.py        # MQTTClient lifecycle, connect/reconnect
│   │   ├── topics.py        # Topic constants and helpers
│   │   └── handlers.py      # on_message handlers (sensors, status)
│   ├── simulator/
│   │   ├── __init__.py
│   │   ├── engine.py        # SimulatorEngine (asyncio task)
│   │   └── sensors.py       # Math models: temperature, humidity, light
│   └── websocket.py         # WS manager, broadcast
├── alembic/
│   ├── alembic.ini
│   ├── env.py
│   └── versions/
├── tests/
│   ├── conftest.py
│   ├── test_auth.py
│   ├── test_greenhouses.py
│   ├── test_devices.py
│   ├── test_sensors.py
│   ├── test_actuators.py
│   └── test_mqtt.py
├── requirements.txt
├── Dockerfile
└── .env.example
docker-compose.yml
```

**Structure Decision**: Flat module layout inside `backend/app/`. Routes separated by domain, MQTT and simulator as subpackages. No deep nesting, no service layer abstraction — route handlers call SQLAlchemy directly through dependency-injected sessions.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| `mqtt/` subpackage (3 files) | MQTT client lifecycle, topic routing, message handlers are distinct concerns | Single file would be 300+ lines mixing connection logic with business logic |
| `simulator/` subpackage (3 files) | Engine loop, sensor math models need separation | Single file would mix asyncio orchestration with math formulas |
