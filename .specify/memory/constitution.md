<!--
Sync Impact Report
===================
Version change: 1.0.0 → 1.1.0 (MINOR — 3 new principles added,
  Principle IV expanded with data retention policy)
Modified principles:
  - IV. Data Integrity & Persistence — expanded with retention/archival rules
Added sections:
  - VII. Observability & Monitoring (new principle)
  - VIII. Device Resilience (new principle)
  - IX. Contract Stability (new principle)
Removed sections: N/A
Templates requiring updates:
  - .specify/templates/plan-template.md — ✅ no update needed
  - .specify/templates/spec-template.md — ✅ no update needed
  - .specify/templates/tasks-template.md — ✅ no update needed
Follow-up TODOs: none
-->

# IoT Smart Greenhouse Monitoring System Constitution

## Core Principles

### I. Layered Architecture

Every component MUST belong to exactly one layer: IoT Device,
Communication (MQTT Broker), Backend, or Frontend. Cross-layer
coupling is prohibited — layers communicate only through their
defined interfaces (MQTT topics for device-backend, REST/WebSocket
for backend-frontend, SQL for backend-database).

Rationale: strict layer boundaries enable independent development,
testing, and deployment of each subsystem.

### II. MQTT-First Device Communication

All communication between IoT devices and the backend MUST use
MQTT publish-subscribe via the Mosquitto broker. Direct HTTP calls
from devices to the backend are prohibited. Topic naming MUST
follow the pattern `devices/{device_id}/{category}/{type}` where
category is one of `sensors`, `commands`, or `status`. Commands
MUST use QoS 1 (at-least-once); sensor data MAY use QoS 0.

Rationale: MQTT is lightweight for constrained ESP32 devices and
supports reliable bidirectional messaging with retained state.

### III. Containerized Services

Backend (FastAPI), Frontend (React/Nginx), PostgreSQL, and
Mosquitto MUST run as Docker containers orchestrated via
Docker Compose. IoT devices (ESP32/Wokwi) remain external to the
container network and connect via exposed MQTT port. Each service
MUST declare health checks. Persistent data MUST use named volumes.

Rationale: containerization ensures reproducible environments and
one-command deployment for the full stack.

### IV. Data Integrity & Persistence

All sensor readings and actuator commands MUST be persisted in
PostgreSQL. Schema changes MUST be managed through Alembic
migrations — manual DDL in production is prohibited. Time-series
sensor data MUST be indexed by (device_id, sensor_type, timestamp).
Actuator commands MUST track full lifecycle status:
pending → sent → confirmed | failed. Data retention policy:
raw sensor readings MUST be kept for 7 days, aggregated to
hourly averages after 7 days, and to monthly aggregates after
90 days. Actuator command history MUST be retained for at
least 30 days. An automated cleanup job MUST enforce these
retention windows.

Rationale: reliable data persistence is critical for monitoring
history, analytics, and audit trail of device commands. Retention
policy prevents unbounded storage growth from high-frequency
sensor data.

### V. Security by Default

API access MUST require JWT authentication. Passwords MUST be
hashed with bcrypt or argon2 — plaintext storage is prohibited.
MQTT broker MUST use username/password authentication with
per-device credentials. All user input MUST be validated via
Pydantic schemas. SQL queries MUST use ORM (SQLAlchemy) to
prevent injection. CORS MUST be configured to allow only
known frontend origins.

Rationale: IoT systems are high-value targets; security cannot
be deferred to later phases.

### VI. Simplicity & Pragmatism

Start with the simplest working solution. Do not introduce
abstractions, caching layers, or message queues until a concrete
performance problem is measured. Prefer standard library and
framework capabilities over third-party dependencies. The Wokwi
simulator is sufficient for development — physical hardware
integration is out of scope for MVP.

Rationale: project motto "Don't eat hedgehogs" — avoid
overcomplication that delays delivery without measurable benefit.

### VII. Observability & Monitoring

All backend services MUST use structured logging in JSON format
with levels DEBUG, INFO, WARNING, ERROR. Every API request MUST
be logged with method, path, status code, and duration. MQTT
message receipt and publishing MUST be logged at INFO level.
Device connectivity changes (online/offline) MUST generate
log events and be queryable through the API. Health check
endpoints (`/health`, `/health/db`, `/health/mqtt`) MUST be
implemented and return component status.

Rationale: an IoT system with multiple autonomous devices
requires full visibility into message flow, device state, and
service health to diagnose issues without physical access to
hardware.

### VIII. Device Resilience

IoT devices MUST implement automatic WiFi and MQTT reconnection
with exponential backoff. Every device MUST configure an MQTT
Last Will Testament message so the backend detects disconnections
without polling. The backend MUST track `last_seen` timestamp
per device and expose online/offline status through the API.
Commands sent to offline devices MUST be rejected with an
explicit error — silent drops are prohibited.

Rationale: greenhouse devices operate in environments with
unstable connectivity; the system MUST degrade gracefully and
report device state accurately to the operator.

### IX. Contract Stability

REST API endpoints MUST conform to the specification in
`docs/api_specification.md`. Any breaking change to the REST API
MUST increment the URL version (`/api/v1` → `/api/v2`). MQTT
topic structure (`devices/{device_id}/{category}/{type}`) and
payload format MUST NOT change without a documented migration
plan, because ESP32 firmware updates are costly. New sensor types
or actuator types MAY be added without breaking the contract as
long as the topic pattern is preserved.

Rationale: IoT firmware is harder to update than server-side
code; API and MQTT contracts must remain stable to avoid bricking
deployed devices.

## Technology Stack Constraints

- **Backend**: Python 3.11+, FastAPI, SQLAlchemy ORM, Pydantic,
  Paho-MQTT, Alembic
- **Frontend**: React 18+, TypeScript, Axios, Recharts
- **Database**: PostgreSQL (latest stable)
- **MQTT Broker**: Eclipse Mosquitto
- **IoT**: ESP32 (Arduino framework, C/C++), Wokwi simulator
- **Containerization**: Docker, Docker Compose
- **Authentication**: JWT (access + refresh tokens)
- **API versioning**: URL-based (`/api/v1/...`); breaking changes
  MUST increment the version

Adding new runtime dependencies MUST be justified by a concrete
requirement. Framework-level alternatives (e.g., FastAPI built-in
features) MUST be preferred over external packages.

## Development Workflow & Quality Gates

- Every backend task MUST include unit tests for services and
  integration tests for API endpoints
- Frontend tasks MUST include manual testing checklists at minimum
- Code MUST pass linting (ESLint / Flake8) and type checking
  (TypeScript / mypy) before merge
- Database schema changes MUST go through Alembic migrations
- Docker Compose `up` MUST succeed with all health checks passing
  before any task is considered complete
- Commits SHOULD be made after each completed task or logical group
- API endpoints MUST follow the documented specification in
  `docs/api_specification.md`; deviations require spec update first

## Governance

This constitution is the authoritative source for architectural
decisions and development standards. All code contributions MUST
comply with the principles above.

**Amendment procedure**:
1. Propose change with rationale in a pull request
2. Update this file with new version number
3. Verify consistency with dependent templates
   (plan-template, spec-template, tasks-template)
4. Document changes in the Sync Impact Report header

**Versioning policy**: MAJOR for principle removal or redefinition,
MINOR for new principle or material expansion, PATCH for wording
and clarification fixes.

**Compliance review**: every implementation plan MUST include a
Constitution Check section that verifies alignment with these
principles before work begins.

**Version**: 1.1.0 | **Ratified**: 2026-03-04 | **Last Amended**: 2026-03-04
