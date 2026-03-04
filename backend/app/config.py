from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://localhost/greenhouse"
    USE_MOCK_DB: bool = False
    SECRET_KEY: str = "changeme"
    CORS_ORIGINS: str = "http://localhost:3000"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
