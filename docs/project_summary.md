# IoT Smart Greenhouse Monitoring System - Project Summary

## Overview
This project implements a complete IoT-based smart greenhouse monitoring and control system. The system enables real-time monitoring of environmental conditions (light, temperature, humidity) and remote control of actuators (irrigation, heating, ventilation, lighting) through a web interface.

## Key Components

### 1. IoT Hardware Layer
- **Microcontroller**: ESP32 with built-in WiFi module
- **Development Environment**: Wokwi simulator in VSCode
- **Sensors**:
  - Light sensor
  - Temperature sensor
  - Humidity sensor
- **Actuators**:
  - Irrigation system (watering)
  - Heating system
  - Ventilation system
  - Lighting system

### 2. Communication Layer
- **Protocol**: MQTT (Message Queuing Telemetry Transport)
- **Message Broker**: Eclipse Mosquitto
- **Architecture Pattern**: Publish-Subscribe

### 3. Backend Layer
- **Framework**: FastAPI (Python)
- **MQTT Client**: Paho-MQTT
- **Database**: PostgreSQL
- **API**: RESTful API for frontend communication

### 4. Frontend Layer
- **Framework**: React
- **Language**: TypeScript
- **Communication**: REST API with backend

### 5. Deployment
- **Containerization**: Docker for backend and frontend
- **IoT Devices**: External connectivity (not containerized)

## MQTT Topic Structure

### Sensor Data Topics (ESP32 → Backend)
ESP32 publishes sensor readings, Backend subscribes:
- `devices/{device_id}/sensors/light`
- `devices/{device_id}/sensors/temperature`
- `devices/{device_id}/sensors/humidity`

### Command Topics (Backend → ESP32)
Backend publishes commands, ESP32 subscribes:
- `devices/{device_id}/commands/lighting`
- `devices/{device_id}/commands/heating`
- `devices/{device_id}/commands/ventilation`
- `devices/{device_id}/commands/watering`

### Status Topics (ESP32 → Backend)
ESP32 publishes status confirmations:
- `devices/{device_id}/status/lighting`
- `devices/{device_id}/status/heating`
- `devices/{device_id}/status/ventilation`
- `devices/{device_id}/status/watering`

## System Flow

```
User → Frontend (React/TypeScript)
         ↓ REST API
       Backend (FastAPI/Python) ↔ PostgreSQL Database
         ↓ MQTT
       MQTT Broker (Mosquitto)
         ↓ MQTT
       IoT Devices (ESP32)
```

## Design Principles

1. **Simplicity**: "Don't eat hedgehogs" - avoid overcomplication
2. **Separation of Concerns**: Clear boundaries between layers
3. **Scalability**: Support for multiple IoT devices
4. **Real-time Communication**: Bidirectional MQTT messaging
5. **Pragmatic Deployment**: External IoT connectivity to avoid containerization complexity

## Current Status

Based on the backlog:
- ✅ **Architecture Definition** - COMPLETED (assigned to: semen)
- 🔲 **Backend Endpoints Definition** - NOT STARTED (assigned to: constanteen)
- 🔲 **Database Design** - NOT STARTED (assigned to: тим)

## Team Members
- **semen** - Architecture
- **constanteen** - Backend development
- **тим** - Database design
