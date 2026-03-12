"""MQTT client for communication with IoT devices.

Manages connection to Mosquitto broker, topic subscriptions,
and message publishing with QoS levels per Constitution II.
"""

import logging

import paho.mqtt.client as paho_mqtt

from app.config import settings
from app.mqtt.topics import LWT_TOPIC_PATTERN, SENSOR_TOPIC_PATTERN, STATUS_TOPIC_PATTERN

logger = logging.getLogger("greenhouse.mqtt")


class MQTTClient:
    """Manages MQTT connection to Mosquitto broker.

    Handles connect/disconnect lifecycle, subscriptions to sensor
    and status topics, and publishing commands to actuators.

    Attributes:
        client: Paho MQTT client instance.
        connected: Whether the client is currently connected.
    """

    def __init__(self):
        """Initialize MQTT client with broker settings."""
        self.client = paho_mqtt.Client(paho_mqtt.CallbackAPIVersion.VERSION2)
        self.client.username_pw_set(settings.MQTT_USERNAME, settings.MQTT_PASSWORD)
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.connected = False

    def _on_connect(self, client, userdata, flags, rc, properties=None):
        """Handle successful connection by subscribing to topics.

        Args:
            client: MQTT client instance.
            userdata: User data.
            flags: Connection flags.
            rc: Connection result code.
            properties: MQTT v5 properties.
        """
        from app.mqtt.handlers import on_message

        if rc == 0:
            self.connected = True
            client.subscribe(SENSOR_TOPIC_PATTERN, qos=0)
            client.subscribe(STATUS_TOPIC_PATTERN, qos=1)
            client.subscribe(LWT_TOPIC_PATTERN, qos=1)
            client.on_message = on_message
            logger.info("MQTT subscribed to sensor, status, and LWT topics")
        else:
            logger.error("MQTT connection failed with code %s", rc)

    def _on_disconnect(self, client, userdata, flags, rc, properties=None):
        """Handle disconnection events.

        Args:
            client: MQTT client instance.
            userdata: User data.
            flags: Disconnect flags.
            rc: Disconnect reason code.
            properties: MQTT v5 properties.
        """
        self.connected = False
        if rc != 0:
            logger.warning("MQTT unexpected disconnect (rc=%s), will reconnect", rc)

    def connect(self):
        """Connect to the MQTT broker and start the network loop.

        Uses loop_start() for background thread processing.
        Paho handles automatic reconnection.
        """
        try:
            self.client.connect(settings.MQTT_BROKER_HOST, settings.MQTT_BROKER_PORT)
            self.client.loop_start()
            logger.info("MQTT connecting to %s:%s", settings.MQTT_BROKER_HOST, settings.MQTT_BROKER_PORT)
        except Exception as e:
            logger.warning("MQTT connection failed: %s", e)
            self.connected = False

    def disconnect(self):
        """Disconnect from the MQTT broker and stop the network loop."""
        self.client.loop_stop()
        self.client.disconnect()
        self.connected = False
        logger.info("MQTT disconnected")

    def publish(self, topic: str, payload: str, qos: int = 1):
        """Publish a message to an MQTT topic.

        Args:
            topic: MQTT topic string.
            payload: JSON message payload.
            qos: Quality of service level (default 1 for commands per Constitution II).
        """
        if self.connected:
            self.client.publish(topic, payload, qos=qos)
            logger.info("MQTT published to %s", topic)
        else:
            logger.warning("MQTT not connected, cannot publish to %s", topic)


mqtt_client = MQTTClient()
