# System Architecture

## Architecture Overview

The Smart Greenhouse System follows a layered architecture with clear separation between IoT devices, backend services, and frontend applications.

```
┌─────────────────────────────────────────────────────────────┐
│                         User Layer                           │
│                     (Web Browser)                            │
└──────────────────────────┬──────────────────────────────────┘
                           │ HTTPS/REST
┌──────────────────────────▼──────────────────────────────────┐
│                    Frontend Layer                            │
│                  React + TypeScript                          │
│                    (Docker Container)                        │
└──────────────────────────┬──────────────────────────────────┘
                           │ REST API
┌──────────────────────────▼──────────────────────────────────┐
│                    Backend Layer                             │
│                  FastAPI + Python                            │
│                    (Docker Container)                        │
│  ┌──────────────────────────────────────────────────┐       │
│  │  REST API Server  │  MQTT Client (Paho-MQTT)     │       │
│  └──────────────────────────────────────────────────┘       │
└──────┬────────────────────────────────────┬─────────────────┘
       │                                    │ MQTT
       │ SQL                                │
┌──────▼────────┐              ┌───────────▼─────────────────┐
│  PostgreSQL   │              │    MQTT Broker              │
│   Database    │              │  (Eclipse Mosquitto)        │
│   (Docker)    │              │    (Docker Container)       │
└───────────────┘              └───────────┬─────────────────┘
                                           │ MQTT
                           ┌───────────────┼───────────────┐
                           │               │               │
                    ┌──────▼──────┐ ┌─────▼──────┐ ┌─────▼──────┐
                    │  ESP32      │ │  ESP32     │ │  ESP32     │
                    │  Device 1   │ │  Device 2  │ │  Device N  │
                    │  (Wokwi)    │ │  (Wokwi)   │ │  (Wokwi)   │
                    └─────────────┘ └────────────┘ └────────────┘
```

## Component Responsibilities

### 1. Frontend (React + TypeScript)
**Responsibilities:**
- User interface for monitoring sensor data
- Control panel for actuators
- Device management
- Real-time data visualization
- User authentication UI

**Technology Stack:**
- React 18+
- TypeScript
- REST API client (axios/fetch)
- State management (React Context/Redux)
- Charts library (recharts/chart.js)

**Deployment:**
- Dockerized container
- Nginx for serving static files
- Environment-based configuration

### 2. Backend (FastAPI + Python)
**Responsibilities:**
- RESTful API endpoints
- MQTT message handling (pub/sub)
- Business logic
- Data persistence
- Authentication & authorization
- WebSocket support (optional for real-time updates)

**Technology Stack:**
- FastAPI (Python 3.11+)
- Paho-MQTT client
- SQLAlchemy ORM
- Pydantic for data validation
- Alembic for migrations
- PostgreSQL driver (psycopg2)

**Key Modules:**
- `api/` - REST endpoints
- `mqtt/` - MQTT client and message handlers
- `models/` - Database models
- `schemas/` - Pydantic schemas
- `services/` - Business logic
- `core/` - Configuration and utilities

### 3. MQTT Broker (Eclipse Mosquitto)
**Responsibilities:**
- Message routing between backend and IoT devices
- Topic-based message distribution
- QoS management
- Retained messages for device status

**Configuration:**
- Port: 1883 (MQTT), 9001 (WebSocket - optional)
- Authentication: Username/password
- ACL for topic access control

### 4. Database (PostgreSQL)
**Responsibilities:**
- Persistent storage for:
  - Device information
  - Sensor readings history
  - Actuator commands history
  - User accounts
  - Configuration settings

**Schema Design:**
- Normalized relational model
- Time-series optimization for sensor data
- Indexes for performance

### 5. IoT Devices (ESP32)
**Responsibilities:**
- Sensor data collection
- Actuator control
- MQTT communication
- Local processing

**Development:**
- Wokwi simulator for development/testing
- C/C++ (Arduino framework)
- WiFi connectivity
- MQTT client library

## Communication Patterns

### 1. Frontend ↔ Backend (REST API)
- **Protocol**: HTTPS
- **Format**: JSON
- **Authentication**: JWT tokens
- **Endpoints**: See API specification

### 2. Backend ↔ MQTT Broker
- **Protocol**: MQTT v3.1.1/v5.0
- **QoS Levels**:
  - Sensor data: QoS 0 (at most once) - acceptable for frequent readings
  - Commands: QoS 1 (at least once) - ensure delivery
  - Status: QoS 1 (at least once)

### 3. MQTT Broker ↔ IoT Devices
- **Protocol**: MQTT over WiFi
- **Reconnection**: Automatic with exponential backoff
- **Last Will**: Device disconnection notifications

## Data Flow Examples

### Sensor Reading Flow
1. ESP32 reads sensor (e.g., temperature = 25.5°C)
2. ESP32 publishes to `devices/greenhouse_01/sensors/temperature`
3. Backend subscribes and receives message
4. Backend stores reading in PostgreSQL
5. Frontend polls/receives real-time update via REST/WebSocket

### Actuator Command Flow
1. User clicks "Turn on heating" in frontend
2. Frontend sends POST to `/api/devices/{id}/actuators/heating`
3. Backend validates command
4. Backend publishes to `devices/greenhouse_01/commands/heating` with payload `{"state": "on"}`
5. ESP32 receives command and activates heating
6. ESP32 publishes status to `devices/greenhouse_01/status/heating` with payload `{"state": "on", "timestamp": "..."}`
7. Backend receives status confirmation
8. Backend updates database and notifies frontend

## Deployment Architecture

### Docker Compose Services
```yaml
services:
  postgres:
    - Persistent storage for application data

  mosquitto:
    - MQTT broker
    - Depends on: none

  backend:
    - FastAPI application
    - Depends on: postgres, mosquitto

  frontend:
    - React application (Nginx)
    - Depends on: backend
```

### Network Configuration
- Frontend: Port 80/443 (exposed)
- Backend: Port 8000 (internal + exposed for dev)
- Mosquitto: Port 1883 (exposed for IoT)
- PostgreSQL: Port 5432 (internal only)

## Scalability Considerations

### Horizontal Scaling
- **Backend**: Stateless design allows multiple instances
- **MQTT Broker**: Clustering for high availability
- **Database**: Read replicas for queries

### Vertical Scaling
- Optimize sensor data storage (time-series DB alternative)
- Caching layer (Redis) for frequent queries
- Message queue for async processing

## Security

### Authentication & Authorization
- JWT tokens for API access
- MQTT username/password authentication
- Device-specific credentials

### Network Security
- TLS/SSL for MQTT (production)
- HTTPS for frontend-backend
- Firewall rules for Docker network

### Data Security
- Input validation (Pydantic)
- SQL injection prevention (ORM)
- MQTT topic ACLs

## Monitoring & Logging

### Logging
- Structured logging (JSON format)
- Log levels: DEBUG, INFO, WARNING, ERROR
- Centralized log aggregation

### Metrics
- Device connectivity status
- Message throughput
- API response times
- Database performance

### Alerting
- Device offline notifications
- Sensor threshold violations
- System health checks
