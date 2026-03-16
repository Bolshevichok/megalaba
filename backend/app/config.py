"""Application configuration using Pydantic Settings."""

from pydantic import ConfigDict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables.

    Attributes:
        DATABASE_URL: PostgreSQL connection string.
        SECRET_KEY: JWT signing secret key.
        CORS_ORIGINS: Comma-separated list of allowed CORS origins.
        ACCESS_TOKEN_EXPIRE_MINUTES: Access token TTL in minutes.
        REFRESH_TOKEN_EXPIRE_DAYS: Refresh token TTL in days.
        MQTT_BROKER_HOST: Mosquitto broker hostname.
        MQTT_BROKER_PORT: Mosquitto broker port.
        MQTT_USERNAME: MQTT authentication username.
        MQTT_PASSWORD: MQTT authentication password.
    """

    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/greenhouse"
    SECRET_KEY: str = "changeme"
    CORS_ORIGINS: str = "http://localhost:3000"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    MQTT_BROKER_HOST: str = "localhost"
    MQTT_BROKER_PORT: int = 1883
    MQTT_USERNAME: str = "backend"
    MQTT_PASSWORD: str = "mqtt_secret"

    model_config = ConfigDict(env_file=".env")


settings = Settings()
