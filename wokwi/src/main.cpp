#include <Arduino.h>
#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>

// ==================== DEVICE TYPE (one function per device) ====================
// Set via build_flags in platformio.ini

#if defined(TYPE_TEMPERATURE_SENSOR)
#define SENSOR_TYPE "temperature"
#define SENSOR_UNIT "°C"
#define USE_DHT 1
#define USE_DHT_TEMPERATURE 1
#define USE_LDR 0
#define USE_LED 0
#define USE_WATER_PUMP 0
#define USE_HEATER 0
#define USE_FAN 0
#define DEVICE_TYPE_NAME "temperature-sensor"

#elif defined(TYPE_HUMIDITY_SENSOR)
#define SENSOR_TYPE "humidity"
#define SENSOR_UNIT "%"
#define USE_DHT 1
#define USE_DHT_TEMPERATURE 0
#define USE_LDR 0
#define USE_LED 0
#define USE_WATER_PUMP 0
#define USE_HEATER 0
#define USE_FAN 0
#define DEVICE_TYPE_NAME "humidity-sensor"

#elif defined(TYPE_LIGHT_SENSOR)
#define SENSOR_TYPE "light"
#define SENSOR_UNIT "lux"
#define USE_DHT 0
#define USE_LDR 1
#define USE_LED 0
#define USE_WATER_PUMP 0
#define USE_HEATER 0
#define USE_FAN 0
#define DEVICE_TYPE_NAME "light-sensor"

#elif defined(TYPE_LIGHTING_ACTUATOR)
#define SENSOR_TYPE ""
#define USE_DHT 0
#define USE_LDR 0
#define USE_LED 1
#define USE_WATER_PUMP 0
#define USE_HEATER 0
#define USE_FAN 0
#define DEVICE_TYPE_NAME "lighting-actuator"

#elif defined(TYPE_WATERING_ACTUATOR)
#define SENSOR_TYPE ""
#define USE_DHT 0
#define USE_LDR 0
#define USE_LED 0
#define USE_WATER_PUMP 1
#define USE_HEATER 0
#define USE_FAN 0
#define DEVICE_TYPE_NAME "watering-actuator"

#elif defined(TYPE_HEATING_ACTUATOR)
#define SENSOR_TYPE ""
#define USE_DHT 0
#define USE_LDR 0
#define USE_LED 0
#define USE_WATER_PUMP 0
#define USE_HEATER 1
#define USE_FAN 0
#define DEVICE_TYPE_NAME "heating-actuator"

#elif defined(TYPE_VENTILATION_ACTUATOR)
#define SENSOR_TYPE ""
#define USE_DHT 0
#define USE_LDR 0
#define USE_LED 0
#define USE_WATER_PUMP 0
#define USE_HEATER 0
#define USE_FAN 1
#define DEVICE_TYPE_NAME "ventilation-actuator"

#else
#error "No device type defined! See platformio.ini"
#endif

#define IS_ACTUATOR (USE_LED || USE_WATER_PUMP || USE_HEATER || USE_FAN)

#if USE_DHT
#include <DHT.h>
#endif

// ==================== CONFIG ====================

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

#if USE_DHT
#define DHT_PIN 15
DHT dht(DHT_PIN, DHT22);
#endif
#if USE_LDR
#define LDR_PIN 34
#endif
#if USE_LED
#define LED_PIN 2
#endif
#if USE_WATER_PUMP
#define WATER_PUMP_PIN 4
#endif
#if USE_HEATER
#define HEATER_PIN 5
#endif
#if USE_FAN
#define FAN_PIN 18
#endif

// ==================== OBJECTS ====================

WiFiClient espClient;
PubSubClient mqtt(espClient);

char topicBuf[64];
char payloadBuf[128];
unsigned long lastSend = 0;

// ==================== WIFI ====================

void connectWiFi()
{
    Serial.print("[WiFi] Connecting...");
    WiFi.begin(WIFI_SSID, WIFI_PASS, 6);
    while (WiFi.status() != WL_CONNECTED)
    {
        delay(500);
        Serial.print(".");
    }
    Serial.printf(" OK, IP: %s\n", WiFi.localIP().toString().c_str());
}

// ==================== MQTT CALLBACK (actuators only) ====================

void onMqttMessage(char *topic, byte *payload, unsigned int length)
{
#if IS_ACTUATOR
    payload[length] = '\0';

    JsonDocument doc;
    if (deserializeJson(doc, (char *)payload))
        return;

    const char *command = doc["command"];
    if (!command)
        return;

    bool turnOn = (strcmp(command, "on") == 0);

#if USE_LED
    digitalWrite(LED_PIN, turnOn ? HIGH : LOW);
    Serial.printf("[LED] %s\n", turnOn ? "ON" : "OFF");
    snprintf(topicBuf, sizeof(topicBuf), "devices/%d/status/lighting", DEVICE_ID);
#elif USE_WATER_PUMP
    digitalWrite(WATER_PUMP_PIN, turnOn ? HIGH : LOW);
    Serial.printf("[WATER_PUMP] %s\n", turnOn ? "ON" : "OFF");
    snprintf(topicBuf, sizeof(topicBuf), "devices/%d/status/watering", DEVICE_ID);
#elif USE_HEATER
    digitalWrite(HEATER_PIN, turnOn ? HIGH : LOW);
    Serial.printf("[HEATER] %s\n", turnOn ? "ON" : "OFF");
    snprintf(topicBuf, sizeof(topicBuf), "devices/%d/status/heating", DEVICE_ID);
#elif USE_FAN
    digitalWrite(FAN_PIN, turnOn ? HIGH : LOW);
    Serial.printf("[FAN] %s\n", turnOn ? "ON" : "OFF");
    snprintf(topicBuf, sizeof(topicBuf), "devices/%d/status/ventilation", DEVICE_ID);
#endif

    snprintf(payloadBuf, sizeof(payloadBuf), "{\"status\":\"%s\"}", command);
    mqtt.publish(topicBuf, payloadBuf, false);
    Serial.printf("[MQTT] Status sent: %s\n", topicBuf);
#else
    (void)topic;
    (void)payload;
    (void)length;
#endif
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

            // Announce online status
            snprintf(topicBuf, sizeof(topicBuf), "devices/%d/lwt", DEVICE_ID);
            mqtt.publish(topicBuf, "{\"status\":\"online\"}", false);

#if IS_ACTUATOR
            snprintf(topicBuf, sizeof(topicBuf), "devices/%d/commands/+", DEVICE_ID);
            mqtt.subscribe(topicBuf, 1);
            Serial.printf("[MQTT] Subscribed: %s\n", topicBuf);
#endif
        }
        else
        {
            Serial.printf("[MQTT] Failed rc=%d, retry 3s...\n", mqtt.state());
            delay(3000);
        }
    }
}

// ==================== PUBLISH (sensors only) ====================

void publishSensor()
{
#if USE_DHT && USE_DHT_TEMPERATURE
    float val = dht.readTemperature();
    if (isnan(val))
        return;
    Serial.printf("[SENSOR] temperature = %.1f°C\n", val);
#elif USE_DHT
    float val = dht.readHumidity();
    if (isnan(val))
        return;
    Serial.printf("[SENSOR] humidity = %.1f%%\n", val);
#elif USE_LDR
    int raw = analogRead(LDR_PIN);
    const float GAMMA = 0.7;
    const float RL10 = 50; // kOhm at 10 lux
    const float VCC = 3.3;
    float voltage = raw / 4095.0 * VCC;
    float val = 0;
    if (voltage > 0.01 && voltage < (VCC - 0.01)) {
        float resistance = 10000.0 * voltage / (VCC - voltage);
        val = pow(RL10 * 1e3 * pow(10, GAMMA) / resistance, 1.0 / GAMMA);
    }
    Serial.printf("[SENSOR] light = %.0f lux (raw=%d, V=%.2f)\n", val, raw, voltage);
#else
    return;
#endif

#if !IS_ACTUATOR
    snprintf(topicBuf, sizeof(topicBuf), "devices/%d/sensors/%s", DEVICE_ID, SENSOR_TYPE);
    snprintf(payloadBuf, sizeof(payloadBuf), "{\"value\":%.2f}", val);
    mqtt.publish(topicBuf, payloadBuf);
#endif
}

// ==================== SETUP ====================

void setup()
{
    Serial.begin(115200);
    delay(100);

    Serial.println("========================================");
    Serial.printf("  %s  (device %d)\n", DEVICE_TYPE_NAME, DEVICE_ID);
    Serial.println("========================================");

#if USE_LED
    pinMode(LED_PIN, OUTPUT);
    digitalWrite(LED_PIN, LOW);
#endif
#if USE_WATER_PUMP
    pinMode(WATER_PUMP_PIN, OUTPUT);
    digitalWrite(WATER_PUMP_PIN, LOW);
#endif
#if USE_HEATER
    pinMode(HEATER_PIN, OUTPUT);
    digitalWrite(HEATER_PIN, LOW);
#endif
#if USE_FAN
    pinMode(FAN_PIN, OUTPUT);
    digitalWrite(FAN_PIN, LOW);
#endif
#if USE_DHT
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
#if IS_ACTUATOR
        // Heartbeat — keep device online
        snprintf(topicBuf, sizeof(topicBuf), "devices/%d/lwt", DEVICE_ID);
        mqtt.publish(topicBuf, "{\"status\":\"online\"}", false);
#else
        publishSensor();
#endif
        lastSend = millis();
    }
}
