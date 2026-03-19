# Smart Greenhouse IoT

IoT-система мониторинга и управления теплицей. Датчики (температура, влажность, свет) и актуаторы (полив, отопление, вентиляция, освещение) на ESP32, связь через MQTT, веб-интерфейс с real-time обновлениями.

## Архитектура

```
Frontend (Next.js)  →  Backend (FastAPI)  →  PostgreSQL
                           ↕ MQTT
                       Mosquitto
                           ↕ MQTT
                     ESP32 (Wokwi)
```

## Запуск

### 1. Бэкенд + БД + MQTT

```bash
docker compose up --build -d
```

Проверка:
```bash
curl http://localhost:8000/api/v1/health
```

### 2. Фронтенд

```bash
cd frontend
npm install
npm run dev
```

Открыть http://localhost:3000

### 3. Wokwi-устройства

Требуется: [PlatformIO](https://platformio.org/install/cli) + [Wokwi VS Code Extension](https://docs.wokwi.com/vscode/getting-started)

```bash
cd wokwi
pio run    # собрать все прошивки
```

Запуск: открыть `wokwi/device-types/<тип>/diagram.json` → F1 → "Wokwi: Start Simulator"

`DEVICE_ID` в `platformio.ini` должен совпадать с ID устройства в бэкенде.

### Типы устройств

| Тип | Компонент | Env |
|-----|-----------|-----|
| temperature-sensor | DHT22 | `pio run -e temperature-sensor` |
| humidity-sensor | DHT22 | `pio run -e humidity-sensor` |
| light-sensor | Фоторезистор | `pio run -e light-sensor` |
| lighting-actuator | LED | `pio run -e lighting-actuator` |
| watering-actuator | Насос | `pio run -e watering-actuator` |
| heating-actuator | Нагреватель | `pio run -e heating-actuator` |
| ventilation-actuator | Вентилятор | `pio run -e ventilation-actuator` |

## Порты

| Сервис | Порт |
|--------|------|
| Frontend | 3000 |
| Backend API | 8000 |
| Swagger UI | 8000/docs |
| PostgreSQL | 5433 |
| MQTT | 1883 |

## Тесты

```bash
cd backend && pytest tests/ -v
```

## Остановка

```bash
docker compose down       # остановить
docker compose down -v    # остановить + удалить данные
```
