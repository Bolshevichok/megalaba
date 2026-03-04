<!--
Sync Impact Report
===================
Version change: 0.0.0 → 1.0.0 (initial ratification)
Modified principles: N/A (first version)
Added sections:
  - Core Principles (6 principles)
  - Technology Stack Constraints
  - Development Workflow & Quality Gates
  - Governance
Removed sections: N/A
Templates requiring updates:
  - .specify/templates/plan-template.md — ✅ no update needed (Constitution Check section is generic)
  - .specify/templates/spec-template.md — ✅ no update needed (requirements section aligns)
  - .specify/templates/tasks-template.md — ✅ no update needed (phase structure compatible)
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
pending → sent → confirmed | failed.

Rationale: reliable data persistence is critical for monitoring
history, analytics, and audit trail of device commands.

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

**Version**: 1.0.0 | **Ratified**: 2026-03-04 | **Last Amended**: 2026-03-04
