#include <Arduino.h>
#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>

// ==================== DEVICE TYPE FLAGS ====================
// Set via build_flags in platformio.ini:
//   -DTYPE_CLIMATE_SENSOR   — DHT22 only (temperature + humidity)
//   -DTYPE_LIGHT_CONTROLLER — LDR + LED (light sensing + lighting control)
//   -DTYPE_FULL_GREENHOUSE  — all sensors + all actuators

#if defined(TYPE_CLIMATE_SENSOR)
#define HAS_DHT 1
#define HAS_LDR 0
#define HAS_LED 0
#define DEVICE_TYPE_NAME "climate-sensor"
#elif defined(TYPE_LIGHT_CONTROLLER)
#define HAS_DHT 0
#define HAS_LDR 1
#define HAS_LED 1
#define DEVICE_TYPE_NAME "light-controller"
#elif defined(TYPE_FULL_GREENHOUSE)
#define HAS_DHT 1
#define HAS_LDR 1
#define HAS_LED 1
#define DEVICE_TYPE_NAME "full-greenhouse"
#else
#error "No device type defined! Add -DTYPE_CLIMATE_SENSOR, -DTYPE_LIGHT_CONTROLLER, or -DTYPE_FULL_GREENHOUSE to build_flags"
#endif

#if HAS_DHT
#include <DHT.h>
#endif

// ==================== CONFIGURATION ====================

const char *WIFI_SSID = "Wokwi-GUEST";
const char *WIFI_PASS = "";

const char *MQTT_SERVER = "host.wokwi.internal";
const int MQTT_PORT = 1883;
const char *MQTT_USER = "backend";
const char *MQTT_PASS = "mqtt_secret";

// Device ID — each instance gets its own ID via build flag
#ifndef DEVICE_ID
#define DEVICE_ID 1
#endif

const unsigned long SEND_INTERVAL = 5000;

// ==================== PINS ====================

#if HAS_DHT
#define DHT_PIN 15
#endif
#if HAS_LDR
#define LDR_PIN 34
#endif
#if HAS_LED
#define LED_PIN 2
#endif

// ==================== OBJECTS ====================

#if HAS_DHT
DHT dht(DHT_PIN, DHT22);
#endif
WiFiClient espClient;
PubSubClient mqtt(espClient);

char topicBuf[64];
char payloadBuf[128];
unsigned long lastSend = 0;

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
#if HAS_LED
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

    if (actuatorType == "lighting")
    {
        bool turnOn = (strcmp(command, "on") == 0);
        digitalWrite(LED_PIN, turnOn ? HIGH : LOW);
        Serial.printf("[LED] %s\n", turnOn ? "ON" : "OFF");
    }

    // Send status confirmation
    snprintf(topicBuf, sizeof(topicBuf), "devices/%d/status/%s", DEVICE_ID, actuatorType.c_str());
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

#if HAS_LED
            snprintf(topicBuf, sizeof(topicBuf), "devices/%d/commands/+", DEVICE_ID);
            mqtt.subscribe(topicBuf, 1);
            Serial.printf("[MQTT] Subscribed to: %s\n", topicBuf);
#endif
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
#if HAS_DHT
    float temperature = dht.readTemperature();
    float humidity = dht.readHumidity();

    if (!isnan(temperature))
    {
        snprintf(topicBuf, sizeof(topicBuf), "devices/%d/sensors/temperature", DEVICE_ID);
        snprintf(payloadBuf, sizeof(payloadBuf), "{\"value\":%.2f}", temperature);
        mqtt.publish(topicBuf, payloadBuf);
    }

    if (!isnan(humidity))
    {
        snprintf(topicBuf, sizeof(topicBuf), "devices/%d/sensors/humidity", DEVICE_ID);
        snprintf(payloadBuf, sizeof(payloadBuf), "{\"value\":%.2f}", humidity);
        mqtt.publish(topicBuf, payloadBuf);
    }

    Serial.printf("[SENSORS] T=%.1f°C  H=%.1f%%\n", temperature, humidity);
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

#if HAS_LED
    pinMode(LED_PIN, OUTPUT);
    digitalWrite(LED_PIN, LOW);
#endif

#if HAS_DHT
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
