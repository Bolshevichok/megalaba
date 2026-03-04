# Implementation Plan: Backend API Foundation

**Branch**: `001-backend-api-foundation` | **Date**: 2026-03-04 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-backend-api-foundation/spec.md`

## Summary

Создать основу backend-сервиса на FastAPI: все REST-роуты по
`docs/api_specification.md`, подключение к БД через SQLAlchemy,
ORM-модели по `docs/database_design.md`, Pydantic-схемы для
валидации. Пока БД недоступна — сервисный слой работает через
in-memory моки. Структура папок минимальна (≤15 файлов).

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: FastAPI, SQLAlchemy 2.0, Pydantic v2, uvicorn
**Storage**: PostgreSQL (через SQLAlchemy sync sessions); моки пока БД нет
**Testing**: pytest + httpx (AsyncClient для FastAPI)
**Target Platform**: Linux/macOS (Docker container)
**Project Type**: Web service (REST API)
**Performance Goals**: Health endpoint <100ms, startup <5s
**Constraints**: ≤15 source files (excluding tests), minimal folder nesting
**Scale/Scope**: 10+ concurrent IoT devices, 4 core entities

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Layered Architecture | ✅ PASS | Backend — отдельный слой, общается с frontend через REST, с БД через SQL |
| II. MQTT-First | ✅ N/A | MQTT вне скоупа этой фичи (будет добавлен позже) |
| III. Containerized Services | ✅ PASS | Dockerfile не в скоупе, но код готов к контейнеризации |
| IV. Data Integrity | ✅ PASS | ORM-модели соответствуют `docs/database_design.md`, lifecycle статусов actuator учтён |
| V. Security by Default | ✅ PASS | JWT auth роуты определены, Pydantic валидация, CORS настроен, bcrypt для паролей |
| VI. Simplicity | ✅ PASS | ≤15 файлов, нет лишних абстракций, моки вместо сложной инфраструктуры |
| VII. Observability | ✅ PASS | Health endpoint включён, structured logging запланирован |
| VIII. Device Resilience | ✅ N/A | Backend-only: last_seen поле в Device модели, остальное — IoT firmware |
| IX. Contract Stability | ✅ PASS | Роуты строго по `docs/api_specification.md`, URL versioning `/api/v1/` |

**Gate result**: PASS — все применимые принципы соблюдены.

## Project Structure

### Documentation (this feature)

```text
specs/001-backend-api-foundation/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── api-routes.md
└── tasks.md
```

### Source Code (repository root)

```text
backend/
├── app/
│   ├── __init__.py
│   ├── main.py          # FastAPI app, CORS, routers, startup
│   ├── config.py         # Pydantic Settings (env vars)
│   ├── database.py       # SQLAlchemy engine, session factory
│   ├── models.py         # All ORM models (User, Device, SensorReading, ActuatorCommand)
│   ├── schemas.py        # All Pydantic request/response schemas
│   ├── services.py       # Business logic + mock fallback
│   ├── dependencies.py   # FastAPI dependencies (get_db, get_current_user)
│   └── routes/
│       ├── __init__.py
│       ├── health.py     # GET /api/v1/health
│       ├── auth.py       # /api/v1/auth/*
│       ├── devices.py    # /api/v1/devices/*
│       ├── sensors.py    # /api/v1/devices/{id}/sensors/*
│       ├── actuators.py  # /api/v1/devices/{id}/actuators/*
│       └── dashboard.py  # /api/v1/dashboard/*
├── requirements.txt
└── tests/
```

**Structure Decision**: Flat backend structure grouped by concern.
Все модели в одном файле `models.py`, все схемы в `schemas.py`,
все сервисы в `services.py`. Роуты разнесены по файлам в `routes/`
для читаемости. Итого: **15 source файлов** (включая `__init__.py`).

## Complexity Tracking

Нет нарушений конституции — секция не требуется.
