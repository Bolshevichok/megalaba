#include <Arduino.h>
#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>

// ==================== DEVICE TYPE FLAGS ====================
// СЕНСОРЫ:
//   -DTYPE_TEMPERATURE_SENSOR — датчик температуры
//   -DTYPE_HUMIDITY_SENSOR    — датчик влажности
//   -DTYPE_LIGHT_SENSOR       — датчик освещённости
//
// АКТУАТОРЫ:
//   -DTYPE_WATERING_ACTUATOR    — система полива
//   -DTYPE_HEATING_ACTUATOR     — обогрев
//   -DTYPE_VENTILATION_ACTUATOR — проветривание
//   -DTYPE_LIGHTING_ACTUATOR    — освещение

#if defined(TYPE_TEMPERATURE_SENSOR)
#define HAS_DHT_TEMP 1
#define HAS_DHT_HUMID 0
#define HAS_LDR 0
#define HAS_WATER_PUMP 0
#define HAS_HEATER 0
#define HAS_FAN 0
#define HAS_LED 0
#define DEVICE_TYPE_NAME "temperature-sensor"

#elif defined(TYPE_HUMIDITY_SENSOR)
#define HAS_DHT_TEMP 0
#define HAS_DHT_HUMID 1
#define HAS_LDR 0
#define HAS_WATER_PUMP 0
#define HAS_HEATER 0
#define HAS_FAN 0
#define HAS_LED 0
#define DEVICE_TYPE_NAME "humidity-sensor"

#elif defined(TYPE_LIGHT_SENSOR)
#define HAS_DHT_TEMP 0
#define HAS_DHT_HUMID 0
#define HAS_LDR 1
#define HAS_WATER_PUMP 0
#define HAS_HEATER 0
#define HAS_FAN 0
#define HAS_LED 0
#define DEVICE_TYPE_NAME "light-sensor"

#elif defined(TYPE_WATERING_ACTUATOR)
#define HAS_DHT_TEMP 0
#define HAS_DHT_HUMID 0
#define HAS_LDR 0
#define HAS_WATER_PUMP 1
#define HAS_HEATER 0
#define HAS_FAN 0
#define HAS_LED 0
#define DEVICE_TYPE_NAME "watering-actuator"

#elif defined(TYPE_HEATING_ACTUATOR)
#define HAS_DHT_TEMP 0
#define HAS_DHT_HUMID 0
#define HAS_LDR 0
#define HAS_WATER_PUMP 0
#define HAS_HEATER 1
#define HAS_FAN 0
#define HAS_LED 0
#define DEVICE_TYPE_NAME "heating-actuator"

#elif defined(TYPE_VENTILATION_ACTUATOR)
#define HAS_DHT_TEMP 0
#define HAS_DHT_HUMID 0
#define HAS_LDR 0
#define HAS_WATER_PUMP 0
#define HAS_HEATER 0
#define HAS_FAN 1
#define HAS_LED 0
#define DEVICE_TYPE_NAME "ventilation-actuator"

#elif defined(TYPE_LIGHTING_ACTUATOR)
#define HAS_DHT_TEMP 0
#define HAS_DHT_HUMID 0
#define HAS_LDR 0
#define HAS_WATER_PUMP 0
#define HAS_HEATER 0
#define HAS_FAN 0
#define HAS_LED 1
#define DEVICE_TYPE_NAME "lighting-actuator"

#else
#error "Не указан тип устройства! Добавьте один из флагов -DTYPE_* в build_flags"
#endif

#if HAS_DHT_TEMP || HAS_DHT_HUMID
#include <DHT.h>
#endif

// ==================== CONFIGURATION ====================

const char *WIFI_SSID = "Wokwi-GUEST";
const char *WIFI_PASS = "";

const char *MQTT_SERVER = "host.wokwi.internal";
const int MQTT_PORT = 1883;
const char *MQTT_USER = "backend";
const char *MQTT_PASS = "mqtt_secret";

#ifndef DEVICE_ID
#define DEVICE_ID 1
#endif

const unsigned long SEND_INTERVAL = 5000;

// ==================== PINS ====================

#if HAS_DHT_TEMP || HAS_DHT_HUMID
#define DHT_PIN 15
#endif

#if HAS_LDR
#define LDR_PIN 34
#endif

#if HAS_LED
#define LED_PIN 2
#endif

#if HAS_WATER_PUMP
#define WATER_PUMP_PIN 4
#endif

#if HAS_HEATER
#define HEATER_PIN 5
#endif

#if HAS_FAN
#define FAN_PIN 18
#endif

// ==================== OBJECTS ====================

#if HAS_DHT_TEMP || HAS_DHT_HUMID
DHT dht(DHT_PIN, DHT22);
#endif

WiFiClient espClient;
PubSubClient mqtt(espClient);

char topicBuf[64];
char payloadBuf[128];
unsigned long lastSend = 0;

// Состояния актуаторов
bool wateringState = false;
bool heaterState = false;
bool fanState = false;
bool ledState = false;

// ==================== WIFI ====================

void connectWiFi()
{
    Serial.print("[WiFi] Connecting to ");
    Serial.println(WIFI_SSID);
    WiFi.begin(WIFI_SSID, WIFI_PASS, 6);
    while (WiFi.status() != WL_CONNECTED)
    {
        delay(500);
        Serial.print(".");
    }
    Serial.println();
    Serial.print("[WiFi] Connected, IP: ");
    Serial.println(WiFi.localIP());
}

// ==================== MQTT CALLBACK ====================

void onMqttMessage(char *topic, byte *payload, unsigned int length)
{
    payload[length] = '\0';
    String topicStr = String(topic);

    Serial.printf("[MQTT] Received: %s -> %s\n", topic, (char *)payload);

    JsonDocument doc;
    DeserializationError err = deserializeJson(doc, (char *)payload);
    if (err)
    {
        Serial.printf("[MQTT] JSON parse error: %s\n", err.c_str());
        return;
    }

    const char *command = doc["command"];
    if (!command)
        return;

    String actuatorType = topicStr.substring(topicStr.lastIndexOf('/') + 1);
    Serial.printf("[CMD] %s -> %s\n", actuatorType.c_str(), command);

    bool turnOn = (strcmp(command, "on") == 0);
    bool published = false;

#if HAS_WATER_PUMP
    if (actuatorType == "watering")
    {
        wateringState = turnOn;
        digitalWrite(WATER_PUMP_PIN, turnOn ? HIGH : LOW);
        Serial.printf("[WATER_PUMP] %s\n", turnOn ? "ON" : "OFF");
        snprintf(topicBuf, sizeof(topicBuf), "devices/%d/status/watering", DEVICE_ID);
        snprintf(payloadBuf, sizeof(payloadBuf), "{\"status\":\"%s\"}", command);
        mqtt.publish(topicBuf, payloadBuf);
        published = true;
    }
#endif

#if HAS_HEATER
    if (actuatorType == "heating")
    {
        heaterState = turnOn;
        digitalWrite(HEATER_PIN, turnOn ? HIGH : LOW);
        Serial.printf("[HEATER] %s\n", turnOn ? "ON" : "OFF");
        snprintf(topicBuf, sizeof(topicBuf), "devices/%d/status/heating", DEVICE_ID);
        snprintf(payloadBuf, sizeof(payloadBuf), "{\"status\":\"%s\"}", command);
        mqtt.publish(topicBuf, payloadBuf);
        published = true;
    }
#endif

#if HAS_FAN
    if (actuatorType == "ventilation")
    {
        fanState = turnOn;
        digitalWrite(FAN_PIN, turnOn ? HIGH : LOW);
        Serial.printf("[FAN] %s\n", turnOn ? "ON" : "OFF");
        snprintf(topicBuf, sizeof(topicBuf), "devices/%d/status/ventilation", DEVICE_ID);
        snprintf(payloadBuf, sizeof(payloadBuf), "{\"status\":\"%s\"}", command);
        mqtt.publish(topicBuf, payloadBuf);
        published = true;
    }
#endif

#if HAS_LED
    if (actuatorType == "lighting")
    {
        ledState = turnOn;
        digitalWrite(LED_PIN, turnOn ? HIGH : LOW);
        Serial.printf("[LED] %s\n", turnOn ? "ON" : "OFF");
        snprintf(topicBuf, sizeof(topicBuf), "devices/%d/status/lighting", DEVICE_ID);
        snprintf(payloadBuf, sizeof(payloadBuf), "{\"status\":\"%s\"}", command);
        mqtt.publish(topicBuf, payloadBuf);
        published = true;
    }
#endif

    if (published)
    {
        Serial.printf("[MQTT] Status sent: %s\n", topicBuf);
    }
}

// ==================== MQTT CONNECT ====================

void connectMQTT()
{
    while (!mqtt.connected())
    {
        Serial.printf("[MQTT] Connecting to %s:%d...\n", MQTT_SERVER, MQTT_PORT);

        snprintf(topicBuf, sizeof(topicBuf), "devices/%d/lwt", DEVICE_ID);
        String clientId = "esp32-" + String(DEVICE_TYPE_NAME) + "-" + String(DEVICE_ID);

        if (mqtt.connect(clientId.c_str(), MQTT_USER, MQTT_PASS,
                         topicBuf, 1, false, "{\"status\":\"offline\"}"))
        {
            Serial.println("[MQTT] Connected!");

            // Subscribe to actuator commands
#if HAS_WATER_PUMP || HAS_HEATER || HAS_FAN || HAS_LED
            snprintf(topicBuf, sizeof(topicBuf), "devices/%d/commands/+", DEVICE_ID);
            mqtt.subscribe(topicBuf, 1);
            Serial.printf("[MQTT] Subscribed to: %s\n", topicBuf);
#endif

            // Publish online status
            snprintf(topicBuf, sizeof(topicBuf), "devices/%d/lwt", DEVICE_ID);
            mqtt.publish(topicBuf, "{\"status\":\"online\"}", false);
        }
        else
        {
            Serial.printf("[MQTT] Failed, rc=%d. Retry in 3s...\n", mqtt.state());
            delay(3000);
        }
    }
}

// ==================== PUBLISH SENSORS ====================

void publishSensors()
{
#if HAS_DHT_TEMP
    float temperature = dht.readTemperature();
    if (!isnan(temperature))
    {
        snprintf(topicBuf, sizeof(topicBuf), "devices/%d/sensors/temperature", DEVICE_ID);
        snprintf(payloadBuf, sizeof(payloadBuf), "{\"value\":%.2f}", temperature);
        mqtt.publish(topicBuf, payloadBuf);
        Serial.printf("[SENSORS] T=%.1f°C\n", temperature);
    }
#endif

#if HAS_DHT_HUMID
    float humidity = dht.readHumidity();
    if (!isnan(humidity))
    {
        snprintf(topicBuf, sizeof(topicBuf), "devices/%d/sensors/humidity", DEVICE_ID);
        snprintf(payloadBuf, sizeof(payloadBuf), "{\"value\":%.2f}", humidity);
        mqtt.publish(topicBuf, payloadBuf);
        Serial.printf("[SENSORS] H=%.1f%%\n", humidity);
    }
#endif

#if HAS_LDR
    int ldrRaw = analogRead(LDR_PIN);
    float light = map(ldrRaw, 0, 4095, 0, 1000);

    snprintf(topicBuf, sizeof(topicBuf), "devices/%d/sensors/light", DEVICE_ID);
    snprintf(payloadBuf, sizeof(payloadBuf), "{\"value\":%.0f}", light);
    mqtt.publish(topicBuf, payloadBuf);
    Serial.printf("[SENSORS] L=%.0f lux (raw=%d)\n", light, ldrRaw);
#endif
}

// ==================== SETUP ====================

void setup()
{
    Serial.begin(115200);
    delay(100);

    Serial.println("========================================");
    Serial.printf("  Smart Greenhouse ESP32 — %s\n", DEVICE_TYPE_NAME);
    Serial.printf("  Device ID: %d\n", DEVICE_ID);
    Serial.println("========================================");

    // Инициализация пинов актуаторов
#if HAS_WATER_PUMP
    pinMode(WATER_PUMP_PIN, OUTPUT);
    digitalWrite(WATER_PUMP_PIN, LOW);
#endif

#if HAS_HEATER
    pinMode(HEATER_PIN, OUTPUT);
    digitalWrite(HEATER_PIN, LOW);
#endif

#if HAS_FAN
    pinMode(FAN_PIN, OUTPUT);
    digitalWrite(FAN_PIN, LOW);
#endif

#if HAS_LED
    pinMode(LED_PIN, OUTPUT);
    digitalWrite(LED_PIN, LOW);
#endif

    // Инициализация сенсоров
#if HAS_DHT_TEMP || HAS_DHT_HUMID
    dht.begin();
#endif

    connectWiFi();

    mqtt.setServer(MQTT_SERVER, MQTT_PORT);
    mqtt.setCallback(onMqttMessage);
    mqtt.setBufferSize(512);
}

// ==================== LOOP ====================

void loop()
{
    if (WiFi.status() != WL_CONNECTED)
        connectWiFi();

    if (!mqtt.connected())
        connectMQTT();

    mqtt.loop();

    if (millis() - lastSend >= SEND_INTERVAL)
    {
        publishSensors();
        lastSend = millis();
    }
}
