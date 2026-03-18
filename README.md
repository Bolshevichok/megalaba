# IoT Система Мониторинга Умной Теплицы

Полнофункциональная IoT-система мониторинга и управления умной теплицей с сбором данных датчиков в реальном времени, управлением исполнительными устройствами и веб-интерфейсом.

## 🌱 Обзор

Этот проект реализует комплексное IoT-решение для мониторинга и управления окружающей средой теплицы. Система обеспечивает:

- **Мониторинг в реальном времени**: Отслеживание температуры, влажности и уровня освещенности
- **Удаленное управление**: Контроль систем отопления, освещения, вентиляции и полива
- **Веб-интерфейс**: Удобная панель управления для визуализации и контроля
- **Поддержка множества устройств**: Управление несколькими тепличными комплексами одновременно
- **Исторические данные**: Просмотр трендов и аналитики за период времени

## 🏗️ Архитектура

```
Пользователь → Фронтенд (React/TS) → Бэкенд (FastAPI/Python) → База данных (PostgreSQL)
                                    ↕ MQTT
                            MQTT Брокер (Mosquitto)
                                    ↕ MQTT
                            IoT Устройства (ESP32)
```

### Ключевые Компоненты

- **Фронтенд**: React + TypeScript с визуализацией данных в реальном времени
- **Бэкенд**: FastAPI (Python) с REST API и MQTT клиентом
- **MQTT Брокер**: Eclipse Mosquitto для IoT коммуникаций
- **База данных**: PostgreSQL для хранения данных
- **IoT Устройства**: Микроконтроллеры ESP32 (симулятор Wokwi)

## 📚 Документация

Подробная документация доступна в директории [`docs/`](./docs/):

- **[Сводка проекта](./docs/project_summary.md)** - Общий обзор и текущий статус
- **[Архитектура](./docs/architecture.md)** - Детальная архитектура системы и дизайн
- **[Дизайн базы данных](./docs/database_design.md)** - Схема базы данных и модели данных
- **[Спецификация API](./docs/api_specification.md)** - Конечные точки REST API и их использование
- **[План реализации](./docs/implementation_plan.md)** - Детальная разбивка задач и сроки

## 🚀 Быстрый Старт

### Предварительные Требования

- Docker & Docker Compose
- Python 3.11+ (для локальной разработки)
- Node.js 18+ (для разработки фронтенда)
- VSCode с расширением Wokwi (для IoT разработки)

### Настройка Windows

**Важно**: На Windows могут возникнуть проблемы с монтированием файлов аутентификации Mosquitto. Проект включает упрощенную конфигурацию для разработки на Windows.

1. **Клонировать репозиторий**
   ```powershell
   git clone <repository-url>
   cd megalaba
   ```

2. **Создать файл окружения**
   ```powershell
   # Создать .env файл с минимальной конфигурацией
   @"
   SECRET_KEY=changeme
   CORS_ORIGINS=http://localhost:3000
   "@ | Out-File -FilePath .env -Encoding UTF8
   ```

3. **Запустить сервисы с Docker Compose**
   ```powershell
   docker compose up --build -d
   ```

4. **Проверить работу сервисов**
   ```powershell
   docker ps
   ```

5. **Доступ к приложению**
   - Backend API: http://localhost:8000
   - Документация API: http://localhost:8000/docs
   - PostgreSQL: localhost:5433
   - MQTT Брокер: localhost:1883

**Устранение проблем Windows:**
- Если Mosquitto не запускается, проверьте что в `mosquitto/mosquitto.conf` установлено `allow_anonymous true`
- Используйте PowerShell вместо Command Prompt для лучшей поддержки Docker
- Убедитесь что Docker Desktop запущен и имеет достаточное количество выделенных ресурсов

### Установка

1. **Клонировать репозиторий**
   ```bash
   git clone <repository-url>
   cd megalaba
   ```

2. **Настроить переменные окружения**
   ```bash
   cp .env.example .env
   # Отредактируйте .env с вашей конфигурацией
   ```

3. **Запустить все сервисы с Docker Compose**
   ```bash
   docker-compose up -d
   ```

4. **Доступ к приложению**
   - Фронтенд: http://localhost:80
   - Backend API: http://localhost:8000
   - Документация API: http://localhost:8000/docs
   - MQTT Брокер: localhost:1883

### Настройка Разработки

#### Разработка Бэкенда
```bash
cd backend
python -m venv venv
source venv/bin/activate  # На Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

#### Разработка Фронтенда
```bash
cd frontend
npm install
npm start
```

#### IoT Разработка
1. Открыть VSCode
2. Установить расширение Wokwi
3. Открыть `iot/wokwi/diagram.json`
4. Нажать F1 → "Wokwi: Start Simulator"

## 📡 Структура MQTT Топиков

### Топики Данных Датчиков (ESP32 → Бэкенд)
- `devices/{device_id}/sensors/light` - Показания датчика освещенности (люксы)
- `devices/{device_id}/sensors/temperature` - Показания температуры (°C)
- `devices/{device_id}/sensors/humidity` - Показания влажности (%)

### Топики Команд (Бэкенд → ESP32)
- `devices/{device_id}/commands/lighting` - Управление освещением
- `devices/{device_id}/commands/heating` - Управление отоплением
- `devices/{device_id}/commands/ventilation` - Ventilation control
- `devices/{device_id}/commands/watering` - Irrigation control

### Status Topics (ESP32 → Backend)
- `devices/{device_id}/status/lighting` - Lighting status confirmation
- `devices/{device_id}/status/heating` - Heating status confirmation
- `devices/{device_id}/status/ventilation` - Ventilation status confirmation
- `devices/{device_id}/status/watering` - Watering status confirmation

## 🧪 Testing

### Backend Tests
```bash
cd backend
pytest tests/ -v
pytest --cov=app tests/  # With coverage
```

### Frontend Tests
```bash
cd frontend
npm test
npm run test:coverage
```

### Integration Tests
```bash
# Start all services first
docker-compose up -d

# Run integration tests
cd backend
pytest tests/integration/ -v
```

## 🔧 Configuration

### Environment Variables

Key environment variables (see `.env.example` for complete list):

```bash
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/greenhouse

# MQTT Broker
MQTT_BROKER_HOST=localhost
MQTT_BROKER_PORT=1883
MQTT_USERNAME=admin
MQTT_PASSWORD=password

# Backend
SECRET_KEY=your-secret-key-here
DEBUG=false

# Frontend
REACT_APP_API_URL=http://localhost:8000/api/v1
```

## 📊 API Usage

### Authentication
```bash
# Register user
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username": "user", "email": "user@example.com", "password": "password"}'

# Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "user", "password": "password"}'
```

### Device Management
```bash
# List all devices
curl http://localhost:8000/api/v1/devices \
  -H "Authorization: Bearer <token>"

# Get sensor data
curl http://localhost:8000/api/v1/devices/greenhouse_01/sensors \
  -H "Authorization: Bearer <token>"

# Control actuator
curl -X POST http://localhost:8000/api/v1/devices/greenhouse_01/actuators/heating \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"command": "on"}'
```

See [API Specification](./docs/api_specification.md) for complete API documentation.

## 🏭 Production Deployment

### Using Docker Compose (Production)
```bash
# Build production images
docker-compose -f docker-compose.prod.yml build

# Start services
docker-compose -f docker-compose.prod.yml up -d

# View logs
docker-compose -f docker-compose.prod.yml logs -f

# Stop services
docker-compose -f docker-compose.prod.yml down
```

### Database Migrations
```bash
# Run migrations
docker-compose exec backend alembic upgrade head

# Create new migration
docker-compose exec backend alembic revision --autogenerate -m "description"
```

## 🛠️ Technology Stack

### Backend
- **FastAPI** - Modern Python web framework
- **Paho-MQTT** - MQTT client library
- **SQLAlchemy** - ORM for database operations
- **Pydantic** - Data validation
- **Alembic** - Database migrations
- **PostgreSQL** - Relational database

### Frontend
- **React 18** - UI library
- **TypeScript** - Type-safe JavaScript
- **React Router** - Navigation
- **Axios** - HTTP client
- **Recharts** - Data visualization
- **Tailwind CSS** - Utility-first CSS (optional)

### IoT
- **ESP32** - Microcontroller
- **Arduino Framework** - Development framework
- **Wokwi** - IoT simulator
- **PubSubClient** - MQTT library for Arduino

### Infrastructure
- **Docker** - Containerization
- **Docker Compose** - Multi-container orchestration
- **Nginx** - Frontend web server
- **Eclipse Mosquitto** - MQTT broker

## 🤝 Contributing

This is a university project. Contributions are welcome!

### Development Workflow
1. Create a feature branch
2. Make your changes
3. Run tests and linting
4. Submit a pull request

### Code Style
- **Backend**: Black formatting, Flake8 linting
- **Frontend**: ESLint + Prettier
- **Commits**: Conventional Commits format

## 📝 Project Status

Current implementation status (see [Implementation Plan](./docs/implementation_plan.md) for details):

- ✅ Architecture Definition - COMPLETED
- 🔲 Backend Endpoints - NOT STARTED
- 🔲 Database Design - NOT STARTED
- 🔲 Frontend Development - NOT STARTED
- 🔲 IoT Firmware - NOT STARTED

## 👥 Team

- **semen** - Architecture & System Design
- **constanteen** - Backend Development
- **тим** - Database Design

## 📄 License

This project is licensed for educational purposes as part of university coursework.

## 🙏 Acknowledgments

- Eclipse Mosquitto - MQTT broker
- Wokwi - IoT simulator platform
- FastAPI - Python web framework
- React - Frontend library

---

For detailed implementation steps and task breakdown, see [Implementation Plan](./docs/implementation_plan.md).

For architecture details, see [Architecture Documentation](./docs/architecture.md).

For API reference, see [API Specification](./docs/api_specification.md).
