# IoT Умная Теплица — Обзор проекта

## Описание

Система мониторинга и управления умной теплицей на базе IoT. Обеспечивает мониторинг параметров окружающей среды в реальном времени (температура, влажность воздуха, влажность почвы, освещённость, pH, CO2) и дистанционное управление актуаторами (полив, обогрев, вентиляция, освещение) через веб-интерфейс.

## Ключевые компоненты

### 1. IoT-уровень (ESP32 + Wokwi)

- **Микроконтроллер**: ESP32 со встроенным WiFi
- **Среда разработки**: Wokwi-симулятор в VSCode
- **Датчики**: температура, влажность воздуха, влажность почвы, освещённость, pH почвы, CO2
- **Актуаторы**: полив, обогрев, вентиляция, освещение
- **Протокол**: MQTT (Publish-Subscribe)

### 2. Коммуникации

- **ESP32 ↔ Бэкенд**: MQTT через брокер Eclipse Mosquitto
- **Бэкенд → Фронтенд**: REST API + WebSocket (real-time)
- **Паттерн**: Publish-Subscribe (MQTT) + Request-Response (REST)

### 3. Бэкенд

- **Фреймворк**: FastAPI (Python 3.11+)
- **MQTT-клиент**: Paho-MQTT
- **ORM**: SQLAlchemy 2.0
- **Валидация**: Pydantic v2
- **БД**: PostgreSQL
- **API**: RESTful + WebSocket

### 4. Фронтенд

- **Фреймворк**: React
- **Язык**: TypeScript
- **Коммуникация**: REST API + WebSocket

### 5. Деплой

- **Контейнеризация**: Docker (бэкенд, фронтенд, PostgreSQL, Mosquitto)
- **IoT-устройства**: внешнее подключение (Wokwi / реальные ESP32)

### 6. Программный эмулятор (дополнительно)

- Встроенный в бэкенд background task для разработки и тестирования без Wokwi
- Генерирует реалистичные данные по математическим моделям
- Подробнее: [iot_device_emulation.md](iot_device_emulation.md)

## Иерархия сущностей

```
Пользователь (users)
  └── Теплица (greenhouses)
        ├── Устройство (devices)
        │     ├── Датчик (sensors) → Показания (sensor_readings)
        │     └── Актуатор (actuators) → Команды (actuator_commands)
        └── Скрипт автоматизации (scripts)
```

## MQTT-топики

### 1. Данные с датчиков (публикует ESP32, подписывается Backend)
- `devices/{device_id}/sensors/light` — данные об освещённости
- `devices/{device_id}/sensors/temperature` — данные о температуре
- `devices/{device_id}/sensors/humidity` — данные о влажности почвы/воздуха

### 2. Команды управления (публикует Backend, подписывается ESP32)
- `devices/{device_id}/commands/lighting` — управление освещением
- `devices/{device_id}/commands/heating` — управление подогревом
- `devices/{device_id}/commands/ventilation` — управление проветриванием
- `devices/{device_id}/commands/watering` — управление поливом

### 3. Статусы актуаторов (публикует ESP32, подписывается Backend)
- `devices/{device_id}/status/lighting` — текущее состояние освещения
- `devices/{device_id}/status/heating` — текущее состояние подогрева
- `devices/{device_id}/status/ventilation` — текущее состояние проветривания
- `devices/{device_id}/status/watering` — текущее состояние полива

## Поток данных

```
Пользователь → Фронтенд (React/TypeScript)
                    ↓ REST API + WebSocket
                  Бэкенд (FastAPI/Python) ↔ PostgreSQL
                    ↓ MQTT
                  MQTT-брокер (Mosquitto)
                    ↓ MQTT
                  IoT-устройства (ESP32 / Wokwi)
```

## Принципы разработки

1. **Простота**: минимальная необходимая сложность для текущей задачи
2. **Разделение ответственности**: чёткие границы между слоями
3. **Масштабируемость**: поддержка нескольких теплиц и устройств
4. **Real-time**: MQTT для IoT + WebSocket для фронтенда
5. **Гибкость**: работа как с реальными ESP32, так и с программным эмулятором

## Команда

- **semen** — архитектура
- **constanteen** — бэкенд
- **тим** — база данных
