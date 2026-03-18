## Wokwi IoT Devices — интеграция с бэкендом

### Что сделано

Добавлена папка `wokwi/` с PlatformIO-проектом для ESP32 устройств, которые подключаются к бэкенду через MQTT.

**Модульная архитектура: 7 типов устройств (каждый сенсор/актуатор — отдельное устройство):**

| Тип | Описание | Сенсоры | Актуаторы | Папка |
|-----|----------|---------|-----------|-------|
| `temperature-sensor` | Датчик температуры | DHT22 (температура) | — | `wokwi/device-types/temperature-sensor/` |
| `humidity-sensor` | Датчик влажности воздуха | DHT22 (влажность) | — | `wokwi/device-types/humidity-sensor/` |
| `light-sensor` | Датчик освещённости | LDR (люксы) | — | `wokwi/device-types/light-sensor/` |
| `watering-actuator` | Система полива | — | Насос | `wokwi/device-types/watering-actuator/` |
| `heating-actuator` | Система обогрева | — | Нагреватель | `wokwi/device-types/heating-actuator/` |
| `ventilation-actuator` | Система проветривания | — | Вентилятор | `wokwi/device-types/ventilation-actuator/` |
| `lighting-actuator` | Система освещения | — | LED | `wokwi/device-types/lighting-actuator/` |

Каждый тип — это отдельная папка с `diagram.json` (схема подключения) + `wokwi.toml` (путь к прошивке). Один общий исходник `src/main.cpp` с условной компиляцией через `#if` флаги (`HAS_DHT_TEMP`, `HAS_DHT_HUMID`, `HAS_LDR`, `HAS_LED`, `HAS_WATER_PUMP`, `HAS_HEATER`, `HAS_FAN`).

**Проверено:** устройства подключаются к бэкенду через MQTT, данные приходят в БД каждые 5 секунд, отображаются через API и dashboard.

---

### Для фронтенда: как создавать устройства

#### 1. Типы устройств

На фронте при создании устройства пользователь выбирает **тип**. Каждый тип определяет набор сенсоров и актуаторов:

```
temperature-sensor    → sensors: [temperature]
humidity-sensor       → sensors: [humidity]
light-sensor          → sensors: [light]
watering-actuator     → actuators: [watering]
heating-actuator      → actuators: [heating]
ventilation-actuator  → actuators: [ventilation]
lighting-actuator     → actuators: [lighting]
```

#### 2. API-флоу создания устройства

```
POST /api/v1/greenhouses/{id}/devices
  body: { "name": "My Sensor", "device_type": "temperature-sensor", "connection_type": "wifi" }
  → response: { "id": 5, "name": "My Sensor", "device_type": "temperature-sensor", ... }
```

Бэкенд автоматически создаёт сенсоры/актуаторы согласно шаблону типа (`DEVICE_TYPE_TEMPLATES` в `models.py`).

#### 3. Справочник type ID

| sensor_type_id | name | unit |
|---------------|------|------|
| 1 | temperature | °C |
| 2 | humidity | % |
| 3 | light | lux |

| actuator_type_id | name |
|-----------------|------|
| 1 | lighting |
| 2 | heating |
| 3 | ventilation |
| 4 | watering |

#### 4. Чтение данных

```
GET /api/v1/sensors/{sensor_id}/readings?limit=10   — показания сенсора
GET /api/v1/dashboard/overview                       — сводка по всем теплицам
GET /api/v1/greenhouses/{id}/devices                 — список устройств
POST /api/v1/actuators/{id}/commands                 — отправить команду
  body: { "command": "on" }
```

#### 5. WebSocket (real-time)

```
ws://localhost:8000/ws/greenhouse/{greenhouse_id}
```

Приходят обновления при каждом новом показании сенсора.

---

### Как запустить Wokwi-устройство локально

```bash
# 1. Установить PlatformIO (если нет)
pip install platformio

# 2. Собрать прошивку (первый раз ~5 мин, потом ~10 сек)
cd wokwi

# Сенсоры:
pio run -e temperature-sensor
pio run -e humidity-sensor
pio run -e light-sensor

# Актуаторы:
pio run -e watering-actuator
pio run -e heating-actuator
pio run -e ventilation-actuator
pio run -e lighting-actuator

# 3. Поднять бэкенд
docker compose up -d

# 4. Открыть wokwi/device-types/<тип>/ в VS Code
#    F1 → "Wokwi: Start Simulator"
#    (нужен Wokwi VS Code Extension + API ключ)

# 5. Менять DEVICE_ID в platformio.ini под свой device
```

### MQTT топики

#### Сенсоры (ESP32 → Бэкенд)
- `devices/{id}/sensors/temperature` — температура (°C)
- `devices/{id}/sensors/humidity` — влажность воздуха (%)
- `devices/{id}/sensors/light` — освещённость (lux)

#### Актуаторы (Бэкенд → ESP32)
- `devices/{id}/commands/watering` — команда поливу
- `devices/{id}/commands/heating` — команда обогреву
- `devices/{id}/commands/ventilation` — команда вентиляции
- `devices/{id}/commands/lighting` — команда освещению

#### Статусы (ESP32 → Бэкенд)
- `devices/{id}/status/watering` — статус полива
- `devices/{id}/status/heating` — статус обогрева
- `devices/{id}/status/ventilation` — статус вентиляции
- `devices/{id}/status/lighting` — статус освещения

---

### TODO
- [x] API для создания сенсоров/актуаторов при создании устройства (auto-provisioning через `device_type`)
- [x] Эндпоинт `/api/v1/device-types` — список доступных типов с их сенсорами/актуаторами
- [ ] На фронте: форма создания устройства с выбором типа
