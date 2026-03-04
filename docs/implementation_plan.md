# Implementation Plan - IoT Smart Greenhouse System

## Project Overview
Deliver a working IoT-based smart greenhouse monitoring and control system with real-time sensor data collection, actuator control, and web-based user interface.

## Implementation Strategy

### Phase 1: Foundation & Infrastructure (Week 1)
Set up development environment, database, and basic backend structure.

### Phase 2: MQTT & Backend Core (Week 2)
Implement MQTT communication, core API endpoints, and data persistence.

### Phase 3: Frontend Development (Week 3)
Build React-based user interface with real-time data visualization.

### Phase 4: IoT Device Integration (Week 4)
Develop ESP32 firmware and integrate with backend.

### Phase 5: Testing & Deployment (Week 5)
End-to-end testing, Docker deployment, and documentation.

---

## Detailed Task Breakdown

### TASK 1: Project Setup & Environment Configuration
**Priority:** P0 (Critical)
**Status:** PENDING

**Objectives:**
- Initialize project structure
- Set up development environment
- Configure Docker infrastructure

**Acceptance Criteria:**
- [ ] Project directory structure created
- [ ] Git repository initialized with .gitignore
- [ ] Docker Compose file configured for all services
- [ ] Environment variables template created (.env.example)
- [ ] Development dependencies installed

**Implementation Steps:**

1.1. **Create Project Structure**
```bash
megalaba/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── api/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── services/
│   │   ├── mqtt/
│   │   └── core/
│   ├── tests/
│   ├── requirements.txt
│   ├── Dockerfile
│   └── alembic/
├── frontend/
│   ├── src/
│   ├── public/
│   ├── package.json
│   ├── tsconfig.json
│   └── Dockerfile
├── iot/
│   ├── wokwi/
│   └── src/
├── docker-compose.yml
├── .env.example
├── .gitignore
└── docs/
```

1.2. **Docker Compose Configuration**
- PostgreSQL service with persistent volume
- Eclipse Mosquitto MQTT broker
- Backend service (FastAPI)
- Frontend service (React + Nginx)
- Network configuration

1.3. **Environment Setup**
- Python virtual environment for backend
- Node.js environment for frontend
- VSCode Wokwi extension for IoT development

**Files to Create:**
- `docker-compose.yml`
- `.env.example`
- `.gitignore`
- `backend/requirements.txt`
- `frontend/package.json`

**Testing:**
- [ ] Run `docker-compose up` successfully
- [ ] All services start without errors
- [ ] Can connect to PostgreSQL
- [ ] Can connect to Mosquitto

**Demo:**
Show all Docker containers running and healthy status.

---

### TASK 2: Database Schema Implementation
**Priority:** P0 (Critical)
**Status:** PENDING
**Depends On:** TASK 1

**Objectives:**
- Implement PostgreSQL database schema
- Set up Alembic migrations
- Create initial seed data

**Acceptance Criteria:**
- [ ] All database tables created (users, devices, sensor_readings, actuator_commands)
- [ ] Indexes and constraints properly defined
- [ ] Alembic migrations configured
- [ ] Seed data script creates test devices
- [ ] Database initialization automated in Docker

**Implementation Steps:**

2.1. **SQLAlchemy Models** (`backend/app/models/`)
- `user.py` - User model
- `device.py` - Device model
- `sensor.py` - SensorReading model
- `actuator.py` - ActuatorCommand model
- `base.py` - Base model with common fields

2.2. **Alembic Setup**
```bash
cd backend
alembic init alembic
alembic revision --autogenerate -m "Initial schema"
```

2.3. **Seed Data** (`backend/scripts/seed_db.py`)
- Create 3 test devices (greenhouse_01, greenhouse_02, greenhouse_03)
- Create test user account
- Insert sample sensor readings

**Files to Create:**
- `backend/app/models/*.py`
- `backend/app/database.py`
- `backend/alembic/versions/*.py`
- `backend/scripts/seed_db.py`

**Testing:**
- [ ] Run migrations: `alembic upgrade head`
- [ ] Verify all tables created: `\dt` in psql
- [ ] Check constraints and indexes
- [ ] Run seed script successfully
- [ ] Query seed data successfully

**Demo:**
Show database tables, relationships, and sample data in PostgreSQL.

---

### TASK 3: Backend Core - FastAPI Setup & Configuration
**Priority:** P0 (Critical)
**Status:** PENDING
**Depends On:** TASK 2

**Objectives:**
- Set up FastAPI application
- Implement configuration management
- Create base API structure with health checks

**Acceptance Criteria:**
- [ ] FastAPI app runs successfully
- [ ] Configuration loaded from environment variables
- [ ] Health check endpoint responds
- [ ] CORS configured for frontend
- [ ] Logging configured
- [ ] OpenAPI documentation accessible

**Implementation Steps:**

3.1. **Core Configuration** (`backend/app/config.py`)
- Environment variables management (Pydantic Settings)
- Database URL
- MQTT broker settings
- JWT secret key
- CORS origins

3.2. **Main Application** (`backend/app/main.py`)
- FastAPI app initialization
- CORS middleware
- Router registration
- Startup/shutdown events
- Exception handlers

3.3. **Health Check** (`backend/app/api/health.py`)
- `/health` - Basic health check
- `/health/db` - Database connectivity
- `/health/mqtt` - MQTT broker connectivity

**Files to Create:**
- `backend/app/config.py`
- `backend/app/main.py`
- `backend/app/api/health.py`
- `backend/app/core/logging.py`

**Testing:**
- [ ] Unit test: Configuration loads correctly
- [ ] Integration test: Health endpoints return 200
- [ ] Manual test: Access http://localhost:8000/docs
- [ ] Verify OpenAPI schema generation

**Demo:**
Show FastAPI docs UI at /docs, health check endpoints responding.

---

### TASK 4: Authentication & Authorization System
**Priority:** P1 (High)
**Status:** PENDING
**Depends On:** TASK 3

**Objectives:**
- Implement JWT-based authentication
- Create user registration and login endpoints
- Add authentication middleware

**Acceptance Criteria:**
- [ ] User registration endpoint works
- [ ] Login returns JWT token
- [ ] Token validation middleware implemented
- [ ] Password hashing with bcrypt
- [ ] Token refresh endpoint implemented
- [ ] Protected routes require authentication

**Implementation Steps:**

4.1. **Auth Schemas** (`backend/app/schemas/auth.py`)
- UserCreate, UserLogin, UserResponse
- Token, TokenPayload

4.2. **Auth Service** (`backend/app/services/auth.py`)
- Password hashing (bcrypt)
- JWT token creation
- Token verification
- User authentication

4.3. **Auth API** (`backend/app/api/auth.py`)
- POST `/api/v1/auth/register`
- POST `/api/v1/auth/login`
- POST `/api/v1/auth/refresh`
- GET `/api/v1/auth/me`

4.4. **Dependencies** (`backend/app/core/security.py`)
- `get_current_user` dependency
- `get_current_active_user` dependency

**Files to Create:**
- `backend/app/schemas/auth.py`
- `backend/app/services/auth_service.py`
- `backend/app/api/v1/auth.py`
- `backend/app/core/security.py`

**Testing:**
- [ ] Unit test: Password hashing and verification
- [ ] Unit test: JWT token creation and validation
- [ ] Integration test: Register user flow
- [ ] Integration test: Login flow returns valid token
- [ ] Integration test: Protected endpoint rejects invalid token

**Demo:**
Use Postman/curl to register, login, and access protected endpoint.

---

### TASK 5: Device Management API
**Priority:** P1 (High)
**Status:** PENDING
**Depends On:** TASK 4

**Objectives:**
- Implement CRUD operations for devices
- Create device schemas and services
- Add device listing with filters

**Acceptance Criteria:**
- [ ] List all devices with pagination
- [ ] Get device by ID
- [ ] Create new device
- [ ] Update device information
- [ ] Delete (deactivate) device
- [ ] Filter devices by status (active/online)

**Implementation Steps:**

5.1. **Device Schemas** (`backend/app/schemas/device.py`)
- DeviceCreate, DeviceUpdate, DeviceResponse
- DeviceList with pagination

5.2. **Device Service** (`backend/app/services/device_service.py`)
- CRUD operations
- Filter and pagination logic
- Device status management

5.3. **Device API** (`backend/app/api/v1/devices.py`)
- GET `/api/v1/devices` - List devices
- GET `/api/v1/devices/{device_id}` - Get device
- POST `/api/v1/devices` - Create device
- PUT `/api/v1/devices/{device_id}` - Update device
- DELETE `/api/v1/devices/{device_id}` - Delete device

**Files to Create:**
- `backend/app/schemas/device.py`
- `backend/app/services/device_service.py`
- `backend/app/api/v1/devices.py`

**Testing:**
- [ ] Unit test: Device service CRUD operations
- [ ] Integration test: Create device via API
- [ ] Integration test: List devices with filters
- [ ] Integration test: Update device
- [ ] Integration test: Device not found returns 404

**Demo:**
Use Postman to perform all CRUD operations on devices.

---

### TASK 6: MQTT Client Setup & Connection
**Priority:** P0 (Critical)
**Status:** PENDING
**Depends On:** TASK 3

**Objectives:**
- Implement MQTT client with Paho-MQTT
- Establish connection to Mosquitto broker
- Handle connection lifecycle (connect, disconnect, reconnect)

**Acceptance Criteria:**
- [ ] MQTT client connects to broker on startup
- [ ] Connection status logged
- [ ] Automatic reconnection on disconnect
- [ ] Last Will Testament configured
- [ ] Connection status available via health check

**Implementation Steps:**

6.1. **MQTT Client** (`backend/app/mqtt/client.py`)
- MQTTClient class
- Connection handling
- Reconnection logic with exponential backoff
- Callback registration

6.2. **MQTT Manager** (`backend/app/mqtt/manager.py`)
- Singleton MQTT client instance
- Lifecycle management
- Connection status tracking

6.3. **Integration with FastAPI** (`backend/app/main.py`)
- Initialize MQTT client on startup
- Disconnect on shutdown

**Files to Create:**
- `backend/app/mqtt/__init__.py`
- `backend/app/mqtt/client.py`
- `backend/app/mqtt/manager.py`

**Testing:**
- [ ] Unit test: MQTT client initialization
- [ ] Integration test: Connect to broker
- [ ] Integration test: Reconnection after broker restart
- [ ] Manual test: Check health endpoint shows MQTT connected

**Demo:**
Show MQTT client connecting, logs, and health check status.

---

### TASK 7: MQTT Topic Subscription & Message Handling
**Priority:** P0 (Critical)
**Status:** PENDING
**Depends On:** TASK 6

**Objectives:**
- Subscribe to sensor data topics
- Subscribe to actuator status topics
- Implement message parsing and validation

**Acceptance Criteria:**
- [ ] Subscribe to all sensor topics on startup
- [ ] Subscribe to all status topics on startup
- [ ] Parse JSON messages correctly
- [ ] Validate message structure
- [ ] Log received messages
- [ ] Handle malformed messages gracefully

**Implementation Steps:**

7.1. **Topic Definitions** (`backend/app/mqtt/topics.py`)
- Constants for topic patterns
- Topic builder functions
- Topic parser (extract device_id, sensor_type)

7.2. **Message Handlers** (`backend/app/mqtt/handlers.py`)
- `handle_sensor_message()` - Process sensor data
- `handle_status_message()` - Process actuator status
- Message validation with Pydantic

7.3. **Subscription Setup** (`backend/app/mqtt/client.py`)
- Subscribe to `devices/+/sensors/#`
- Subscribe to `devices/+/status/#`
- Register message callbacks

**Files to Create:**
- `backend/app/mqtt/topics.py`
- `backend/app/mqtt/handlers.py`
- `backend/app/schemas/mqtt.py`

**Testing:**
- [ ] Unit test: Topic parsing
- [ ] Unit test: Message validation
- [ ] Integration test: Publish test message, verify handler called
- [ ] Integration test: Invalid message handled gracefully

**Demo:**
Publish test MQTT message with mosquitto_pub, show handler processing.

---

### TASK 8: Sensor Data Storage & Retrieval
**Priority:** P1 (High)
**Status:** PENDING
**Depends On:** TASK 7

**Objectives:**
- Store sensor readings from MQTT in database
- Create API endpoints for sensor data retrieval
- Implement time-series queries with filtering

**Acceptance Criteria:**
- [ ] Sensor data from MQTT saved to database
- [ ] API endpoint returns latest sensor readings
- [ ] API endpoint supports time range filtering
- [ ] API endpoint supports aggregation (hourly, daily)
- [ ] Statistics calculated (min, max, avg)

**Implementation Steps:**

8.1. **Sensor Service** (`backend/app/services/sensor_service.py`)
- `create_reading()` - Save sensor data
- `get_latest_readings()` - Get latest for device
- `get_readings_by_type()` - Get historical data
- `get_statistics()` - Calculate stats

8.2. **Sensor API** (`backend/app/api/v1/sensors.py`)
- GET `/api/v1/devices/{device_id}/sensors` - Latest all sensors
- GET `/api/v1/devices/{device_id}/sensors/{sensor_type}` - Historical data
- POST `/api/v1/devices/{device_id}/sensors/{sensor_type}` - Manual entry

8.3. **MQTT Handler Integration**
- Call `sensor_service.create_reading()` from MQTT handler

**Files to Create:**
- `backend/app/schemas/sensor.py`
- `backend/app/services/sensor_service.py`
- `backend/app/api/v1/sensors.py`

**Testing:**
- [ ] Unit test: Sensor service create and retrieve
- [ ] Integration test: MQTT message creates DB record
- [ ] Integration test: API returns sensor data
- [ ] Integration test: Time range filtering works
- [ ] Integration test: Aggregation calculations correct

**Demo:**
Publish sensor data via MQTT, retrieve via API with various filters.

---

### TASK 9: Actuator Command Publishing
**Priority:** P1 (High)
**Status:** PENDING
**Depends On:** TASK 7

**Objectives:**
- Implement actuator command API endpoints
- Publish commands to MQTT topics
- Track command status (pending, sent, confirmed, failed)

**Acceptance Criteria:**
- [ ] API endpoint sends actuator commands
- [ ] Command published to correct MQTT topic
- [ ] Command saved to database
- [ ] Status updates from MQTT processed
- [ ] Command history available via API

**Implementation Steps:**

9.1. **Actuator Service** (`backend/app/services/actuator_service.py`)
- `send_command()` - Create and publish command
- `update_command_status()` - Update from MQTT status
- `get_actuator_status()` - Current actuator states
- `get_command_history()` - Historical commands

9.2. **Actuator API** (`backend/app/api/v1/actuators.py`)
- GET `/api/v1/devices/{device_id}/actuators` - All actuator status
- POST `/api/v1/devices/{device_id}/actuators/{actuator_type}` - Send command
- GET `/api/v1/devices/{device_id}/actuators/{actuator_type}/history` - Command history

9.3. **MQTT Publishing**
- Publish to `devices/{device_id}/commands/{actuator_type}`
- Set QoS to 1 (at least once delivery)

9.4. **Status Handler**
- Update command status from `devices/{device_id}/status/{actuator_type}`

**Files to Create:**
- `backend/app/schemas/actuator.py`
- `backend/app/services/actuator_service.py`
- `backend/app/api/v1/actuators.py`

**Testing:**
- [ ] Unit test: Command creation and publishing
- [ ] Integration test: API sends command to MQTT
- [ ] Integration test: Status update from MQTT
- [ ] Integration test: Command history retrieval
- [ ] Integration test: Invalid command rejected

**Demo:**
Send actuator command via API, show MQTT message, simulate status response.

---

### TASK 10: Dashboard & Analytics API
**Priority:** P2 (Medium)
**Status:** PENDING
**Depends On:** TASK 8, TASK 9

**Objectives:**
- Create dashboard overview endpoint
- Implement analytics endpoints with aggregations
- Calculate trends and statistics

**Acceptance Criteria:**
- [ ] Dashboard endpoint returns all device summaries
- [ ] Analytics endpoint provides time-series data
- [ ] Statistics include min, max, avg, trend
- [ ] Support for multiple time periods (24h, 7d, 30d)

**Implementation Steps:**

10.1. **Dashboard Service** (`backend/app/services/dashboard_service.py`)
- `get_overview()` - System-wide summary
- `get_device_analytics()` - Device-specific analytics
- Trend calculation logic

10.2. **Dashboard API** (`backend/app/api/v1/dashboard.py`)
- GET `/api/v1/dashboard/overview`
- GET `/api/v1/devices/{device_id}/analytics`

**Files to Create:**
- `backend/app/services/dashboard_service.py`
- `backend/app/api/v1/dashboard.py`
- `backend/app/schemas/dashboard.py`

**Testing:**
- [ ] Integration test: Dashboard overview returns correct data
- [ ] Integration test: Analytics for various time periods
- [ ] Integration test: Trend calculations accurate

**Demo:**
Show dashboard endpoint with multiple devices, analytics with charts.

---

### TASK 11: Frontend Project Setup
**Priority:** P1 (High)
**Status:** PENDING
**Depends On:** TASK 1

**Objectives:**
- Initialize React + TypeScript project
- Set up routing and state management
- Configure API client

**Acceptance Criteria:**
- [ ] React app runs in development mode
- [ ] TypeScript configured correctly
- [ ] React Router setup
- [ ] Axios/fetch client configured
- [ ] Environment variables configured
- [ ] Basic layout and navigation

**Implementation Steps:**

11.1. **Project Initialization**
```bash
npx create-react-app frontend --template typescript
cd frontend
npm install react-router-dom axios recharts
npm install -D @types/react-router-dom
```

11.2. **Project Structure**
```
frontend/src/
├── components/
│   ├── layout/
│   ├── devices/
│   ├── sensors/
│   └── actuators/
├── pages/
├── services/
├── contexts/
├── hooks/
├── types/
└── utils/
```

11.3. **API Client** (`src/services/api.ts`)
- Axios instance with base URL
- Request/response interceptors
- Token management

11.4. **Routing** (`src/App.tsx`)
- `/` - Dashboard
- `/login` - Login page
- `/devices` - Device list
- `/devices/:id` - Device details

**Files to Create:**
- `frontend/src/services/api.ts`
- `frontend/src/types/index.ts`
- `frontend/src/contexts/AuthContext.tsx`
- `frontend/src/App.tsx`

**Testing:**
- [ ] npm start runs without errors
- [ ] TypeScript compilation successful
- [ ] Routing works between pages
- [ ] API client makes test request

**Demo:**
Show React app running, navigation working.

---

### TASK 12: Authentication UI
**Priority:** P1 (High)
**Status:** PENDING
**Depends On:** TASK 11

**Objectives:**
- Create login and registration forms
- Implement auth context and hooks
- Protect routes with authentication

**Acceptance Criteria:**
- [ ] Login form functional
- [ ] Registration form functional
- [ ] Auth token stored in localStorage
- [ ] Protected routes redirect to login
- [ ] Logout functionality works
- [ ] Auth context provides user state

**Implementation Steps:**

12.1. **Auth Context** (`src/contexts/AuthContext.tsx`)
- User state management
- Login, logout, register functions
- Token persistence

12.2. **Login Page** (`src/pages/Login.tsx`)
- Login form with validation
- Error handling
- Redirect after login

12.3. **Protected Route** (`src/components/ProtectedRoute.tsx`)
- Check authentication
- Redirect to login if not authenticated

**Files to Create:**
- `frontend/src/contexts/AuthContext.tsx`
- `frontend/src/pages/Login.tsx`
- `frontend/src/pages/Register.tsx`
- `frontend/src/components/ProtectedRoute.tsx`

**Testing:**
- [ ] Manual test: Login with valid credentials
- [ ] Manual test: Login with invalid credentials shows error
- [ ] Manual test: Protected route redirects
- [ ] Manual test: Logout clears token

**Demo:**
Complete login flow, show token storage, access protected page.

---

### TASK 13: Device List & Management UI
**Priority:** P1 (High)
**Status:** PENDING
**Depends On:** TASK 12

**Objectives:**
- Display list of all devices
- Show device status (online/offline)
- Navigate to device details
- Create new device (admin)

**Acceptance Criteria:**
- [ ] Device list page displays all devices
- [ ] Shows device name, location, status
- [ ] Click device navigates to details
- [ ] Add device button functional
- [ ] Loading and error states handled

**Implementation Steps:**

13.1. **Device Service** (`src/services/deviceService.ts`)
- `getDevices()` - Fetch device list
- `getDevice(id)` - Fetch single device
- `createDevice()` - Create new device
- `updateDevice()` - Update device

13.2. **Device List Page** (`src/pages/DeviceList.tsx`)
- Fetch and display devices
- Filter controls (active, online)
- Device cards with status indicators

13.3. **Device Form** (`src/components/devices/DeviceForm.tsx`)
- Form for creating/editing devices
- Validation

**Files to Create:**
- `frontend/src/services/deviceService.ts`
- `frontend/src/pages/DeviceList.tsx`
- `frontend/src/components/devices/DeviceCard.tsx`
- `frontend/src/components/devices/DeviceForm.tsx`

**Testing:**
- [ ] Manual test: Device list loads
- [ ] Manual test: Click device opens details
- [ ] Manual test: Create device form works

**Demo:**
Show device list, create new device, navigate to details.

---

### TASK 14: Device Dashboard UI
**Priority:** P1 (High)
**Status:** PENDING
**Depends On:** TASK 13

**Objectives:**
- Create device detail page with real-time sensor data
- Display current sensor readings
- Show sensor data charts
- Display actuator status

**Acceptance Criteria:**
- [ ] Device details page shows current sensor values
- [ ] Charts display sensor history
- [ ] Auto-refresh sensor data (polling or WebSocket)
- [ ] Actuator status cards displayed
- [ ] Loading and error states

**Implementation Steps:**

14.1. **Sensor Service** (`src/services/sensorService.ts`)
- `getLatestReadings(deviceId)` - Current readings
- `getSensorHistory(deviceId, sensorType, params)` - Historical data

14.2. **Device Detail Page** (`src/pages/DeviceDetail.tsx`)
- Fetch device info
- Display current readings
- Show actuator status
- Tabs for different views

14.3. **Sensor Display Components**
- `SensorCard.tsx` - Display single sensor reading
- `SensorChart.tsx` - Line chart for historical data (using recharts)

14.4. **Auto-refresh**
- Use `useEffect` with interval for polling
- Optional: WebSocket connection for real-time updates

**Files to Create:**
- `frontend/src/services/sensorService.ts`
- `frontend/src/pages/DeviceDetail.tsx`
- `frontend/src/components/sensors/SensorCard.tsx`
- `frontend/src/components/sensors/SensorChart.tsx`

**Testing:**
- [ ] Manual test: Sensor readings display
- [ ] Manual test: Charts render correctly
- [ ] Manual test: Auto-refresh updates data

**Demo:**
Show device dashboard with live sensor data and charts.

---

### TASK 15: Actuator Control UI
**Priority:** P1 (High)
**Status:** PENDING
**Depends On:** TASK 14

**Objectives:**
- Create actuator control panel
- Send commands to actuators
- Display command status and feedback
- Show command history

**Acceptance Criteria:**
- [ ] Actuator control buttons functional
- [ ] Command sent to backend
- [ ] Status updates reflected in UI
- [ ] Loading state during command execution
- [ ] Error handling for failed commands

**Implementation Steps:**

15.1. **Actuator Service** (`src/services/actuatorService.ts`)
- `getActuatorStatus(deviceId)` - Get all actuator states
- `sendCommand(deviceId, actuatorType, command)` - Send command
- `getCommandHistory(deviceId, actuatorType)` - Get history

15.2. **Actuator Control Components**
- `ActuatorCard.tsx` - Single actuator with on/off button
- `ActuatorPanel.tsx` - All actuators for device

15.3. **Command Feedback**
- Toast notifications for success/error
- Status indicators (pending, confirmed, failed)

**Files to Create:**
- `frontend/src/services/actuatorService.ts`
- `frontend/src/components/actuators/ActuatorCard.tsx`
- `frontend/src/components/actuators/ActuatorPanel.tsx`

**Testing:**
- [ ] Manual test: Click button sends command
- [ ] Manual test: Success notification shown
- [ ] Manual test: Error handled gracefully

**Demo:**
Send actuator command, show status update, demonstrate error case.

---

### TASK 16: Dashboard Overview Page
**Priority:** P2 (Medium)
**Status:** PENDING
**Depends On:** TASK 14, TASK 15

**Objectives:**
- Create main dashboard with overview of all devices
- Show system-wide statistics
- Quick access to all devices

**Acceptance Criteria:**
- [ ] Dashboard shows summary of all devices
- [ ] Displays total devices, online count
- [ ] Shows recent sensor readings for all devices
- [ ] Quick links to device details

**Implementation Steps:**

16.1. **Dashboard Service** (`src/services/dashboardService.ts`)
- `getOverview()` - System-wide summary

16.2. **Dashboard Page** (`src/pages/Dashboard.tsx`)
- Summary cards (total devices, online, offline)
- Device status grid
- Recent activity

**Files to Create:**
- `frontend/src/services/dashboardService.ts`
- `frontend/src/pages/Dashboard.tsx`
- `frontend/src/components/dashboard/SummaryCard.tsx`

**Testing:**
- [ ] Manual test: Dashboard loads all data
- [ ] Manual test: Click device opens details

**Demo:**
Show complete dashboard with multiple devices.

---

### TASK 17: ESP32 Firmware - Basic Setup
**Priority:** P1 (High)
**Status:** PENDING
**Depends On:** TASK 6

**Objectives:**
- Set up ESP32 project in Wokwi
- Implement WiFi connection
- Implement MQTT client connection

**Acceptance Criteria:**
- [ ] ESP32 connects to WiFi
- [ ] MQTT client connects to broker
- [ ] Device publishes "online" status on connect
- [ ] Last Will Testament configured

**Implementation Steps:**

17.1. **Wokwi Project Setup** (`iot/wokwi/diagram.json`)
- ESP32 board configuration
- WiFi credentials in code

17.2. **Main Firmware** (`iot/src/main.cpp`)
- WiFi connection with auto-reconnect
- MQTT client setup (PubSubClient library)
- Connection callbacks

17.3. **Configuration** (`iot/src/config.h`)
- WiFi SSID/password
- MQTT broker address
- Device ID

**Files to Create:**
- `iot/wokwi/diagram.json`
- `iot/wokwi/wokwi.toml`
- `iot/src/main.cpp`
- `iot/src/config.h`

**Testing:**
- [ ] Wokwi simulation runs
- [ ] WiFi connection established
- [ ] MQTT connection logged

**Demo:**
Run Wokwi simulation, show WiFi and MQTT connection in serial monitor.

---

### TASK 18: ESP32 Firmware - Sensor Integration
**Priority:** P1 (High)
**Status:** PENDING
**Depends On:** TASK 17

**Objectives:**
- Configure virtual sensors in Wokwi
- Read sensor data
- Publish sensor data to MQTT topics

**Acceptance Criteria:**
- [ ] Temperature sensor reads values
- [ ] Humidity sensor reads values
- [ ] Light sensor reads values
- [ ] Sensor data published every 5 seconds
- [ ] Data formatted as JSON

**Implementation Steps:**

18.1. **Wokwi Diagram** (`iot/wokwi/diagram.json`)
- Add DHT22 sensor (temperature/humidity)
- Add photoresistor (light sensor)
- Wire sensors to GPIO pins

18.2. **Sensor Reading** (`iot/src/sensors.cpp`)
- Read DHT22 for temp/humidity
- Read analog pin for light level
- Convert to appropriate units

18.3. **MQTT Publishing** (`iot/src/mqtt_handler.cpp`)
- Publish to `devices/{device_id}/sensors/temperature`
- Publish to `devices/{device_id}/sensors/humidity`
- Publish to `devices/{device_id}/sensors/light`
- JSON payload format

**Files to Create:**
- `iot/src/sensors.h`
- `iot/src/sensors.cpp`
- `iot/src/mqtt_handler.h`
- `iot/src/mqtt_handler.cpp`

**Testing:**
- [ ] Wokwi simulation reads sensor values
- [ ] MQTT messages published
- [ ] Backend receives and stores data

**Demo:**
Show sensor readings in serial monitor, MQTT messages, data in backend API.

---

### TASK 19: ESP32 Firmware - Actuator Control
**Priority:** P1 (High)
**Status:** PENDING
**Depends On:** TASK 18

**Objectives:**
- Configure virtual actuators in Wokwi
- Subscribe to command topics
- Execute actuator commands
- Publish status confirmations

**Acceptance Criteria:**
- [ ] Subscribe to all command topics
- [ ] Parse incoming commands
- [ ] Control LED/relay for each actuator
- [ ] Publish status after execution
- [ ] Handle invalid commands gracefully

**Implementation Steps:**

19.1. **Wokwi Diagram**
- Add 4 LEDs (representing actuators)
- Connect to GPIO pins

19.2. **Command Subscription** (`iot/src/mqtt_handler.cpp`)
- Subscribe to `devices/{device_id}/commands/#`
- Parse command topic and payload

19.3. **Actuator Control** (`iot/src/actuators.cpp`)
- Control functions for each actuator
- Set GPIO states (HIGH/LOW)

19.4. **Status Publishing**
- Publish to `devices/{device_id}/status/{actuator_type}`
- Include current state and timestamp

**Files to Create:**
- `iot/src/actuators.h`
- `iot/src/actuators.cpp`

**Testing:**
- [ ] Publish command via mosquitto_pub
- [ ] ESP32 receives and executes
- [ ] LED state changes in Wokwi
- [ ] Status published to MQTT
- [ ] Backend receives status update

**Demo:**
Send command from frontend, show LED in Wokwi, status update in backend.

---

### TASK 20: End-to-End Integration Testing
**Priority:** P0 (Critical)
**Status:** PENDING
**Depends On:** TASK 19

**Objectives:**
- Test complete flow from IoT device to frontend
- Verify all components communicate correctly
- Fix integration issues

**Acceptance Criteria:**
- [ ] Sensor data flows: ESP32 → MQTT → Backend → Database → Frontend
- [ ] Actuator commands flow: Frontend → Backend → MQTT → ESP32
- [ ] Status confirmations: ESP32 → MQTT → Backend → Frontend
- [ ] Multiple devices work simultaneously
- [ ] Reconnection scenarios handled

**Testing Scenarios:**

20.1. **Sensor Data Flow**
- Start ESP32 simulator
- Verify sensor data appears in frontend dashboard
- Check database has records

20.2. **Actuator Control Flow**
- Send command from frontend
- Verify command reaches ESP32
- Verify actuator state changes in Wokwi
- Verify status update in frontend

20.3. **Device Offline/Online**
- Stop ESP32 simulator
- Verify device shows offline in frontend
- Restart ESP32
- Verify device shows online

20.4. **Multiple Devices**
- Run 2 Wokwi simulations
- Verify both devices visible in frontend
- Verify data from both devices stored separately

**Files to Create:**
- `tests/integration/test_e2e.py`
- `tests/integration/README.md`

**Testing:**
- [ ] All E2E scenarios pass
- [ ] Performance acceptable (< 1s latency)
- [ ] No data loss during normal operation

**Demo:**
Complete flow: view sensors, send command, show all updates.

---

### TASK 21: Docker Deployment & Production Setup
**Priority:** P0 (Critical)
**Status:** PENDING
**Depends On:** TASK 20

**Objectives:**
- Create production Docker images
- Set up docker-compose for production
- Configure environment variables
- Document deployment process

**Acceptance Criteria:**
- [ ] All services run in Docker containers
- [ ] Frontend served by Nginx
- [ ] Backend runs with Gunicorn/Uvicorn
- [ ] Database has persistent volumes
- [ ] Environment variables configurable
- [ ] Health checks configured

**Implementation Steps:**

21.1. **Backend Dockerfile (Production)**
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

21.2. **Frontend Dockerfile (Production)**
```dockerfile
FROM node:18 AS build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/build /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
```

21.3. **Docker Compose Production** (`docker-compose.prod.yml`)
- Production-ready configuration
- Resource limits
- Restart policies
- Health checks

21.4. **Environment Configuration**
- `.env.production` template
- Secrets management
- Documentation

**Files to Create:**
- `backend/Dockerfile`
- `frontend/Dockerfile`
- `frontend/nginx.conf`
- `docker-compose.prod.yml`
- `.env.production.example`
- `docs/deployment.md`

**Testing:**
- [ ] `docker-compose -f docker-compose.prod.yml up` works
- [ ] All services healthy
- [ ] Frontend accessible
- [ ] API calls work
- [ ] MQTT communication functional

**Demo:**
Deploy entire stack with Docker Compose, show all services running.

---

### TASK 22: Documentation & README
**Priority:** P2 (Medium)
**Status:** PENDING
**Depends On:** TASK 21

**Objectives:**
- Create comprehensive README
- Document setup and installation
- Create user guide
- Document API usage

**Acceptance Criteria:**
- [ ] README.md has project overview
- [ ] Setup instructions clear and complete
- [ ] API documentation linked
- [ ] Architecture diagram included
- [ ] Troubleshooting section

**Files to Update:**
- `README.md`
- `docs/setup.md`
- `docs/user_guide.md`
- `docs/troubleshooting.md`

**Testing:**
- [ ] Follow README from scratch
- [ ] All commands work as documented

**Demo:**
Walk through README, show successful setup.

---

## Quality Assurance

### Testing Requirements
Every task must include:
- [ ] Unit tests (for services and utilities)
- [ ] Integration tests (for API endpoints)
- [ ] Manual testing checklist
- [ ] Demo preparation

### Code Quality
- [ ] Linting: ESLint (frontend), Flake8/Black (backend)
- [ ] Type checking: TypeScript (frontend), mypy (backend)
- [ ] Code formatting: Prettier (frontend), Black (backend)
- [ ] Test coverage: >80% for core services

### Pre-Commit Checks
```bash
# Backend
cd backend
black app/ tests/
flake8 app/ tests/
mypy app/
pytest tests/

# Frontend
cd frontend
npm run lint
npm run type-check
npm run test
```

---

## Success Criteria

### Functional Requirements
- [ ] IoT devices send sensor data to backend
- [ ] Sensor data stored in database
- [ ] Frontend displays real-time sensor data
- [ ] Users can send actuator commands
- [ ] Actuator status updates visible in UI
- [ ] Multiple devices supported
- [ ] User authentication works

### Non-Functional Requirements
- [ ] System uptime > 99% (in normal conditions)
- [ ] Sensor data latency < 2 seconds
- [ ] Actuator command response < 1 second
- [ ] Frontend loads in < 3 seconds
- [ ] Supports at least 10 concurrent devices
- [ ] Database queries optimized (< 100ms)

### Deployment Requirements
- [ ] All services containerized
- [ ] One-command deployment
- [ ] Environment variables documented
- [ ] Logs accessible
- [ ] Health checks functional

---

## Timeline Estimate

- **Week 1**: Tasks 1-6 (Foundation & MQTT setup)
- **Week 2**: Tasks 7-10 (Backend API completion)
- **Week 3**: Tasks 11-16 (Frontend development)
- **Week 4**: Tasks 17-19 (IoT firmware)
- **Week 5**: Tasks 20-22 (Integration, deployment, docs)

**Note**: This is a reference timeline. Focus on delivering working end-to-end slices rather than strict timeline adherence.
