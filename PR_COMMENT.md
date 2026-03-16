## Wokwi IoT Devices — интеграция с бэкендом

### Что сделано

Добавлена папка `wokwi/` с PlatformIO-проектом для ESP32 устройств, которые подключаются к бэкенду через MQTT.

**3 типа устройств (шаблоны):**

| Тип | Сенсоры | Актуаторы | Папка |
|-----|---------|-----------|-------|
| `climate-sensor` | DHT22 (температура + влажность) | — | `wokwi/device-types/climate-sensor/` |
| `light-controller` | LDR (освещённость) | LED (свет) | `wokwi/device-types/light-controller/` |
| `full-greenhouse` | DHT22 + LDR | LED | `wokwi/device-types/full-greenhouse/` |

Каждый тип — это "класс": `diagram.json` (схема) + `wokwi.toml` (ссылка на прошивку). Один общий исходник `src/main.cpp` с условной компиляцией (`#if HAS_DHT`, `#if HAS_LDR`, `#if HAS_LED`).

**Проверено:** climate-sensor подключён к бэкенду, данные температуры/влажности приходят в БД каждые 5 секунд, отображаются через API и dashboard.

---

### Для фронтенда: как создавать устройства

#### 1. Типы устройств

На фронте при создании устройства пользователь выбирает **тип**. Каждый тип определяет набор сенсоров и актуаторов:

```
climate-sensor    → sensors: [temperature, humidity]
light-controller  → sensors: [light],           actuators: [lighting]
full-greenhouse   → sensors: [temperature, humidity, light], actuators: [lighting]
```

#### 2. API-флоу создания устройства

```
POST /api/v1/greenhouses/{id}/devices
  body: { "name": "My Sensor", "connection_type": "wifi" }
  → response: { "id": 5, ... }
```

После создания device — привязать сенсоры/актуаторы. Пока через SQL (TODO: сделать API):

```sql
-- Для climate-sensor (device_id=5):
INSERT INTO sensors (device_id, sensor_type_id, unit) VALUES
  (5, 1, '°C'),  -- temperature
  (5, 2, '%');    -- humidity

-- Для light-controller (device_id=5):
INSERT INTO sensors (device_id, sensor_type_id, unit) VALUES
  (5, 3, 'lux');  -- light
INSERT INTO actuators (device_id, actuator_type_id, status) VALUES
  (5, 1, 'off');  -- lighting

-- Для full-greenhouse (device_id=5):
INSERT INTO sensors (device_id, sensor_type_id, unit) VALUES
  (5, 1, '°C'), (5, 2, '%'), (5, 3, 'lux');
INSERT INTO actuators (device_id, actuator_type_id, status) VALUES
  (5, 1, 'off');
```

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
pio run -e climate-sensor

# 3. Поднять бэкенд
docker compose up -d

# 4. Открыть wokwi/device-types/climate-sensor/ в VS Code
#    F1 → "Wokwi: Start Simulator"
#    (нужен Wokwi VS Code Extension + API ключ)

# 5. Менять DEVICE_ID в platformio.ini под свой device
```

### TODO
- [ ] API для создания сенсоров/актуаторов при создании устройства (сейчас через SQL)
- [ ] Эндпоинт `/api/v1/device-types` — список доступных типов с их сенсорами/актуаторами
- [ ] На фронте: форма создания устройства с выбором типа
