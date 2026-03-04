# IoT Smart Greenhouse Monitoring System

A complete IoT-based smart greenhouse monitoring and control system with real-time sensor data collection, actuator control, and web-based user interface.

## 🌱 Overview

This project implements an end-to-end IoT solution for monitoring and controlling greenhouse environments. The system enables:

- **Real-time Monitoring**: Track temperature, humidity, and light levels
- **Remote Control**: Control heating, lighting, ventilation, and irrigation systems
- **Web Interface**: User-friendly dashboard for visualization and control
- **Multi-Device Support**: Manage multiple greenhouse units simultaneously
- **Historical Data**: View trends and analytics over time

## 🏗️ Architecture

```
User → Frontend (React/TS) → Backend (FastAPI/Python) → Database (PostgreSQL)
                                    ↕ MQTT
                            MQTT Broker (Mosquitto)
                                    ↕ MQTT
                            IoT Devices (ESP32)
```

### Key Components

- **Frontend**: React + TypeScript with real-time data visualization
- **Backend**: FastAPI (Python) with REST API and MQTT client
- **MQTT Broker**: Eclipse Mosquitto for IoT communication
- **Database**: PostgreSQL for data persistence
- **IoT Devices**: ESP32 microcontrollers (Wokwi simulator)

## 📚 Documentation

Comprehensive documentation is available in the [`docs/`](./docs/) directory:

- **[Project Summary](./docs/project_summary.md)** - High-level overview and current status
- **[Architecture](./docs/architecture.md)** - Detailed system architecture and design
- **[Database Design](./docs/database_design.md)** - Database schema and data models
- **[API Specification](./docs/api_specification.md)** - REST API endpoints and usage
- **[Implementation Plan](./docs/implementation_plan.md)** - Detailed task breakdown and timeline

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose
- Python 3.11+ (for local development)
- Node.js 18+ (for frontend development)
- VSCode with Wokwi extension (for IoT development)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd megalaba
   ```

2. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Start all services with Docker Compose**
   ```bash
   docker-compose up -d
   ```

4. **Access the application**
   - Frontend: http://localhost:80
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs
   - MQTT Broker: localhost:1883

### Development Setup

#### Backend Development
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

#### Frontend Development
```bash
cd frontend
npm install
npm start
```

#### IoT Development
1. Open VSCode
2. Install Wokwi extension
3. Open `iot/wokwi/diagram.json`
4. Press F1 → "Wokwi: Start Simulator"

## 📡 MQTT Topic Structure

### Sensor Data Topics (ESP32 → Backend)
- `devices/{device_id}/sensors/light` - Light sensor readings (lux)
- `devices/{device_id}/sensors/temperature` - Temperature readings (°C)
- `devices/{device_id}/sensors/humidity` - Humidity readings (%)

### Command Topics (Backend → ESP32)
- `devices/{device_id}/commands/lighting` - Lighting control
- `devices/{device_id}/commands/heating` - Heating control
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
