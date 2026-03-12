# Tasks: Backend API Foundation

**Input**: Design documents from `/specs/001-backend-api-foundation/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/

**Tests**: Constitution requires unit tests for services and integration tests for API endpoints. Test tasks included per phase.

**Organization**: Tasks grouped by user story for independent implementation.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: US1–US11 maps to spec.md user stories
- Exact file paths included in every task

## Phase 1: Setup

**Purpose**: Project initialization and dependency configuration

- [x] T000Create backend directory structure per plan.md: `backend/app/`, `backend/app/routes/`, `backend/app/mqtt/`, `backend/app/simulator/`, `backend/alembic/`, `backend/tests/`, all `__init__.py` files
- [x] T000[P] Create `backend/requirements.txt` with all dependencies: fastapi, uvicorn[standard], sqlalchemy, psycopg2-binary, pydantic, pydantic-settings, python-jose[cryptography], passlib[bcrypt], python-multipart, paho-mqtt, alembic, python-json-logger, httpx, pytest, pytest-asyncio
- [x] T000[P] Create `backend/app/config.py` — Pydantic Settings class with DATABASE_URL, SECRET_KEY, CORS_ORIGINS, ACCESS_TOKEN_EXPIRE_MINUTES, REFRESH_TOKEN_EXPIRE_DAYS, MQTT_BROKER_HOST, MQTT_BROKER_PORT, MQTT_USERNAME, MQTT_PASSWORD (see quickstart.md for defaults)
- [x] T000[P] Create `backend/.env.example` with all environment variables and example values per quickstart.md
- [x] T000[P] Create `backend/Dockerfile` — Python 3.11-slim, pip install requirements.txt, expose port 8000, CMD uvicorn
- [x] T000[P] Create `docker-compose.yml` at repo root — services: postgres (16-alpine, port 5432, named volume), mosquitto (2-alpine, port 1883, config volume), backend (build from backend/, depends_on postgres+mosquitto, env_file)
- [x] T000[P] Create linting config: `backend/pyproject.toml` with ruff settings (line-length=120, select=E,F,W,I) and mypy settings (strict=false, ignore_missing_imports=true); add ruff and mypy to requirements.txt

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story

**CRITICAL**: No user story work can begin until this phase is complete

- [x] T008 Create `backend/app/database.py` — SQLAlchemy 2.0 sync engine, sessionmaker, Base declarative base, `get_db` generator with yield (per research.md R1)
- [x] T009 [P] Create `backend/app/models.py` — All 10 ORM models matching data-model.md: User, Greenhouse, Device, SensorType, Sensor, SensorReading, ActuatorType, Actuator, ActuatorCommand, Script; include all ENUMs (connection_type_enum, device_status_enum, actuator_status_enum, command_enum), FKs, cascades, indexes (sensor_readings: sensor_id+recorded_at DESC — functionally satisfies Constitution IV index requirement since sensor_id encodes device+type), defaults; columns per Constitution: devices.last_seen (TIMESTAMPTZ), actuator_commands.status (VARCHAR(20) DEFAULT 'pending')
- [x] T010 [P] Create `backend/app/schemas.py` — Pydantic v2 schemas grouped by entity: UserCreate/UserResponse, GreenhouseCreate/GreenhouseUpdate/GreenhouseResponse, DeviceCreate/DeviceUpdate/DeviceResponse, SensorResponse/SensorReadingCreate/SensorReadingResponse/SensorReadingsHistoryResponse, ActuatorResponse/ActuatorCommandCreate/ActuatorCommandResponse, ScriptCreate/ScriptUpdate/ScriptResponse, DashboardOverviewResponse, HealthResponse/HealthDBResponse/HealthMQTTResponse, TokenResponse, ErrorResponse (per contracts/api-routes.md)
- [x] T011 Create `backend/app/dependencies.py` — FastAPI dependencies: `get_db` (imports from database.py), `get_current_user` stub (raises 401, filled in T016)
- [x] T012 Create `backend/app/main.py` — FastAPI app with lifespan placeholder (MQTT wired in T025), CORS middleware (origins from Settings), structured JSON logging middleware (method, path, status_code, duration_ms per research.md R8), standardized error handlers (422, 404, 500, 503 → ErrorResponse format), include all routers with `/api/v1` prefix
- [x] T013 Set up Alembic: create `backend/alembic.ini`, `backend/alembic/env.py` with models metadata, generate initial migration via `alembic revision --autogenerate -m "initial schema"` (per research.md R10)
- [x] T014 Create `backend/tests/conftest.py` — pytest fixtures: in-memory SQLite test DB, TestClient with dependency overrides for get_db, test user factory, auth token helper

**Checkpoint**: Foundation ready — app structure complete, models defined, migrations generated, test infra ready

---

## Phase 3: User Story 1 — Auth (Priority: P1)

**Goal**: Register, login, JWT token flow; protected routes reject unauthenticated requests

**Independent Test**: Register → login → use token on protected endpoint → 200; no token → 401

- [x] T015 [US1] Implement auth routes in `backend/app/routes/auth.py` — POST `/auth/register` (hash password with passlib bcrypt, create user, return 201 UserResponse), POST `/auth/login` (verify credentials, return 200 TokenResponse with access_token+refresh_token), POST `/auth/refresh` (validate refresh_token, return new access_token), GET `/auth/me` (Depends get_current_user, return UserResponse)
- [x] T016 [US1] Wire `get_current_user` in `backend/app/dependencies.py` — full JWT decode with python-jose, lookup user in DB session, raise 401 with INVALID_CREDENTIALS/TOKEN_EXPIRED codes; apply Depends(get_current_user) to all routes except /health/*, /auth/register,login,refresh, /simulator/*
- [x] T017 [US1] Tests in `backend/tests/test_auth.py` — test register (201, duplicate email 422), login (200 with tokens, wrong password 401), refresh (200, invalid token 401), me (200 with valid token, 401 without)

**Checkpoint**: US1 complete — auth flow works, protected routes require valid JWT

---

## Phase 4: User Story 1 (cont.) — Health Endpoints (Priority: P1)

**Goal**: Health endpoints with DB and MQTT status details

**Independent Test**: `curl /api/v1/health` returns 200 with db/mqtt status

- [x] T018 [US1] Implement health routes in `backend/app/routes/health.py` — GET `/health` (200, return status + db status + mqtt status + timestamp), GET `/health/db` (200, check DB connectivity, return status + latency_ms), GET `/health/mqtt` (200, check MQTT connection status, return status + connected boolean); no auth required

**Checkpoint**: Health endpoints complete with sub-checks (needed before Docker healthchecks)

---

## Phase 5: User Story 2 — Greenhouses CRUD (Priority: P1)

**Goal**: Full CRUD for greenhouses scoped to current user

**Independent Test**: Create greenhouse, list (only own), update, delete with cascade

- [x] T019 [US2] Implement greenhouse routes in `backend/app/routes/greenhouses.py` — GET `/greenhouses` (list user's greenhouses with total count), GET `/greenhouses/{id}` (with devices[], scripts[] eager load, 404 if not owned), POST `/greenhouses` (201, bind to current user_id), PUT `/greenhouses/{id}` (200, only own), DELETE `/greenhouses/{id}` (204, cascade)
- [x] T020 [US2] Tests in `backend/tests/test_greenhouses.py` — test CRUD (create 201, list only own, get 404 for other user's, update 200, delete 204 cascade)

**Checkpoint**: US2 complete — greenhouse CRUD with user isolation

---

## Phase 6: User Story 3 — Devices CRUD (Priority: P1)

**Goal**: Full CRUD for devices within greenhouses

**Independent Test**: Create device in greenhouse, list with status filter, get details with sensors/actuators, delete cascade

- [x] T021 [US3] Implement device routes in `backend/app/routes/devices.py` — GET `/greenhouses/{id}/devices` (filterable by status query param, return total+devices[]), GET `/greenhouses/{gid}/devices/{did}` (with sensors[] and actuators[] eager load), POST `/greenhouses/{id}/devices` (201), PUT `/greenhouses/{gid}/devices/{did}` (200), DELETE `/greenhouses/{gid}/devices/{did}` (204, cascade); verify greenhouse ownership in all routes
- [x] T022 [US3] Tests in `backend/tests/test_devices.py` — test CRUD within greenhouse, status filter, ownership check, cascade delete

**Checkpoint**: US3 complete — device CRUD functional within greenhouse hierarchy

---

## Phase 7: User Story 4 — Sensor Readings (Priority: P1)

**Goal**: Sensor listing, manual reading creation, historical readings with filtering and statistics

**Independent Test**: List sensors, add reading, query history with start_time/end_time/limit/aggregation

- [x] T023 [US4] Implement sensor routes in `backend/app/routes/sensors.py` — GET `/greenhouses/{gid}/devices/{did}/sensors` (list sensors with latest readings), GET `/sensors/{id}/readings` (query params: start_time, end_time, limit, aggregation; return sensor_id, sensor_type, unit, readings[], statistics min/max/avg), POST `/sensors/{id}/readings` (manual reading for testing, 201)
- [x] T024 [US4] Tests in `backend/tests/test_sensors.py` — test list sensors, create reading, history with filters, statistics calculation

**Checkpoint**: US4 complete — sensor data endpoints with history and statistics

---

## Phase 8: User Story 6 — MQTT Integration (Priority: P1)

**Goal**: Bidirectional MQTT communication with ESP32 devices via Mosquitto

**Independent Test**: Publish sensor message to MQTT, verify saved in DB; send command via API, verify published to MQTT

- [x] T025 [US6] Create `backend/app/mqtt/topics.py` — topic constants and helper functions: SENSOR_TOPIC_PATTERN = `devices/+/sensors/+`, STATUS_TOPIC_PATTERN = `devices/+/status/+`, LWT_TOPIC_PATTERN = `devices/+/lwt`, command_topic(device_id, actuator_type), parse_topic(topic_string) → (device_id, category, type)
- [x] T026 [P] [US6] Create `backend/app/mqtt/client.py` — MQTTClient class using paho-mqtt: connect with username/password (from Settings.MQTT_USERNAME/MQTT_PASSWORD per Constitution V), reconnect with exponential backoff, subscribe to sensor, status, and LWT topics, `loop_start()` in background thread, publish method for commands with QoS 1 (Constitution II), disconnect on shutdown; store asyncio event loop reference for bridge (per research.md R2)
- [x] T027 [P] [US6] Create `backend/app/mqtt/handlers.py` — on_message callback: parse topic, route to handler; `handle_sensor_message` (parse payload, find sensor by device_id+type, save SensorReading with QoS 0, update device.last_seen, broadcast via WebSocket), `handle_status_message` (parse payload, update actuator status, update actuator_command lifecycle to 'confirmed', broadcast via WebSocket with QoS 1), `handle_lwt_message` (set device.status='offline', broadcast device_status via WebSocket); use `asyncio.run_coroutine_threadsafe()` bridge (per research.md R2)
- [x] T028 [US6] Wire MQTT client into FastAPI lifespan in `backend/app/main.py` — connect on startup, disconnect on shutdown; make client accessible for actuator routes to publish commands and for health/mqtt endpoint
- [x] T029 [US6] Tests in `backend/tests/test_mqtt.py` — test topic parsing, handler routing, sensor message → DB save, status message → actuator update, LWT → device offline (mock paho client)

**Checkpoint**: US6 complete — MQTT bidirectional communication with auth and LWT

---

## Phase 9: User Story 5 — Actuator Commands (Priority: P1)

**Goal**: Actuator listing, command sending (with MQTT publish), command history

**Independent Test**: List actuators, send command, verify 202 and MQTT publish, query history

- [x] T030 [US5] Implement actuator routes in `backend/app/routes/actuators.py` — GET `/greenhouses/{gid}/devices/{did}/actuators` (all actuators with last_command), POST `/actuators/{id}/commands` (validate command enum on/off/set_value, **check device.status — reject with 409 DEVICE_OFFLINE if offline per Constitution VIII**, save to DB with status='pending', publish to MQTT topic `devices/{device_id}/commands/{actuator_type}` with QoS 1, return 202), GET `/actuators/{id}/commands` (history with start_time, end_time, limit filters)
- [x] T031 [US5] Tests in `backend/tests/test_actuators.py` — test list actuators, send command 202, reject command to offline device 409, command history with filters

**Checkpoint**: US5 complete — actuator commands with MQTT publishing and offline rejection

---

## Phase 10: User Story 7 — WebSocket (Priority: P1)

**Goal**: Real-time updates for greenhouse monitoring via WebSocket

**Independent Test**: Connect to WS, send auth token, receive sensor_update/actuator_update/device_status messages

- [x] T032 [US7] Create `backend/app/websocket.py` — ConnectionManager class with dict[greenhouse_id → set[WebSocket]] (per research.md R4); methods: connect(ws, greenhouse_id), disconnect(ws, greenhouse_id), broadcast(greenhouse_id, message); authenticate first message (JWT token), close with 4001 if invalid
- [x] T033 [US7] Add WebSocket endpoint in `backend/app/main.py` or dedicated route — `ws://host/ws/greenhouse/{id}`, first message = auth token, then stream events; message types: `{"type": "sensor_update", "data": {...}}`, `{"type": "actuator_update", "data": {...}}`, `{"type": "device_status", "data": {...}}`

**Checkpoint**: US7 complete — WebSocket real-time broadcast functional

---

## Phase 11: User Story 11 — Containerization (Priority: P1)

**Goal**: Full system runs via `docker compose up`

**Independent Test**: `docker compose up --build` — all services start, health check passes, MQTT accessible

- [x] T034 [US11] Create Mosquitto config: `mosquitto/mosquitto.conf` with listener 1883, `password_file /mosquitto/config/passwd` (Constitution V: MQTT auth required); create `mosquitto/passwd` with default backend user credentials; `allow_anonymous false`
- [x] T035 [US11] Update `backend/Dockerfile` entrypoint: run `alembic upgrade head` before uvicorn (per research.md R10); add healthcheck (`curl /api/v1/health`)
- [x] T036 [US11] Update `docker-compose.yml` — add healthchecks for all services (pg_isready for postgres, mosquitto_sub timeout for mosquitto, curl for backend), proper depends_on with condition: service_healthy, environment variables from .env, named volumes for postgres data and mosquitto config, restart policies

**Checkpoint**: US11 complete — `docker compose up --build` brings up entire system with MQTT auth

---

## Phase 12: User Story 8 — IoT Emulator (Priority: P2)

**Goal**: Background emulator generating realistic sensor data via math models

**Independent Test**: POST /simulator/start → wait → check sensor_readings table for new entries

- [x] T037 [P] [US8] Create `backend/app/simulator/sensors.py` — math models per research.md R9: TemperatureModel (T_base=24, A=4, σ=0.3), HumidityModel (H_base=70, k=2.5, σ=1.0), LightModel (L_max=50000, sunrise/daylight); each model.generate(time, actuator_states) → float; actuator reaction effects (heating ON → +0.5°C, ventilation ON → temp↓/humidity↓, watering ON → humidity +5%, lighting ON → +5000-10000 lux)
- [x] T038 [US8] Create `backend/app/simulator/engine.py` — SimulatorEngine class: asyncio background task, loops over configured devices, generates readings via sensor models every N seconds, writes to DB, broadcasts via WebSocket; start/stop/status methods; tracks uptime, devices_count, readings_generated
- [x] T039 [US8] Implement simulator routes in `backend/app/routes/simulator.py` — POST `/simulator/start` (200, return status+devices_count; idempotent per edge case), POST `/simulator/stop` (200), GET `/simulator/status` (200, return status/uptime_seconds/devices_count/readings_generated); no auth required

**Checkpoint**: US8 complete — emulator generates realistic data visible in readings

---

## Phase 13: User Story 9 — Dashboard (Priority: P2)

**Goal**: Aggregated overview of all user's greenhouses, devices, readings, statuses

**Independent Test**: GET /dashboard/overview returns summary with greenhouse data

- [x] T040 [US9] Implement dashboard route in `backend/app/routes/dashboard.py` — GET `/dashboard/overview` (200); query all user's greenhouses with devices, latest sensor readings, actuator statuses; return `{summary: {total_greenhouses, total_devices, online_devices, offline_devices}, greenhouses: [{id, name, devices: [{id, name, status, latest_readings, actuator_statuses}]}]}`
- [x] T041 [US9] Tests in `backend/tests/test_dashboard.py` — test overview returns correct summary counts and nested structure

**Checkpoint**: US9 complete — dashboard aggregation returns comprehensive overview

---

## Phase 14: User Story 10 — Scripts CRUD (Priority: P2)

**Goal**: CRUD for automation scripts within greenhouses

**Independent Test**: Create, list, update, delete scripts within a greenhouse

- [x] T042 [US10] Implement script routes in `backend/app/routes/scripts.py` — GET `/greenhouses/{id}/scripts` (list scripts, 200), POST `/greenhouses/{id}/scripts` (create with name, script_code, enabled; 201), PUT `/scripts/{id}` (update, 200), DELETE `/scripts/{id}` (204); verify greenhouse ownership

**Checkpoint**: US10 complete — script CRUD functional

---

## Phase 15: Cross-Cutting — Device Resilience & Data Retention

**Purpose**: Constitution IV and VIII compliance

- [x] T043 Add periodic device status checker in `backend/app/main.py` lifespan — asyncio background task every 60s: query devices where last_seen > 60s ago and status='online', set status='offline', broadcast device_status via WebSocket (per research.md R7, Constitution VIII)
- [x] T044 Add data retention cleanup job in `backend/app/main.py` lifespan — asyncio background task (daily): delete raw sensor_readings older than 7 days (Constitution IV); actuator_commands older than 30 days. Note: hourly/monthly aggregation deferred to P2 feature — for now, simple deletion satisfies retention window

**Checkpoint**: Device resilience and data retention policies active

---

## Phase 16: Polish & Verification

**Purpose**: Validation, seed data, linting, and cleanup

- [x] T045 Add seed data for SensorType (temperature, humidity, light) and ActuatorType (lighting, heating, ventilation, watering) — either in Alembic migration or startup event in `backend/app/main.py`
- [x] T046 Verify all endpoints match `specs/001-backend-api-foundation/contracts/api-routes.md` — check method, path, auth requirement, request/response shapes; verify all error responses follow ErrorResponse format `{error: {code, message, timestamp}}`
- [x] T047 Run `ruff check backend/app/` and `mypy backend/app/` — fix all errors (Constitution: code MUST pass linting)
- [x] T048 Verify Google docstrings on all classes, methods, and functions across `backend/app/`
- [x] T049 End-to-end validation: `docker compose up --build`, run health check (all 3 sub-endpoints), register user, login, create greenhouse, create device, add sensor reading, send actuator command, check dashboard, start simulator, connect WebSocket, verify MQTT auth works

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Setup — BLOCKS all user stories
- **US1-Auth (Phase 3)**: Depends on Foundational
- **US1-Health (Phase 4)**: Depends on Foundational (MQTT client reference optional, graceful if unavailable)
- **US2-Greenhouses (Phase 5)**: Depends on US1 (needs auth for user isolation)
- **US3-Devices (Phase 6)**: Depends on US2 (devices belong to greenhouses)
- **US4-Sensors (Phase 7)**: Depends on US3 (sensors belong to devices)
- **US6-MQTT (Phase 8)**: Depends on Foundational (independent of CRUD routes)
- **US5-Actuators (Phase 9)**: Depends on US3 + US6 (commands publish to MQTT, offline check needs device status)
- **US7-WebSocket (Phase 10)**: Depends on Foundational (independent, called from MQTT handlers)
- **US11-Docker (Phase 11)**: Depends on US1-Health (needs health endpoint for healthchecks)
- **US8-Emulator (Phase 12)**: Depends on US4+US6 (writes readings, uses WS broadcast)
- **US9-Dashboard (Phase 13)**: Depends on US2+US3+US4+US5 (aggregates all data)
- **US10-Scripts (Phase 14)**: Depends on US2 (scripts belong to greenhouses)
- **Resilience (Phase 15)**: Depends on US6+US7 (needs MQTT and WebSocket)
- **Polish (Phase 16)**: Depends on all phases

### Parallel Opportunities

- T002-T007 can all run in parallel (Setup — different files)
- T009, T010 can run in parallel (Foundational — models.py vs schemas.py)
- T025, T026, T027 can partially run in parallel (MQTT subpackage — different files)
- T037 can run in parallel with T038 (Emulator — sensors.py vs engine.py)
- US6-MQTT and US7-WebSocket can start in parallel after Foundational
- US10-Scripts is independent of US4-US9 (only needs US2)

### Within Each User Story

- Models/schemas (Foundational) → Routes → Tests
- MQTT topics → client + handlers → wiring into main.py → tests
- Simulator models → engine → routes

---

## Parallel Example: After Foundational

```bash
# These can start simultaneously after Phase 2:
Stream A: US1 (Auth) → US1 (Health) → US2 → US3 → US4 (Sensors)
Stream B: US6 (MQTT) → US7 (WebSocket)

# After convergence:
US5 (Actuators) — needs US3 + US6
US11 (Docker) — needs Health
US8 (Emulator) — needs US4 + US6
US9 (Dashboard) — needs US2-US5
US10 (Scripts) — needs US2
```

---

## Implementation Strategy

### MVP First (US1 + Docker)

1. Complete Phase 1: Setup (T001-T007)
2. Complete Phase 2: Foundational (T008-T014)
3. Complete Phase 3: US1-Auth (T015-T017)
4. Complete Phase 4: US1-Health (T018)
5. Complete Phase 11: US11-Docker (T034-T036)
6. **STOP and VALIDATE**: `docker compose up --build`, health returns 200, auth flow works
7. Deploy/demo if ready

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. US1 → Auth + Health works (MVP)
3. US2 → Greenhouse CRUD
4. US3 → Device CRUD within greenhouses
5. US4 → Sensor readings with history
6. US6 → MQTT bidirectional communication with auth
7. US5 → Actuator commands with MQTT + offline rejection
8. US7 → WebSocket real-time updates
9. US11 → Full Docker containerization
10. US8 → IoT emulator with math models
11. US9 → Dashboard aggregation
12. US10 → Automation scripts CRUD
13. Resilience → Periodic checks + data retention
14. Each story adds value without breaking previous stories

---

## Summary

- **Total tasks**: 49
- **Phases**: 16 (Setup, Foundational, 11 User Stories, Resilience, Polish)
- **P1 tasks**: 36 (Auth, Health, Greenhouses, Devices, Sensors, Actuators, MQTT, WebSocket, Docker)
- **P2 tasks**: 6 (Emulator, Dashboard, Scripts)
- **Cross-cutting**: 7 (test infra, resilience, retention, seed data, linting, docstrings, E2E)
- **Test tasks**: 8 (conftest + 7 test files)

## Constitution Compliance

| Principle | Coverage |
|-----------|----------|
| I. Layered Architecture | ✅ Layers enforced by project structure |
| II. MQTT-First | ✅ T025-T029, QoS 0/1 specified |
| III. Containerized | ✅ T034-T036, healthchecks, named volumes |
| IV. Data Integrity | ✅ T009 (models+index), T013 (Alembic), T044 (retention) |
| V. Security | ✅ T015-T016 (JWT/bcrypt), T026+T034 (MQTT auth), T010 (Pydantic) |
| VI. Simplicity | ✅ Flat layout, no unnecessary abstractions |
| VII. Observability | ✅ T012 (JSON logging), T018 (health sub-endpoints) |
| VIII. Device Resilience | ✅ T027 (LWT), T030 (offline rejection), T043 (periodic check) |
| IX. Contract Stability | ✅ /api/v1 prefix, MQTT topics per Miro |
| Tests | ✅ T014 (conftest), T017/T020/T022/T024/T029/T031/T041 |
| Linting | ✅ T007 (config), T047 (verify) |

## Notes

- [P] tasks = different files, no dependencies on incomplete tasks
- [Story] label maps task to specific user story from spec.md
- All response shapes must match `contracts/api-routes.md`
- Google docstrings required on ALL classes, methods, and functions (FR-018)
- MQTT topics follow Miro board: `devices/{device_id}/{category}/{type}`
- MQTT auth required per Constitution V — no anonymous access
- Commands to offline devices MUST be rejected (Constitution VIII)
- Data retention: raw readings 7 days, commands 30 days (Constitution IV)
