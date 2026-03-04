# Research: Backend API Foundation

**Date**: 2026-03-04
**Feature**: 001-backend-api-foundation

## R1: SQLAlchemy session management в FastAPI

**Decision**: Использовать SQLAlchemy 2.0 с синхронными сессиями
через `sessionmaker` и FastAPI dependency `get_db` с `yield`.

**Rationale**: Синхронный подход проще для MVP. Async можно добавить
позже без изменения интерфейсов. FastAPI поддерживает sync endpoints.

**Alternatives considered**:
- Async SQLAlchemy (`create_async_engine`) — сложнее дебажить,
  не даёт выигрыша при текущей нагрузке (≤10 devices)
- Raw SQL — нарушает Constitution V (MUST use ORM)

## R2: Mock-стратегия при отсутствии БД

**Decision**: Абстрагировать доступ к данным через функции в
`services.py`. При недоступности БД (или для разработки) —
использовать переменную окружения `USE_MOCK_DB=true`, которая
переключает `get_db` dependency на in-memory словарь.

**Rationale**: Единая точка переключения, не требует менять роуты.
Моки возвращают данные в формате, идентичном реальным ORM-объектам.

**Alternatives considered**:
- SQLite in-memory — требует миграций, сложнее для stub-фазы
- Отдельный mock-сервис — overengineering (нарушает Constitution VI)
- Фабрика с protocol/ABC — чрезмерная абстракция для 4 сущностей

## R3: Pydantic v2 schema organization

**Decision**: Все схемы в одном файле `schemas.py`, группировка
по сущности через комментарии. Отдельные Create/Update/Response
модели для каждой сущности.

**Rationale**: ≤15 файлов constraint. При 4 сущностях × 3 схемы =
12 классов — помещается в один файл.

**Alternatives considered**:
- Отдельный файл на сущность (`schemas/device.py`) — нарушает
  constraint на количество файлов
- Один общий BaseSchema — нет общих полей между сущностями

## R4: Структура роутов

**Decision**: Каждая ресурсная группа — отдельный файл в `routes/`.
Все роутеры регистрируются в `main.py` через `include_router`.

**Rationale**: Роуты — единственное место, где файловое разделение
оправдано: разные эндпоинты, разные команды разработчиков. 6 файлов
роутов + `__init__.py` = 7 файлов, укладывается в бюджет.

**Alternatives considered**:
- Один файл `routes.py` — слишком большой (>30 эндпоинтов)
- Разделение по feature (devices/, sensors/) — глубокий nesting

## R5: JWT authentication approach

**Decision**: Использовать `python-jose` для JWT и `passlib[bcrypt]`
для хеширования паролей. FastAPI `Depends(get_current_user)` как
dependency для защищённых роутов.

**Rationale**: Стандартный подход для FastAPI, минимум зависимостей.
Соответствует Constitution V (JWT + bcrypt).

**Alternatives considered**:
- `PyJWT` — менее features, но тоже вариант; `python-jose` шире
  поддерживается в FastAPI-экосистеме
- OAuth2 сервер — overengineering для MVP
