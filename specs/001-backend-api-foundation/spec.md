# Feature Specification: Backend API Foundation

**Feature Branch**: `001-backend-api-foundation`
**Created**: 2026-03-04
**Status**: Draft
**Input**: User description: "Backend routes, DB connectors, ORM model stubs. Minimal folder structure, no DB implementation yet."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Backend Application Startup (Priority: P1)

A developer clones the repository, installs dependencies, and starts
the FastAPI backend. The application boots successfully, connects to
the database (or fails gracefully if DB is unavailable), and exposes
a health check endpoint confirming the service is alive.

**Why this priority**: Nothing else works until the application can
start and respond to requests. This is the foundation for all other
stories.

**Independent Test**: Start the backend with `uvicorn`, call
`GET /health` and confirm a 200 response.

**Acceptance Scenarios**:

1. **Given** the backend is started, **When** a client sends
   `GET /api/v1/health`, **Then** the server returns 200 with
   status information
2. **Given** the database is unreachable, **When** the backend
   starts, **Then** it logs a warning but does not crash — health
   endpoint reports DB as unavailable

---

### User Story 2 - Device Management Routes (Priority: P1)

A frontend developer or API consumer can call CRUD endpoints for
device management: list devices, get a single device, create,
update, and deactivate a device. Routes return proper HTTP status
codes and follow the documented API specification.

**Why this priority**: Device management is the core entity that
all sensor and actuator operations depend on.

**Independent Test**: Call each device endpoint with test data and
verify correct status codes and response shapes.

**Acceptance Scenarios**:

1. **Given** the backend is running, **When** `GET /api/v1/devices`
   is called, **Then** it returns a paginated list of devices (200)
2. **Given** a valid device payload, **When** `POST /api/v1/devices`
   is called, **Then** a new device is created (201)
3. **Given** an unknown device ID, **When** `GET /api/v1/devices/{id}`
   is called, **Then** the server returns 404

---

### User Story 3 - Sensor & Actuator Routes (Priority: P1)

A frontend developer can call endpoints to retrieve sensor readings
for a device and send actuator commands. These routes are defined
and return appropriate responses even if the underlying business
logic is minimal at this stage.

**Why this priority**: Sensor and actuator endpoints are the primary
user-facing features of the greenhouse system.

**Independent Test**: Call sensor retrieval and actuator command
endpoints, verify correct routing, status codes, and response
structure.

**Acceptance Scenarios**:

1. **Given** a registered device, **When**
   `GET /api/v1/devices/{id}/sensors` is called, **Then** it
   returns latest sensor readings (200)
2. **Given** a registered device, **When**
   `POST /api/v1/devices/{id}/actuators/heating` is called with
   a valid command, **Then** it returns 202 Accepted
3. **Given** a registered device, **When**
   `GET /api/v1/devices/{id}/actuators` is called, **Then** it
   returns current actuator statuses (200)

---

### User Story 4 - Authentication Routes (Priority: P2)

A user can register, login, and refresh their JWT token. Protected
routes reject unauthenticated requests with 401.

**Why this priority**: Authentication is required for production
but other stories can be developed and tested without it initially.

**Independent Test**: Register a user, login to get a token, access
a protected endpoint with and without the token.

**Acceptance Scenarios**:

1. **Given** valid credentials, **When** `POST /api/v1/auth/register`
   is called, **Then** a user account is created (201)
2. **Given** a registered user, **When** `POST /api/v1/auth/login`
   is called, **Then** a JWT token is returned (200)
3. **Given** no token, **When** a protected endpoint is called,
   **Then** the server returns 401

---

### User Story 5 - Dashboard Overview Route (Priority: P3)

An operator can call the dashboard endpoint to get a summary of
all devices, their online status, and current readings in a
single request.

**Why this priority**: Dashboard is a convenience aggregation — all
underlying data is accessible via individual endpoints already.

**Independent Test**: Call `GET /api/v1/dashboard/overview` and
verify the response contains device summary data.

**Acceptance Scenarios**:

1. **Given** multiple registered devices, **When**
   `GET /api/v1/dashboard/overview` is called, **Then** it returns
   a summary with total, online, and offline device counts (200)

---

### Edge Cases

- What happens when the request body is malformed JSON?
  System returns 422 with a descriptive validation error.
- What happens when the database is unavailable during a CRUD
  operation? System returns 503 Service Unavailable.
- What happens when pagination parameters are negative or
  exceed maximum? System clamps to valid bounds or returns 400.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST expose a health check endpoint at
  `GET /api/v1/health` returning service status
- **FR-002**: System MUST provide full CRUD for devices at
  `/api/v1/devices` with pagination (limit/offset)
- **FR-003**: System MUST expose sensor reading endpoints at
  `/api/v1/devices/{id}/sensors` and
  `/api/v1/devices/{id}/sensors/{type}`
- **FR-004**: System MUST expose actuator control endpoints at
  `/api/v1/devices/{id}/actuators` and
  `/api/v1/devices/{id}/actuators/{type}`
- **FR-005**: System MUST expose auth endpoints: register, login,
  token refresh at `/api/v1/auth/*`
- **FR-006**: System MUST expose a dashboard overview endpoint at
  `/api/v1/dashboard/overview`
- **FR-007**: System MUST provide a database connection module
  that creates and manages the SQLAlchemy session lifecycle
- **FR-008**: System MUST define ORM model stubs for all core
  entities (User, Device, SensorReading, ActuatorCommand) matching
  the schema in `docs/database_design.md`
- **FR-009**: System MUST validate all request bodies using
  Pydantic schemas and return 422 on validation failure
- **FR-010**: System MUST return standardized error responses
  with error code, message, and timestamp
- **FR-011**: System MUST configure CORS to allow frontend origin

### Key Entities

- **User**: Operator account with username, email, hashed password,
  active/superuser flags
- **Device**: IoT greenhouse unit with unique device_id, name,
  location, online/active status, MQTT client ID, config (JSON)
- **SensorReading**: Time-series record with device reference,
  sensor type (temperature/humidity/light), value, unit, timestamp
- **ActuatorCommand**: Command record with device reference,
  actuator type (lighting/heating/ventilation/watering), command,
  status lifecycle (pending → sent → confirmed | failed)

### Assumptions

- Database schema implementation is handled by another developer;
  this feature only creates ORM model stubs with correct field
  definitions but does not run migrations
- Routes connect to a real service layer with SQLAlchemy sessions;
  while the database is unavailable, services MUST use in-memory
  mocks/fixtures to return realistic data matching the API spec
- MQTT integration is out of scope for this feature — actuator
  endpoints accept commands but do not publish to MQTT yet
- Authentication middleware is defined but may use simplified
  logic until full JWT implementation is complete
- The backend folder structure MUST be minimal — avoid deep
  nesting; group by concern (models, routes, schemas) not by
  feature

## Clarifications

### Session 2026-03-04

- Q: Глубина реализации роутов — заглушки или реальный сервисный слой? → A: Вариант B — реальный сервисный слой с SQLAlchemy-сессиями; пока БД недоступна, использовать моки (in-memory или фикстуры) для возврата данных

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All defined API routes respond with correct HTTP
  status codes when called (no 500 errors on valid requests)
- **SC-002**: The application starts in under 5 seconds and the
  health endpoint responds within 100ms
- **SC-003**: Every route returns responses matching the structure
  defined in `docs/api_specification.md`
- **SC-004**: ORM models cover all 4 core entities with field
  definitions that match `docs/database_design.md`
- **SC-005**: The backend consists of no more than 15 source files
  total (excluding tests), keeping the structure compact
