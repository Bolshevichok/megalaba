# Программный эмулятор IoT устройств (дополнительный инструмент)

## 1. Обзор

> **Основной IoT-уровень** проекта — ESP32 + Wokwi + MQTT. Данный эмулятор — **дополнительный инструмент** для разработки и тестирования бэкенда/фронтенда без запуска Wokwi. Он генерирует реалистичные показания датчиков, реагирует на команды актуаторов и записывает данные напрямую в БД.

### 1.1. Когда использовать эмулятор

| Ситуация | Что использовать |
|---|---|
| Полная интеграция, демонстрация IoT-архитектуры | ESP32 + Wokwi + MQTT |
| Разработка/отладка бэкенда без Wokwi | Программный эмулятор |
| Разработка/отладка фронтенда | Программный эмулятор |
| Автоматические тесты (CI) | Программный эмулятор |
| Нагрузочное тестирование (много устройств) | Программный эмулятор |

### 1.2. Почему не другие готовые эмуляторы

| Платформа | Причина |
|---|---|
| AWS IoT Device Simulator | Deprecated с января 2025 |
| Azure IoT Simulation | Привязка к Azure-экосистеме, избыточно |
| QEMU | Эмуляция аппаратного уровня — не наш случай |
| Bevywise IoT Simulator | Коммерческий, лишняя зависимость |

### 1.2. Полезные open-source примеры

- [leedskiy/IoT-simulator](https://github.com/leedskiy/IoT-simulator) — Python-симулятор умного дома (лампы, термостаты, камеры). Хороший пример архитектуры.
- [simple-iot-device (PyPI)](https://pypi.org/project/simple-iot-device/) — минималистичная Python-библиотека для симуляции IoT.
- [Synth (DevicePilot)](https://devicepilot-synth.readthedocs.io/en/latest/introduction.html) — генерация виртуальных устройств в масштабе.

---

## 2. Архитектура эмулятора

### 2.1. Подход: встроенный background task

Эмулятор работает как asyncio-задача внутри FastAPI lifespan. Никаких внешних процессов, брокеров или сетевых вызовов — прямые вызовы Python-функций и запись в ту же БД.

```
┌─────────────────────────────────────────────────────┐
│                   FastAPI Application                │
│                                                      │
│  ┌──────────────┐     ┌───────────────────────────┐  │
│  │  REST API     │     │  Simulator Engine          │  │
│  │  /sensors     │     │  (asyncio background task) │  │
│  │  /actuators   │     │                            │  │
│  │  /readings    │◄────┤  VirtualDevice[]           │  │
│  │  /commands    │     │    ├── Sensors              │  │
│  │  /simulator   │────►│    └── Actuators            │  │
│  └──────┬───────┘     └─────────┬─────────────────┘  │
│         │                       │                     │
│         ▼                       ▼                     │
│  ┌─────────────────────────────────────────────┐     │
│  │              PostgreSQL (SQLAlchemy)          │     │
│  │  sensor_readings | actuator_commands | ...    │     │
│  └─────────────────────────────────────────────┘     │
│         │                                             │
│         ▼                                             │
│  ┌──────────────┐                                    │
│  │  WebSocket    │──────► Frontend (real-time)        │
│  └──────────────┘                                    │
└─────────────────────────────────────────────────────┘
```

### 2.2. Интеграция в FastAPI

```python
# app/main.py
from contextlib import asynccontextmanager
from app.simulator.engine import SimulatorEngine

@asynccontextmanager
async def lifespan(app: FastAPI):
    engine = SimulatorEngine()
    task = asyncio.create_task(engine.run())
    yield
    task.cancel()

app = FastAPI(lifespan=lifespan)
```

### 2.3. Структура модуля

```
backend/app/simulator/
    __init__.py
    engine.py              # Главный движок, управляет циклом генерации
    devices.py             # Базовый класс VirtualDevice
    config.py              # Конфигурация виртуальных устройств
    sensors/
        __init__.py
        base.py            # Базовый класс VirtualSensor
        temperature.py     # Модель датчика температуры
        humidity.py        # Модель датчика влажности воздуха
        soil_moisture.py   # Модель датчика влажности почвы
        light.py           # Модель датчика освещённости
        ph.py              # Модель датчика pH почвы
        co2.py             # Модель датчика CO2
    actuators/
        __init__.py
        base.py            # Базовый класс VirtualActuator
        irrigation.py      # Система полива
        ventilation.py     # Вентиляция
        lighting.py        # Освещение
        heating.py         # Обогрев
```

---

## 3. Математические модели датчиков

### 3.1. Температура воздуха

```
T(t) = T_base + A * sin(2 * pi * t / period) + drift + noise
```

| Параметр | Значение | Описание |
|---|---|---|
| `T_base` | 22–25 °C | Целевая температура теплицы |
| `A` | 3–5 °C | Амплитуда суточного цикла |
| `period` | 86400 сек | Период (24 часа) |
| `drift` | random walk | Медленный случайный дрейф |
| `noise` | gaussian, σ ≈ 0.3 °C | Шум измерений |

Реакция на актуаторы:
- Обогрев ON → T постепенно растёт (+0.5 °C/мин до целевой)
- Вентиляция ON → T снижается к наружной температуре

### 3.2. Влажность воздуха

```
H(t) = H_base - k * (T(t) - T_base) + noise
```

| Параметр | Значение | Описание |
|---|---|---|
| `H_base` | 65–75 % | Базовая влажность |
| `k` | 2–3 %/°C | Коэффициент корреляции с температурой |
| `noise` | gaussian, σ ≈ 1.0 % | Шум |

Влажность обратно коррелирует с температурой — при росте T влажность падает.

### 3.3. Влажность почвы

```
S(t) = S_prev - evaporation_rate * dt + irrigation_boost
```

| Параметр | Значение | Описание |
|---|---|---|
| `S_prev` | предыдущее значение | Текущее состояние |
| `evaporation_rate` | 0.3–0.5 %/мин | Скорость испарения |
| `irrigation_boost` | +5–15 % | Прибавка при включённом поливе |

Поведение: постепенно падает из-за испарения, резко возрастает при поливе.

### 3.4. Освещённость

```
L(t) = L_max * max(0, sin(pi * (t_hour - sunrise) / daylight_hours)) + artificial
```

| Параметр | Значение | Описание |
|---|---|---|
| `L_max` | 50 000 lux | Максимум при полном солнце |
| `sunrise` | 6:00 | Время восхода |
| `daylight_hours` | 14 часов | Длительность светового дня |
| `artificial` | 5 000–10 000 lux | Вклад искусственного освещения (если ON) |

Ночью естественное освещение = 0. Искусственное добавляется по команде актуатора.

### 3.5. pH почвы

```
pH(t) = pH_base + slow_drift + noise
```

| Параметр | Значение | Описание |
|---|---|---|
| `pH_base` | 6.0–7.0 | Базовый уровень |
| `slow_drift` | ±0.01/час | Очень медленное изменение |
| `noise` | gaussian, σ ≈ 0.05 | Шум датчика |

Наиболее стабильный параметр. Меняется очень медленно.

### 3.6. CO2

```
CO2(t) = CO2_base + ventilation_effect + plant_cycle + noise
```

| Параметр | Значение | Описание |
|---|---|---|
| `CO2_base` | 400–800 ppm | Базовый уровень |
| `ventilation_effect` | -100–200 ppm | Снижение при вентиляции |
| `plant_cycle` | ±50 ppm | Суточный цикл фотосинтеза |
| `noise` | gaussian, σ ≈ 20 ppm | Шум |

---

## 4. Модели актуаторов

Актуаторы влияют на показания датчиков. При получении команды эмулятор корректирует параметры модели.

| Актуатор | Команды | Влияние на датчики |
|---|---|---|
| **Полив** (irrigation) | `on`, `off`, `set_value(intensity)` | Влажность почвы ↑ при ON |
| **Вентиляция** (ventilation) | `on`, `off`, `set_value(speed)` | Температура ↓, CO2 ↓, влажность воздуха ↓ при ON |
| **Освещение** (lighting) | `on`, `off`, `set_value(brightness)` | Освещённость ↑ при ON, температура немного ↑ |
| **Обогрев** (heating) | `on`, `off`, `set_value(target_temp)` | Температура ↑ при ON |

---

## 5. Конфигурация виртуальных устройств

Конфигурация хранится в JSONB-поле таблицы `devices` или в отдельном YAML/JSON файле.

```json
{
  "greenhouse_id": 1,
  "simulation": {
    "interval_seconds": 10,
    "sensors": {
      "temperature": {
        "base": 24,
        "amplitude": 4,
        "noise_sigma": 0.3,
        "unit": "°C"
      },
      "humidity": {
        "base": 70,
        "temp_correlation": -2.5,
        "noise_sigma": 1.0,
        "unit": "%"
      },
      "soil_moisture": {
        "base": 60,
        "evaporation_rate": 0.5,
        "unit": "%"
      },
      "light": {
        "max_lux": 50000,
        "sunrise_hour": 6,
        "sunset_hour": 20,
        "unit": "lux"
      },
      "ph": {
        "base": 6.5,
        "drift_per_hour": 0.01,
        "noise_sigma": 0.05,
        "unit": "pH"
      },
      "co2": {
        "base": 600,
        "noise_sigma": 20,
        "unit": "ppm"
      }
    },
    "actuators": ["irrigation", "ventilation", "lighting", "heating"]
  }
}
```

---

## 6. Протоколы коммуникации

### 6.1. Выбранная схема (MVP)

| Канал | Протокол | Обоснование |
|---|---|---|
| Эмулятор → БД | In-process (Python) | Эмулятор внутри FastAPI, сеть не нужна |
| Фронтенд → Бэкенд (команды) | REST API | Стандартный подход для CRUD и команд |
| Бэкенд → Фронтенд (данные) | WebSocket | Real-time поток показаний датчиков |
| Фронтенд → Бэкенд (история) | REST API | Запросы исторических данных для графиков |

### 6.2. MQTT (основная архитектура проекта)

В основной архитектуре проекта ESP32-устройства общаются с бэкендом через MQTT:

- Брокер: [Mosquitto](https://mosquitto.org/) (в Docker)
- Python-клиент: [paho-mqtt](https://pypi.org/project/paho-mqtt/)
- Топики: `greenhouse/{id}/sensors/{type}`, `greenhouse/{id}/commands/{type}`

Программный эмулятор обходит MQTT и пишет напрямую в БД — это проще для разработки, но не заменяет полную MQTT-архитектуру.

### 6.3. Сравнение протоколов

| Критерий | MQTT | HTTP REST | WebSocket |
|---|---|---|---|
| Модель | Pub/Sub | Request/Response | Bidirectional |
| Overhead | Минимальный (2 байта) | Высокий (HTTP headers) | Средний |
| Real-time | Да | Нет (polling) | Да |
| Сложность | Нужен брокер | Просто | Средне |
| Для MVP | Избыточно | Для API | Для real-time |

---

## 7. Интеграция с фронтендом

### 7.1. WebSocket-эндпоинт для real-time данных

```python
@app.websocket("/ws/greenhouse/{greenhouse_id}")
async def greenhouse_ws(websocket: WebSocket, greenhouse_id: int):
    await websocket.accept()
    while True:
        readings = await get_latest_readings(greenhouse_id)
        await websocket.send_json(readings)
        await asyncio.sleep(2)
```

### 7.2. REST API для управления эмуляцией

| Эндпоинт | Метод | Описание |
|---|---|---|
| `/api/v1/simulator/start` | POST | Запустить эмуляцию |
| `/api/v1/simulator/stop` | POST | Остановить эмуляцию |
| `/api/v1/simulator/status` | GET | Текущее состояние эмулятора |
| `/api/v1/simulator/config` | PUT | Обновить конфигурацию |

### 7.3. Что показывать на фронте

- Карточки/виджеты с текущими показаниями каждого датчика
- Графики истории за час/день (данные через REST API)
- Статус актуаторов (вкл/выкл) с кнопками управления
- Визуальная схема теплицы с цветовой индикацией зон

---

## 8. Зависимости

Минимальный набор — дополнительных зависимостей практически не требуется:

```
# Уже есть в проекте:
fastapi
sqlalchemy
pydantic
uvicorn

# Опционально:
numpy    # для math-моделей (можно обойтись math + random из stdlib)
```

---

## 9. Источники

- [leedskiy/IoT-simulator (GitHub)](https://github.com/leedskiy/IoT-simulator)
- [Digital Twin with Python (Towards Data Science)](https://towardsdatascience.com/digital-twin-with-python-a-hands-on-example-2a3036124b61/)
- [FastAPI Real-time Dashboard with WebSockets (TestDriven.io)](https://testdriven.io/blog/fastapi-postgres-websockets/)
- [FastAPI-MQTT (GitHub)](https://github.com/sabuhish/fastapi-mqtt)
- [Paho MQTT Python Client Guide (EMQ)](https://www.emqx.com/en/blog/how-to-use-mqtt-in-python)
- [MQTT vs REST for IoT (Bevywise)](https://www.bevywise.com/blog/mqtt-vs-rest-iot-implementation/)
- [Greenhouse Crop Simulation Models (IntechOpen)](https://www.intechopen.com/chapters/76412)
- [IoT Device Monitoring Dashboard (GitHub)](https://github.com/HarshithaC-hack/iot-device-monitoring-dashboard)
- [Synth — IoT Device Simulator (DevicePilot)](https://devicepilot-synth.readthedocs.io/en/latest/introduction.html)
