# Research: Backend API — Умная Теплица

**Date**: 2026-03-10
**Feature**: 001-backend-api-foundation

## R1: SQLAlchemy session management в FastAPI

**Decision**: Использовать SQLAlchemy 2.0 с синхронными сессиями через `sessionmaker` и FastAPI dependency `get_db` с `yield`.

**Rationale**: Синхронный подход проще для MVP. Async можно добавить позже без изменения интерфейсов. FastAPI поддерживает sync endpoints.

**Alternatives considered**:
- Async SQLAlchemy (`create_async_engine`) — сложнее дебажить, не даёт выигрыша при текущей нагрузке (≤10 devices)
- Raw SQL — нарушает Constitution V (MUST use ORM)

## R2: Paho-MQTT + asyncio интеграция в FastAPI

**Decision**: Использовать `paho-mqtt` с `loop_start()` в отдельном потоке, колбэки перебрасывают данные в asyncio через `asyncio.run_coroutine_threadsafe()`.

**Rationale**: Paho-MQTT использует свой event loop (thread-based). FastAPI работает на asyncio. `loop_start()` создаёт background thread для сетевого I/O, а колбэки `on_message` безопасно вызывают async-функции через bridge.

**Alternatives considered**:
- `aiomqtt` (asyncio-native MQTT client) — менее зрелый, меньше документации, не в списке зависимостей проекта
- `fastapi-mqtt` — обёртка над paho, добавляет лишнюю зависимость без значимых преимуществ
- Прямой вызов `loop_forever()` — блокирует event loop, непригоден для FastAPI

## R3: Lifecycle MQTT-клиента в FastAPI lifespan

**Decision**: Подключение в `lifespan` context manager. Отключение при shutdown.

**Rationale**: FastAPI lifespan — стандартный механизм для startup/shutdown задач. MQTT-клиент подключается при старте, подписывается на топики, отключается при остановке.

## R4: WebSocket broadcast архитектура

**Decision**: In-memory ConnectionManager с dict[greenhouse_id → set[WebSocket]]. При получении MQTT-сообщения — broadcast всем подключённым клиентам данной теплицы.

**Rationale**: Для масштаба проекта (10+ устройств, единичные клиенты) in-memory менеджер достаточен. Redis pub/sub избыточен.

**Alternatives considered**:
- Redis pub/sub для горизонтального масштабирования — избыточно для MVP
- SSE (Server-Sent Events) — однонаправленный, WebSocket уже в спеке

## R5: JWT authentication approach

**Decision**: Использовать `python-jose` для JWT и `passlib[bcrypt]` для хеширования паролей. FastAPI `Depends(get_current_user)` как dependency для защищённых роутов.

**Rationale**: Стандартный подход для FastAPI, минимум зависимостей. Соответствует Constitution V (JWT + bcrypt).

**Alternatives considered**:
- `PyJWT` — менее features; `python-jose` шире поддерживается в FastAPI-экосистеме
- OAuth2 сервер — overengineering для MVP

## R6: Actuator command lifecycle (Constitution gap IV)

**Decision**: Добавить колонку `status VARCHAR(20) DEFAULT 'pending'` в `actuator_commands` через Alembic-миграцию.

**Lifecycle**: pending → sent → confirmed | failed
- При создании команды через API: status = `pending`
- После публикации в MQTT: status = `sent`
- При получении подтверждения от ESP32: status = `confirmed`
- По таймауту (30s без подтверждения): status = `failed`

## R7: Device online/offline tracking (Constitution gap VIII)

**Decision**: Добавить `last_seen TIMESTAMPTZ` в таблицу `devices`. Устройство = online если `last_seen` < 60 секунд назад.

**Implementation**:
- Каждое MQTT-сообщение от устройства обновляет `last_seen`
- LWT-сообщение устанавливает `status = offline`
- Периодическая проверка (каждые 60s) помечает устройства с устаревшим `last_seen` как offline

## R8: Structured logging (Constitution gap VII)

**Decision**: Python `logging` с JSON formatter (`python-json-logger`). Middleware для request logging.

**Implementation**:
- JSON formatter для всех логов
- Request logging middleware: method, path, status_code, duration_ms
- MQTT events: message received, published, connection state changes

## R9: Программный эмулятор — математические модели

**Decision**: 3 типа датчиков с упрощёнными формулами из `docs/iot_device_emulation.md`.

**Models**:
- **Temperature**: `T(t) = T_base + A * sin(2π * t / period) + noise` (T_base=24°C, A=4°C, σ=0.3)
- **Humidity**: `H(t) = H_base - k * (T(t) - T_base) + noise` (H_base=70%, k=2.5, σ=1.0)
- **Light**: `L(t) = L_max * max(0, sin(π * (hour - sunrise) / daylight)) + artificial` (L_max=50000 lux)

**Actuator reactions**:
- Heating ON → temperature +0.5°C/cycle
- Ventilation ON → temperature decreases, humidity decreases
- Watering ON → humidity +5%/cycle
- Lighting ON → light += 5000-10000 lux

## R10: Alembic migration strategy

**Decision**: Автогенерация начальной миграции из ORM-моделей. Модели на основе `db_create.sql` + Constitution gaps (status, last_seen).

**Implementation**:
- `alembic revision --autogenerate -m "initial schema"`
- Entrypoint: `alembic upgrade head && uvicorn app.main:app`
- ENUM-типы через SQLAlchemy `Enum` type

## R11: Pydantic v2 schema organization

**Decision**: Все схемы в одном файле `schemas.py`, группировка по сущности через комментарии. Отдельные Create/Update/Response модели для каждой сущности.

**Rationale**: При 10 сущностях — один файл manageable. Пользователь просил умеренное разделение.

## R12: Структура роутов

**Decision**: Каждая ресурсная группа — отдельный файл в `routes/`. Все роутеры регистрируются в `main.py` через `include_router`.

**Rationale**: 30+ эндпоинтов в одном файле — нечитаемо. Разделение по доменам (auth, greenhouses, devices, sensors, actuators, scripts, dashboard, simulator, health) — оптимальный баланс.
