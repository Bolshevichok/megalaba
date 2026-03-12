"""Shared test fixtures for the Smart Greenhouse test suite."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.models import ActuatorType, SensorType, User

TEST_DB_URL = "sqlite://"

engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False}, poolclass=StaticPool)


@event.listens_for(engine, "connect")
def _set_sqlite_pragma(dbapi_conn, connection_record):
    """Enable FK support in SQLite for cascade tests."""
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


TestingSessionLocal = sessionmaker(bind=engine, class_=Session, expire_on_commit=False)


@pytest.fixture(autouse=True)
def db_session():
    """Create a fresh database for each test.

    Yields:
        Session: Test database session.
    """
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    _seed_reference_data(session)
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


def _seed_reference_data(session: Session):
    """Insert reference data (sensor types, actuator types).

    Args:
        session: Database session.
    """
    for name in ["temperature", "humidity", "light"]:
        session.add(SensorType(name=name))
    for name in ["lighting", "heating", "ventilation", "watering"]:
        session.add(ActuatorType(name=name))
    session.commit()


@pytest.fixture
def client(db_session):
    """Create a test HTTP client with DB dependency override.

    Args:
        db_session: Test database session.

    Yields:
        TestClient: FastAPI test client.
    """

    def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def test_user(db_session) -> User:
    """Create a test user in the database.

    Args:
        db_session: Test database session.

    Returns:
        User: Created test user.
    """
    from passlib.context import CryptContext

    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    user = User(
        name="Test User",
        email="test@example.com",
        password_hash=pwd_context.hash("testpass123"),
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def auth_headers(client, test_user) -> dict:
    """Get authorization headers with a valid JWT token.

    Args:
        client: Test HTTP client.
        test_user: Test user in DB.

    Returns:
        dict: Headers with Authorization Bearer token.
    """
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "test@example.com", "password": "testpass123"},
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
