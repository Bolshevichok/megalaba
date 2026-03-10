# Quickstart: Backend API — Умная Теплица

## Prerequisites

- Docker & Docker Compose
- Python 3.11+ (для локальной разработки)

## Быстрый запуск (Docker)

```bash
# Из корня проекта
cp .env.example .env  # настроить при необходимости
docker compose up --build
```

Сервисы:
- **Backend**: http://localhost:8000
- **Swagger UI**: http://localhost:8000/docs
- **PostgreSQL**: localhost:5432
- **Mosquitto**: localhost:1883

## Локальная разработка (без Docker)

```bash
cd backend
python -m venv venv
source venv/bin/activate  # macOS/Linux
pip install -r requirements.txt

# Запуск (нужен PostgreSQL и Mosquitto на localhost)
cp .env.example .env
uvicorn app.main:app --reload --port 8000
```

## Проверка

```bash
# Health check
curl http://localhost:8000/api/v1/health

# Регистрация
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"name":"Ivan","email":"ivan@example.com","password":"SecurePass123!"}'

# Логин
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"ivan@example.com","password":"SecurePass123!"}'

# Создать теплицу (подставить токен)
curl -X POST http://localhost:8000/api/v1/greenhouses \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"name":"Main Greenhouse","location":"Building A"}'

# Запустить эмулятор
curl -X POST http://localhost:8000/api/v1/simulator/start

# Проверить показания (после запуска эмулятора)
curl http://localhost:8000/api/v1/sensors/1/readings \
  -H "Authorization: Bearer <token>"

# MQTT тест (mosquitto_pub)
mosquitto_pub -h localhost -t "devices/1/sensors/temperature" \
  -m '{"value": 24.5, "unit": "°C", "timestamp": "2026-03-10T12:00:00Z"}'
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| DATABASE_URL | `postgresql://postgres:postgres@localhost:5432/greenhouse` | PostgreSQL connection string |
| SECRET_KEY | `changeme` | JWT signing key |
| CORS_ORIGINS | `http://localhost:3000` | Allowed CORS origins |
| ACCESS_TOKEN_EXPIRE_MINUTES | `60` | Access token TTL |
| REFRESH_TOKEN_EXPIRE_DAYS | `7` | Refresh token TTL |
| MQTT_BROKER_HOST | `localhost` | Mosquitto host |
| MQTT_BROKER_PORT | `1883` | Mosquitto port |
| MQTT_USERNAME | `backend` | MQTT username (required per Constitution V) |
| MQTT_PASSWORD | `mqtt_secret` | MQTT password (required per Constitution V) |

## Тесты

```bash
cd backend
pytest -v
```
