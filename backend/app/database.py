from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import settings


class Base(DeclarativeBase):
    pass


if settings.USE_MOCK_DB:
    engine = None
    SessionLocal = None
else:
    engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)
    SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


# In-memory mock store shared across mock sessions
mock_store: dict = {
    "devices": {},
    "sensor_readings": [],
    "actuator_commands": [],
    "users": {},
    "counters": {"device": 0, "sensor": 0, "actuator": 0, "user": 0},
}


class MockSession:
    """Minimal session-like object for mock mode."""

    def __init__(self, store: dict):
        self.store = store

    def close(self):
        pass


def get_db() -> Generator[Session | MockSession, None, None]:
    if settings.USE_MOCK_DB:
        yield MockSession(mock_store)
    else:
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()
