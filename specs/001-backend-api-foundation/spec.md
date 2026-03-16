# Feature Specification: Backend API — Умная Теплица

**Feature Branch**: `001-backend-api-foundation`
**Created**: 2026-03-04
**Updated**: 2026-03-10
**Status**: Draft
**Input**: User description: "Разработать backend сервиса умной теплицы на основе артефактов проекта и обновлённой БД. PostgreSQL, контейнеризация Docker. Без избыточного кода, умеренное разделение по пакетам. Google docstring на все классы, методы и функции."

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Регистрация и аутентификация (Priority: P1)

Пользователь регистрируется в системе, входит с логином/паролем и получает JWT-токен. Все защищённые эндпоинты отклоняют запросы без валидного токена.

**Why this priority**: Без аутентификации невозможна привязка данных к пользователю — все остальные сценарии зависят от этого.

**Independent Test**: Зарегистрировать пользователя, залогиниться, вызвать защищённый эндпоинт с токеном и без.

**Acceptance Scenarios**:

1. **Given** валидные данные, **When** `POST /api/v1/auth/register`, **Then** пользователь создан (201), пароль захеширован
2. **Given** зарегистрированный пользователь, **When** `POST /api/v1/auth/login`, **Then** возвращается access_token и refresh_token (200)
3. **Given** истёкший access_token, **When** `POST /api/v1/auth/refresh` с валидным refresh_token, **Then** возвращается новый access_token (200)
4. **Given** отсутствие токена, **When** вызов защищённого эндпоинта, **Then** ответ 401 Unauthorized
5. **Given** валидный токен, **When** `GET /api/v1/auth/me`, **Then** возвращается профиль текущего пользователя (200)

---

### User Story 2 — Управление теплицами (Priority: P1)

Пользователь создаёт, просматривает, редактирует и удаляет свои теплицы. Каждая теплица принадлежит конкретному пользователю, чужие теплицы недоступны.

**Why this priority**: Теплица — корневая сущность иерархии, без неё невозможно добавлять устройства.

**Independent Test**: Создать теплицу, получить список, обновить, удалить. Проверить изоляцию данных между пользователями.

**Acceptance Scenarios**:

1. **Given** авторизованный пользователь, **When** `POST /api/v1/greenhouses`, **Then** теплица создана (201) и привязана к user_id
2. **Given** авторизованный пользователь с теплицами, **When** `GET /api/v1/greenhouses`, **Then** возвращается список только его теплиц (200)
3. **Given** теплица другого пользователя, **When** `GET /api/v1/greenhouses/{id}`, **Then** ответ 404
4. **Given** существующая теплица, **When** `DELETE /api/v1/greenhouses/{id}`, **Then** теплица удалена каскадно (204)

---

### User Story 3 — Управление устройствами (Priority: P1)

Пользователь добавляет устройства в теплицу, просматривает их список и детали (включая датчики и актуаторы), обновляет и удаляет устройства.

**Why this priority**: Устройства связывают теплицу с датчиками и актуаторами — центральное звено архитектуры.

**Independent Test**: Создать устройство в теплице, получить список устройств, получить детали устройства с датчиками/актуаторами.

**Acceptance Scenarios**:

1. **Given** существующая теплица, **When** `POST /api/v1/greenhouses/{id}/devices`, **Then** устройство создано (201)
2. **Given** теплица с устройствами, **When** `GET /api/v1/greenhouses/{id}/devices`, **Then** список устройств (200)
3. **Given** устройство с датчиками и актуаторами, **When** `GET /api/v1/greenhouses/{gid}/devices/{did}`, **Then** ответ содержит sensors[] и actuators[] (200)
4. **Given** устройство с привязанными данными, **When** `DELETE /api/v1/greenhouses/{gid}/devices/{did}`, **Then** каскадное удаление (204)

---

### User Story 4 — Показания датчиков (Priority: P1)

Система принимает и хранит показания датчиков. Пользователь может запросить историю показаний с фильтрацией по времени и агрегацией.

**Why this priority**: Мониторинг показаний — основная задача системы умной теплицы.

**Independent Test**: Добавить показание через API, запросить историю с параметрами start_time, end_time, limit.

**Acceptance Scenarios**:

1. **Given** существующий датчик, **When** `POST /api/v1/sensors/{id}/readings` с value и recorded_at, **Then** показание сохранено (201)
2. **Given** датчик с показаниями, **When** `GET /api/v1/sensors/{id}/readings?limit=50`, **Then** возвращаются последние 50 показаний со статистикой min/max/avg (200)
3. **Given** параметры start_time и end_time, **When** запрос показаний, **Then** возвращаются только показания в указанном диапазоне

---

### User Story 5 — Управление актуаторами и команды (Priority: P1)

Пользователь отправляет команды актуаторам (on/off/set_value). Команды сохраняются в журнал, публикуются в MQTT-топик для доставки на ESP32-устройство. Можно просмотреть историю команд.

**Why this priority**: Управление актуаторами — вторая ключевая функция после мониторинга.

**Independent Test**: Отправить команду актуатору, проверить сохранение в БД и публикацию в MQTT, запросить историю команд.

**Acceptance Scenarios**:

1. **Given** существующий актуатор, **When** `POST /api/v1/actuators/{id}/commands` с command="on", **Then** команда сохранена, статус актуатора обновлён, сообщение опубликовано в MQTT (202)
2. **Given** команда set_value, **When** value указан, **Then** команда сохранена с числовым значением и опубликована в MQTT
3. **Given** актуатор с историей команд, **When** `GET /api/v1/actuators/{id}/commands`, **Then** список команд с пагинацией (200)

---

### User Story 6 — MQTT-интеграция (Priority: P1)

Бэкенд подключается к MQTT-брокеру (Mosquitto) и обрабатывает двусторонний обмен данными с IoT-устройствами. Входящие сообщения от датчиков сохраняются в БД. Команды актуаторам публикуются в соответствующие топики.

**Why this priority**: MQTT — основной протокол связи с ESP32-устройствами, без него нет IoT-функциональности.

**Independent Test**: Опубликовать сообщение в MQTT-топик датчика, проверить сохранение в sensor_readings. Отправить команду актуатору через API, проверить публикацию в MQTT.

**Acceptance Scenarios**:

1. **Given** бэкенд подключён к Mosquitto, **When** ESP32 публикует показание в `devices/{device_id}/sensors/{type}`, **Then** бэкенд получает сообщение и сохраняет в sensor_readings
2. **Given** команда актуатору через API, **When** команда сохранена в БД, **Then** бэкенд публикует в `devices/{device_id}/commands/{actuator_type}`
3. **Given** ESP32 публикует статус в `devices/{device_id}/status/{actuator_type}`, **When** бэкенд получает сообщение, **Then** статус актуатора обновляется в БД
4. **Given** Mosquitto недоступен, **When** бэкенд стартует, **Then** бэкенд переподключается с экспоненциальным backoff

---

### User Story 7 — WebSocket real-time обновления (Priority: P1)

Фронтенд подключается по WebSocket и получает обновления показаний датчиков, статусов актуаторов и устройств в реальном времени.

**Why this priority**: Real-time отображение данных — ключевое требование для мониторинга теплицы.

**Independent Test**: Подключиться к WebSocket, подождать поступления данных от эмулятора/MQTT, проверить формат сообщений.

**Acceptance Scenarios**:

1. **Given** клиент подключён к `ws://localhost:8000/ws/greenhouse/{id}`, **When** приходит новое показание датчика, **Then** клиент получает сообщение типа `sensor_update`
2. **Given** клиент подключён, **When** статус актуатора меняется, **Then** клиент получает сообщение типа `actuator_update`
3. **Given** клиент подключён, **When** устройство меняет статус online/offline, **Then** клиент получает сообщение типа `device_status`
4. **Given** WebSocket-подключение, **When** первое сообщение содержит auth-токен, **Then** подключение авторизовано для данной теплицы

---

### User Story 8 — Программный эмулятор IoT-устройств (Priority: P2)

Эмулятор работает как asyncio background task внутри FastAPI. Генерирует реалистичные показания для 3 типов датчиков (temperature, humidity, light) по математическим моделям, реагирует на команды актуаторов и записывает данные в БД. Управляется через REST API (start/stop/status/config).

**Why this priority**: Дополнительный инструмент для разработки и тестирования без запуска Wokwi. Не заменяет ESP32+MQTT.

**Independent Test**: Запустить эмулятор через `POST /api/v1/simulator/start`, подождать, проверить появление записей в sensor_readings.

**Acceptance Scenarios**:

1. **Given** эмулятор остановлен, **When** `POST /api/v1/simulator/start`, **Then** эмулятор запускается и генерирует показания в БД
2. **Given** эмулятор работает, **When** `POST /api/v1/simulator/stop`, **Then** генерация прекращается
3. **Given** эмулятор работает, **When** `GET /api/v1/simulator/status`, **Then** возвращается uptime, devices_count, readings_generated
4. **Given** эмулятор работает и актуатор обогрева включён, **When** следующий цикл генерации, **Then** температура постепенно растёт согласно модели

---

### User Story 9 — Дашборд (Priority: P2)

Оператор получает сводку по всем теплицам, устройствам, их статусам и последним показаниям в одном запросе.

**Why this priority**: Агрегация данных — удобство; всё доступно через отдельные эндпоинты.

**Independent Test**: Вызвать `GET /api/v1/dashboard/overview` и проверить структуру ответа.

**Acceptance Scenarios**:

1. **Given** пользователь с теплицами и устройствами, **When** `GET /api/v1/dashboard/overview`, **Then** ответ содержит summary (total_greenhouses, total_devices, online/offline) и вложенные данные по теплицам (200)

---

### User Story 10 — Автоматизационные скрипты (Priority: P2)

Пользователь создаёт, просматривает, обновляет и удаляет скрипты автоматизации для теплицы.

**Why this priority**: Скрипты — дополнительная функциональность, CRUD без движка исполнения.

**Independent Test**: CRUD-операции над скриптами в рамках теплицы.

**Acceptance Scenarios**:

1. **Given** существующая теплица, **When** `POST /api/v1/greenhouses/{id}/scripts`, **Then** скрипт создан (201)
2. **Given** скрипт существует, **When** `PUT /api/v1/scripts/{id}`, **Then** скрипт обновлён (200)
3. **Given** скрипт существует, **When** `DELETE /api/v1/scripts/{id}`, **Then** скрипт удалён (204)

---

### User Story 11 — Контейнеризация (Priority: P1)

Разработчик запускает всю систему через `docker compose up` — поднимаются PostgreSQL, Mosquitto, backend (FastAPI), и приложение готово к работе.

**Why this priority**: Контейнеризация обеспечивает воспроизводимость среды и простоту запуска.

**Independent Test**: `docker compose up --build` — все сервисы запускаются, health check проходит, MQTT-брокер доступен.

**Acceptance Scenarios**:

1. **Given** чистая машина с Docker, **When** `docker compose up --build`, **Then** PostgreSQL, Mosquitto и backend запускаются, миграции применяются
2. **Given** запущенные контейнеры, **When** `GET /api/v1/health`, **Then** ответ 200 с информацией о статусе БД и MQTT
3. **Given** Mosquitto запущен, **When** MQTT-клиент подключается к порту 1883, **Then** подключение успешно

---

### Edge Cases

- Что если запрос содержит невалидный JSON? → 422 с описанием ошибки валидации
- Что если БД недоступна при CRUD-операции? → 503 Service Unavailable
- Что если пользователь пытается получить чужую теплицу? → 404 Not Found (не 403, чтобы не раскрывать существование)
- Что если команда актуатору содержит невалидный command? → 422 с ошибкой
- Что если limit/offset отрицательные? → Значения приводятся к допустимым границам или 400
- Что если refresh_token просрочен? → 401 с кодом TOKEN_EXPIRED
- Что если команда отправляется на offline-устройство? → 409 Conflict с кодом DEVICE_OFFLINE (Constitution VIII: команды на offline-устройства MUST быть отклонены)
- Что если WebSocket-клиент не прислал auth-токен? → Соединение закрывается с кодом 4001
- Что если эмулятор уже запущен и приходит повторный POST /simulator/start? → Ответ с текущим статусом, повторный запуск не происходит

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Система ДОЛЖНА предоставлять эндпоинт `GET /api/v1/health` с информацией о статусе сервиса, БД и MQTT
- **FR-002**: Система ДОЛЖНА реализовать полный auth-flow: register, login, refresh, me (JWT)
- **FR-003**: Система ДОЛЖНА предоставлять полный CRUD для теплиц (`/api/v1/greenhouses`) с привязкой к текущему пользователю
- **FR-004**: Система ДОЛЖНА предоставлять полный CRUD для устройств (`/api/v1/greenhouses/{id}/devices`) с фильтрацией по статусу
- **FR-005**: Система ДОЛЖНА предоставлять эндпоинты для создания датчиков и получения списка датчиков устройства
- **FR-006**: Система ДОЛЖНА сохранять показания датчиков и возвращать историю с фильтрацией по времени и статистикой (min/max/avg)
- **FR-007**: Система ДОЛЖНА предоставлять эндпоинты для создания актуаторов и получения списка актуаторов устройства
- **FR-008**: Система ДОЛЖНА принимать команды актуаторов (on/off/set_value), сохранять в журнал, обновлять статус актуатора и публиковать в MQTT
- **FR-009**: Система ДОЛЖНА предоставлять историю команд актуатора с пагинацией
- **FR-010**: Система ДОЛЖНА предоставлять эндпоинт дашборда с агрегированными данными
- **FR-011**: Система ДОЛЖНА предоставлять CRUD для скриптов автоматизации в рамках теплицы
- **FR-012**: Система ДОЛЖНА валидировать все входные данные через Pydantic-схемы и возвращать 422 при ошибках
- **FR-013**: Система ДОЛЖНА возвращать стандартизированные ошибки с полями error.code, error.message, error.timestamp
- **FR-014**: Система ДОЛЖНА определить ORM-модели для всех 10 таблиц БД с корректными связями и каскадным удалением
- **FR-015**: Система ДОЛЖНА управлять миграциями БД через Alembic
- **FR-016**: Система ДОЛЖНА настроить CORS для фронтенд-origin
- **FR-017**: Система ДОЛЖНА быть контейнеризирована через Docker Compose (PostgreSQL + Mosquitto + backend)
- **FR-018**: Все классы, методы и функции ДОЛЖНЫ иметь документацию в формате Google docstring
- **FR-019**: Система ДОЛЖНА подключаться к MQTT-брокеру (Mosquitto) через Paho-MQTT и подписываться на топики `devices/+/sensors/+` и `devices/+/status/+`
- **FR-020**: Система ДОЛЖНА публиковать команды актуаторов в MQTT-топики `devices/{device_id}/commands/{actuator_type}`
- **FR-021**: Система ДОЛЖНА обрабатывать входящие MQTT-сообщения от датчиков и сохранять показания в sensor_readings
- **FR-022**: Система ДОЛЖНА предоставлять WebSocket-эндпоинт `ws://host/ws/greenhouse/{id}` для real-time обновлений
- **FR-023**: WebSocket ДОЛЖЕН транслировать события: sensor_update, actuator_update, device_status
- **FR-024**: WebSocket ДОЛЖЕН требовать аутентификацию через JWT-токен в первом сообщении
- **FR-025**: Система ДОЛЖНА включать программный эмулятор IoT-устройств как asyncio background task
- **FR-026**: Эмулятор ДОЛЖЕН генерировать показания по математическим моделям для 3 типов датчиков: temperature, humidity, light
- **FR-027**: Эмулятор ДОЛЖЕН реагировать на команды актуаторов (обогрев → температура ↑, полив → влажность почвы ↑, и т.д.)
- **FR-028**: Эмулятор ДОЛЖЕН управляться через REST API: start, stop, status

### MQTT-топики (из Miro)

**1. Данные с датчиков** (публикует ESP32, подписывается Backend):
- `devices/{device_id}/sensors/light` — данные об освещённости
- `devices/{device_id}/sensors/temperature` — данные о температуре
- `devices/{device_id}/sensors/humidity` — данные о влажности почвы/воздуха

**2. Команды управления** (публикует Backend, подписывается ESP32):
- `devices/{device_id}/commands/lighting` — управление освещением
- `devices/{device_id}/commands/heating` — управление подогревом
- `devices/{device_id}/commands/ventilation` — управление проветриванием
- `devices/{device_id}/commands/watering` — управление поливом

**3. Статусы актуаторов** (публикует ESP32, подписывается Backend):
- `devices/{device_id}/status/lighting` — текущее состояние освещения
- `devices/{device_id}/status/heating` — текущее состояние подогрева
- `devices/{device_id}/status/ventilation` — текущее состояние проветривания
- `devices/{device_id}/status/watering` — текущее состояние полива

**Формат payload (JSON):**
- Датчики: `{"value": <float>, "unit": "<string>", "timestamp": "<ISO8601>"}`
- Команды: `{"command": "<on|off|set_value>", "value": <float|null>}`
- Статусы: `{"status": "<on|off>", "timestamp": "<ISO8601>"}`

### Key Entities

- **User**: Оператор системы — name, email, password_hash, billing_address, phone
- **Greenhouse**: Теплица пользователя — name, location. Связь: user → greenhouses (1:N)
- **Device**: IoT-устройство в теплице — name, connection_type (wifi/gsm/ethernet/zigbee), ip_address, status (online/offline). Связь: greenhouse → devices (1:N)
- **SensorType**: Справочник типов датчиков — name
- **Sensor**: Датчик на устройстве — name, unit, sensor_type_id. Связь: device → sensors (1:N)
- **SensorReading**: Показание датчика — value, recorded_at. Связь: sensor → readings (1:N)
- **ActuatorType**: Справочник типов актуаторов — name
- **Actuator**: Актуатор на устройстве — status (on/off), actuator_type_id. Связь: device → actuators (1:N)
- **ActuatorCommand**: Команда актуатору — command (on/off/set_value), value, created_at. Связь: actuator → commands (1:N)
- **Script**: Скрипт автоматизации — name, script_code, enabled. Связь: greenhouse → scripts (1:N)

### Assumptions

- Основной IoT-уровень — ESP32 + Wokwi + MQTT. Бэкенд реализует MQTT-клиент (Paho-MQTT) для связи с устройствами
- Программный эмулятор — дополнительный инструмент для разработки/тестирования без Wokwi, пишет в БД напрямую
- Frontend — отдельная фича, не входит в эту спецификацию
- Миграции Alembic создаются на основе `db_create.sql` — схема уже определена
- MQTT QoS: данные датчиков — QoS 0, команды — QoS 1, статусы — QoS 1
- Docker Compose включает PostgreSQL, Mosquitto и backend
- Код пишется без избыточных абстракций: умеренное разделение по пакетам, без чрезмерного Clean Code

## Clarifications

### Session 2026-03-04

- Q: Глубина реализации роутов — заглушки или реальный сервисный слой? → A: Вариант B — реальный сервисный слой с SQLAlchemy-сессиями; пока БД недоступна, использовать моки (in-memory или фикстуры) для возврата данных

### Session 2026-03-10

- Q: Miro определяет 3 MQTT-топика датчиков (light, temperature, humidity), но эмулятор описывает 6 типов (+ soil_moisture, ph, co2). Сколько типов реализовывать? → A: Только 3 типа из Miro (light, temperature, humidity) — для MQTT и эмулятора. Остальные добавить позже при необходимости.
- Q: Формат JSON-сообщений MQTT (payload от ESP32 и к ESP32)? → A: `{"value": <float>, "unit": "<string>", "timestamp": "<ISO8601>"}`

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Все определённые API-эндпоинты отвечают корректными HTTP-кодами (нет 500 на валидных запросах)
- **SC-002**: Приложение стартует менее чем за 5 секунд, health-эндпоинт отвечает за < 100ms
- **SC-003**: Все ответы соответствуют структурам из `docs/api_specification.md`
- **SC-004**: ORM-модели покрывают все 10 таблиц из `db_create.sql` с корректными типами и связями
- **SC-005**: `docker compose up --build` поднимает PostgreSQL + Mosquitto + backend без ручного вмешательства
- **SC-006**: Миграции Alembic применяются автоматически и создают все таблицы и ENUM-типы
- **SC-007**: Изоляция данных: пользователь A не видит теплицы пользователя B
- **SC-008**: Все классы, методы и функции имеют Google docstring
- **SC-009**: MQTT-клиент подключается к Mosquitto и обрабатывает входящие сообщения от датчиков
- **SC-010**: WebSocket-эндпоинт транслирует обновления подключённым клиентам в реальном времени
- **SC-011**: Эмулятор генерирует реалистичные показания, которые появляются в sensor_readings
