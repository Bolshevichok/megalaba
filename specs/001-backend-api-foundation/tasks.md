# Tasks: Backend API Foundation

**Input**: Design documents from `/specs/001-backend-api-foundation/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/

**Tests**: Not explicitly requested — test tasks omitted.

**Organization**: Tasks grouped by user story for independent implementation.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: US1–US5 maps to spec.md user stories
- Exact file paths included in every task

## Phase 1: Setup

**Purpose**: Project initialization and dependency configuration

- [x] T001 Create backend directory structure: `backend/app/`, `backend/app/routes/`, `backend/app/__init__.py`, `backend/app/routes/__init__.py`
- [x] T002 [P] Create `backend/requirements.txt` with: fastapi, uvicorn, sqlalchemy, psycopg2-binary, pydantic, pydantic-settings, python-jose[cryptography], passlib[bcrypt], python-multipart
- [x] T003 [P] Create `backend/app/config.py` — Pydantic Settings class with DATABASE_URL, USE_MOCK_DB, SECRET_KEY, CORS_ORIGINS, ACCESS_TOKEN_EXPIRE_MINUTES (see quickstart.md for defaults)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story

**CRITICAL**: No user story work can begin until this phase is complete

- [x] T004 Create `backend/app/database.py` — SQLAlchemy engine, sessionmaker, Base declarative base, `get_db` generator with yield; when `USE_MOCK_DB=true` return mock store instead of real session (per research.md R2)
- [x] T005 [P] Create `backend/app/models.py` — ORM models for User, Device, SensorReading, ActuatorCommand matching data-model.md (fields, types, FKs, indexes, defaults)
- [x] T006 [P] Create `backend/app/schemas.py` — Pydantic v2 schemas: UserCreate/UserResponse, DeviceCreate/DeviceUpdate/DeviceResponse/DeviceList, SensorReadingCreate/SensorReadingResponse/SensorListResponse, ActuatorCommandCreate/ActuatorCommandResponse/ActuatorListResponse, DashboardOverview, HealthResponse, TokenResponse, ErrorResponse (per contracts/api-routes.md)
- [x] T007 Create `backend/app/dependencies.py` — FastAPI dependencies: `get_db` (imports from database.py), `get_current_user` (JWT decode stub, returns User or raises 401)
- [x] T008 Create `backend/app/services.py` — base structure: in-memory mock data store (3 test devices, sample sensor readings, sample actuator states per docs/api_specification.md); empty function stubs for each service group; service functions MUST catch DB exceptions and raise HTTPException(503) when database is unavailable (per spec.md edge case)
- [x] T009 Create `backend/app/main.py` — FastAPI app instance, CORS middleware (origins strictly from `Settings.CORS_ORIGINS` in config.py, never hardcoded), standardized error handlers (422, 404, 500, 503 → ErrorResponse format per contracts/api-routes.md), include all routers with `/api/v1` prefix, structured JSON logging middleware (log every request with method, path, status_code, duration_ms per Constitution VII)

**Checkpoint**: Foundation ready — `uvicorn app.main:app` starts without errors (no routes yet)

---

## Phase 3: User Story 1 — Backend Startup + Health (Priority: P1) MVP

**Goal**: App starts, health endpoint confirms service is alive

**Independent Test**: `curl http://localhost:8000/api/v1/health` returns 200

- [x] T010 [US1] Implement health check route in `backend/app/routes/health.py` — GET `/health` returns `{status: "ok", db: "available"|"unavailable", timestamp: ISO8601}`; check DB connectivity, catch exceptions gracefully
- [x] T011 [US1] Verify app startup: run `USE_MOCK_DB=true uvicorn app.main:app`, confirm health endpoint returns 200, confirm OpenAPI docs at `/docs`

**Checkpoint**: US1 complete — app boots and health responds

---

## Phase 4: User Story 2 — Device Management Routes (Priority: P1)

**Goal**: Full CRUD for devices with pagination and filters

**Independent Test**: Call all 5 device endpoints, verify status codes and response shapes

- [x] T012 [US2] Add device service functions to `backend/app/services.py` — `list_devices(limit, offset, is_active, is_online)`, `get_device(device_id)`, `create_device(data)`, `update_device(device_id, data)`, `delete_device(device_id)`; mock implementation returns data from in-memory store
- [x] T013 [US2] Implement device routes in `backend/app/routes/devices.py` — GET `/devices` (paginated, filterable), GET `/devices/{device_id}`, POST `/devices`, PUT `/devices/{device_id}`, DELETE `/devices/{device_id}`; wire to service functions; return 404 for unknown device_id, 201 on create, 204 on delete (per contracts/api-routes.md)

**Checkpoint**: US2 complete — all device CRUD endpoints return correct responses

---

## Phase 5: User Story 3 — Sensor & Actuator Routes (Priority: P1)

**Goal**: Sensor retrieval and actuator command endpoints

**Independent Test**: GET sensors returns readings, POST actuator returns 202

- [x] T014 [P] [US3] Add sensor service functions to `backend/app/services.py` — `get_latest_readings(device_id)`, `get_sensor_history(device_id, sensor_type, start_time, end_time, limit, aggregation)`, `create_reading(device_id, sensor_type, data)`; mock returns sample temperature/humidity/light data with statistics
- [x] T015 [P] [US3] Add actuator service functions to `backend/app/services.py` — `get_actuator_statuses(device_id)`, `send_command(device_id, actuator_type, command, parameters)`, `get_command_history(device_id, actuator_type, filters)`; mock creates command with status "pending" in memory
- [x] T016 [US3] Implement sensor routes in `backend/app/routes/sensors.py` — GET `/devices/{device_id}/sensors`, GET `/devices/{device_id}/sensors/{sensor_type}` (with query params: start_time, end_time, limit, aggregation), POST `/devices/{device_id}/sensors/{sensor_type}`; validate sensor_type is one of temperature/humidity/light
- [x] T017 [US3] Implement actuator routes in `backend/app/routes/actuators.py` — GET `/devices/{device_id}/actuators`, POST `/devices/{device_id}/actuators/{actuator_type}` (returns 202), GET `/devices/{device_id}/actuators/{actuator_type}/history`; validate actuator_type and command values

**Checkpoint**: US3 complete — sensor and actuator endpoints functional with mock data

---

## Phase 6: User Story 4 — Authentication Routes (Priority: P2)

**Goal**: Register, login, JWT token flow; protected routes reject unauthenticated requests

**Independent Test**: Register → login → use token on protected endpoint → 200; no token → 401

- [x] T018 [US4] Add auth service functions to `backend/app/services.py` — `register_user(data)` (hash password with passlib bcrypt, store in mock), `authenticate_user(username, password)` (verify hash), `create_access_token(user_id)` and `create_refresh_token(user_id)` (python-jose JWT), `refresh_token(token)`
- [x] T019 [US4] Implement auth routes in `backend/app/routes/auth.py` — POST `/auth/register` (201), POST `/auth/login` (200 + TokenResponse), POST `/auth/refresh` (200 + TokenResponse); validate input, return appropriate errors
- [x] T020 [US4] Wire `get_current_user` dependency in `backend/app/dependencies.py` — decode JWT from Authorization header, lookup user in mock store, raise 401 if invalid; add `Depends(get_current_user)` to device, sensor, actuator, and dashboard routes; health endpoint (`/health`) and auth routes (`/auth/*`) MUST remain public (no JWT required)

**Checkpoint**: US4 complete — auth flow works, protected routes require valid JWT

---

## Phase 7: User Story 5 — Dashboard Overview Route (Priority: P3)

**Goal**: Single endpoint aggregating all device statuses and current readings

**Independent Test**: GET `/api/v1/dashboard/overview` returns summary with device counts

- [x] T021 [US5] Add dashboard service functions to `backend/app/services.py` — `get_overview()` returns `{summary: {total_devices, online_devices, offline_devices, active_alerts}, devices: [{device_id, name, is_online, current_readings, actuator_status}]}`; aggregates from mock device/sensor/actuator data
- [x] T022 [US5] Implement dashboard route in `backend/app/routes/dashboard.py` — GET `/dashboard/overview` (200, DashboardOverview schema); wire to service

**Checkpoint**: US5 complete — dashboard returns aggregated data

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Validation and cleanup

- [x] T023 Verify all 17 endpoints match `specs/001-backend-api-foundation/contracts/api-routes.md` — check method, path, auth requirement, request/response shapes; verify all error responses follow ErrorResponse format `{error: {code, message, details, timestamp}}`; verify CORS allows only configured origins
- [x] T024 Verify source file count in `backend/app/` is ≤15 (excluding tests)
- [x] T025 Run `specs/001-backend-api-foundation/quickstart.md` validation — start app in mock mode, call health, register user, login, list devices, get sensors

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Setup — BLOCKS all user stories
- **US1 (Phase 3)**: Depends on Foundational
- **US2 (Phase 4)**: Depends on Foundational (independent of US1)
- **US3 (Phase 5)**: Depends on Foundational (independent of US1, US2)
- **US4 (Phase 6)**: Depends on US2, US3 (needs routes to protect)
- **US5 (Phase 7)**: Depends on US2, US3 (needs device/sensor data to aggregate)
- **Polish (Phase 8)**: Depends on all user stories

### User Story Dependencies

- **US1 (P1)**: Independent after Foundational
- **US2 (P1)**: Independent after Foundational
- **US3 (P1)**: Independent after Foundational
- **US4 (P2)**: Requires US2 + US3 routes to exist (adds auth protection)
- **US5 (P3)**: Requires US2 + US3 services (aggregates their data)

### Within Each User Story

- Service functions before route handlers
- Route handlers before integration verification

### Parallel Opportunities

- T002, T003 can run in parallel (Setup phase)
- T005, T006 can run in parallel (Foundational — different files)
- US1, US2, US3 can all run in parallel after Foundational
- T014, T015 can run in parallel (US3 — sensor vs actuator services)

---

## Parallel Example: Foundational Phase

```bash
# These can run in parallel (different files):
Task: "Create models.py — all 4 ORM models" (T005)
Task: "Create schemas.py — all Pydantic schemas" (T006)

# Then sequentially:
Task: "Create services.py — base structure + mock store" (T008, depends on T005/T006)
Task: "Create main.py — app + CORS + routers" (T009, depends on T007/T008)
```

## Parallel Example: P1 Stories After Foundational

```bash
# All three P1 stories can start simultaneously:
Story US1: T010 → T011
Story US2: T012 → T013
Story US3: T014+T015 → T016+T017
```

---

## Implementation Strategy

### MVP First (US1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational
3. Complete Phase 3: US1 (health endpoint)
4. **STOP and VALIDATE**: App starts, health returns 200
5. Deploy/demo if ready

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. US1 → Health check works (MVP)
3. US2 → Device CRUD works
4. US3 → Sensors + actuators work
5. US4 → Auth protection active
6. US5 → Dashboard aggregation
7. Each story adds value without breaking previous stories

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story
- Mock data in services.py switched via `USE_MOCK_DB=true`
- All response shapes must match `contracts/api-routes.md`
- File budget: 15 source files max (see plan.md)
- No migrations — ORM models are stubs for future DB integration
