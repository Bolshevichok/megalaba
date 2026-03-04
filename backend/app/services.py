from datetime import datetime, timezone

from fastapi import HTTPException, status
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import settings
from app.database import MockSession, mock_store

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ALGORITHM = "HS256"

# ── Helpers ────────────────────────────────────────────────────────


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _next_id(key: str) -> int:
    mock_store["counters"][key] += 1
    return mock_store["counters"][key]


def _ensure_mock(db) -> dict:
    if isinstance(db, MockSession):
        return db.store
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="Database unavailable",
    )


# ── Seed data (runs once on import when USE_MOCK_DB=true) ─────────

if settings.USE_MOCK_DB:
    _seed_devices = [
        {
            "id": 1, "device_id": "greenhouse_01", "name": "Main Greenhouse",
            "description": "Primary growing area", "location": "Building A, Section 1",
            "device_type": "greenhouse", "is_active": True, "is_online": True,
            "last_seen": _now().isoformat(), "mqtt_client_id": "esp32_greenhouse_01",
            "config": {"wifi_strength": -45, "firmware_version": "1.0.0"},
            "created_at": _now().isoformat(), "updated_at": _now().isoformat(),
        },
        {
            "id": 2, "device_id": "greenhouse_02", "name": "Secondary Greenhouse",
            "description": "Secondary growing area", "location": "Building A, Section 2",
            "device_type": "greenhouse", "is_active": True, "is_online": False,
            "last_seen": None, "mqtt_client_id": "esp32_greenhouse_02",
            "config": None,
            "created_at": _now().isoformat(), "updated_at": _now().isoformat(),
        },
        {
            "id": 3, "device_id": "greenhouse_03", "name": "Test Environment",
            "description": "Testing", "location": "Lab",
            "device_type": "greenhouse", "is_active": True, "is_online": True,
            "last_seen": _now().isoformat(), "mqtt_client_id": "esp32_greenhouse_03",
            "config": None,
            "created_at": _now().isoformat(), "updated_at": _now().isoformat(),
        },
    ]
    for d in _seed_devices:
        mock_store["devices"][d["device_id"]] = d
    mock_store["counters"]["device"] = 3

    mock_store["sensor_readings"] = [
        {"id": 1, "device_id": "greenhouse_01", "sensor_type": "temperature",
         "value": 22.5, "unit": "°C", "timestamp": _now().isoformat()},
        {"id": 2, "device_id": "greenhouse_01", "sensor_type": "humidity",
         "value": 65.0, "unit": "%", "timestamp": _now().isoformat()},
        {"id": 3, "device_id": "greenhouse_01", "sensor_type": "light",
         "value": 8500, "unit": "lux", "timestamp": _now().isoformat()},
    ]
    mock_store["counters"]["sensor"] = 3

    mock_store["actuator_states"] = {
        "greenhouse_01": {
            "lighting": {"status": "on", "last_command": _now().isoformat(), "last_update": _now().isoformat()},
            "heating": {"status": "off", "last_command": _now().isoformat(), "last_update": _now().isoformat()},
            "ventilation": {"status": "on", "last_command": _now().isoformat(), "last_update": _now().isoformat()},
            "watering": {"status": "off", "last_command": _now().isoformat(), "last_update": _now().isoformat()},
        },
    }


# ── Auth services ──────────────────────────────────────────────────


def register_user(db, data: dict) -> dict:
    store = _ensure_mock(db)
    if any(u["username"] == data["username"] for u in store["users"].values()):
        raise HTTPException(status_code=409, detail="Username already exists")
    if any(u["email"] == data["email"] for u in store["users"].values()):
        raise HTTPException(status_code=409, detail="Email already exists")
    uid = _next_id("user")
    user = {
        "id": uid,
        "username": data["username"],
        "email": data["email"],
        "password_hash": pwd_context.hash(data["password"]),
        "is_active": True,
        "is_superuser": False,
        "created_at": _now().isoformat(),
        "updated_at": _now().isoformat(),
    }
    store["users"][uid] = user
    return user


def authenticate_user(db, username: str, password: str) -> dict | None:
    store = _ensure_mock(db)
    for u in store["users"].values():
        if u["username"] == username and pwd_context.verify(password, u["password_hash"]):
            return u
    return None


def create_access_token(user_id: int) -> str:
    expire = _now().timestamp() + settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    return jwt.encode(
        {"sub": str(user_id), "exp": expire, "type": "access"},
        settings.SECRET_KEY,
        algorithm=ALGORITHM,
    )


def create_refresh_token(user_id: int) -> str:
    expire = _now().timestamp() + 7 * 24 * 60 * 60  # 7 days
    return jwt.encode(
        {"sub": str(user_id), "exp": expire, "type": "refresh"},
        settings.SECRET_KEY,
        algorithm=ALGORITHM,
    )


def verify_access_token(token: str) -> dict | None:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "access":
            return None
        return payload
    except JWTError:
        return None


def verify_refresh_token(token: str) -> dict | None:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "refresh":
            return None
        return payload
    except JWTError:
        return None


def get_user_by_id(db, user_id: str | int) -> dict | None:
    store = _ensure_mock(db)
    return store["users"].get(int(user_id))


# ── Device services ────────────────────────────────────────────────


def list_devices(
    db, limit: int = 100, offset: int = 0,
    is_active: bool | None = None, is_online: bool | None = None,
) -> tuple[list[dict], int]:
    store = _ensure_mock(db)
    devices = list(store["devices"].values())
    if is_active is not None:
        devices = [d for d in devices if d["is_active"] == is_active]
    if is_online is not None:
        devices = [d for d in devices if d["is_online"] == is_online]
    total = len(devices)
    return devices[offset : offset + limit], total


def get_device(db, device_id: str) -> dict | None:
    store = _ensure_mock(db)
    return store["devices"].get(device_id)


def create_device(db, data: dict) -> dict:
    store = _ensure_mock(db)
    if data["device_id"] in store["devices"]:
        raise HTTPException(status_code=409, detail="Device already exists")
    did = _next_id("device")
    device = {
        "id": did,
        "device_id": data["device_id"],
        "name": data["name"],
        "description": data.get("description"),
        "location": data.get("location"),
        "device_type": data.get("device_type", "greenhouse"),
        "is_active": True,
        "is_online": False,
        "last_seen": None,
        "mqtt_client_id": None,
        "config": None,
        "created_at": _now().isoformat(),
        "updated_at": _now().isoformat(),
    }
    store["devices"][data["device_id"]] = device
    return device


def update_device(db, device_id: str, data: dict) -> dict | None:
    store = _ensure_mock(db)
    device = store["devices"].get(device_id)
    if device is None:
        return None
    for k, v in data.items():
        if v is not None and k in device:
            device[k] = v
    device["updated_at"] = _now().isoformat()
    return device


def delete_device(db, device_id: str) -> bool:
    store = _ensure_mock(db)
    if device_id not in store["devices"]:
        return False
    store["devices"][device_id]["is_active"] = False
    return True


# ── Sensor services ────────────────────────────────────────────────

VALID_SENSOR_TYPES = {"temperature", "humidity", "light"}
SENSOR_UNITS = {"temperature": "°C", "humidity": "%", "light": "lux"}


def get_latest_readings(db, device_id: str) -> list[dict]:
    store = _ensure_mock(db)
    readings = [r for r in store["sensor_readings"] if r["device_id"] == device_id]
    latest = {}
    for r in readings:
        latest[r["sensor_type"]] = r
    return list(latest.values())


def get_sensor_history(
    db, device_id: str, sensor_type: str,
    start_time: str | None = None, end_time: str | None = None,
    limit: int = 100, aggregation: str | None = None,
) -> tuple[list[dict], dict | None]:
    store = _ensure_mock(db)
    readings = [
        r for r in store["sensor_readings"]
        if r["device_id"] == device_id and r["sensor_type"] == sensor_type
    ][:limit]
    if not readings:
        return [], None
    values = [float(r["value"]) for r in readings]
    stats = {
        "min": min(values),
        "max": max(values),
        "avg": round(sum(values) / len(values), 2),
        "count": len(values),
    }
    return readings, stats


def create_reading(db, device_id: str, sensor_type: str, data: dict) -> dict:
    store = _ensure_mock(db)
    rid = _next_id("sensor")
    reading = {
        "id": rid,
        "device_id": device_id,
        "sensor_type": sensor_type,
        "value": data["value"],
        "unit": SENSOR_UNITS.get(sensor_type, ""),
        "timestamp": data.get("timestamp", _now().isoformat()),
    }
    store["sensor_readings"].append(reading)
    return reading


# ── Actuator services ──────────────────────────────────────────────

VALID_ACTUATOR_TYPES = {"lighting", "heating", "ventilation", "watering"}
VALID_COMMANDS = {"on", "off", "toggle", "set_level"}


def get_actuator_statuses(db, device_id: str) -> list[dict]:
    store = _ensure_mock(db)
    states = store.get("actuator_states", {}).get(device_id, {})
    return [
        {
            "actuator_type": atype,
            "status": info["status"],
            "last_command": info.get("last_command"),
            "last_update": info.get("last_update"),
        }
        for atype, info in states.items()
    ]


def send_command(db, device_id: str, actuator_type: str, command: str, parameters: dict | None = None) -> dict:
    store = _ensure_mock(db)
    cid = _next_id("actuator")
    cmd = {
        "id": cid,
        "device_id": device_id,
        "actuator_type": actuator_type,
        "command": command,
        "parameters": parameters,
        "status": "pending",
        "created_at": _now().isoformat(),
        "executed_at": None,
        "confirmed_at": None,
    }
    store["actuator_commands"].append(cmd)
    return cmd


def get_command_history(
    db, device_id: str, actuator_type: str,
    start_time: str | None = None, end_time: str | None = None,
    cmd_status: str | None = None, limit: int = 100,
) -> list[dict]:
    store = _ensure_mock(db)
    cmds = [
        c for c in store["actuator_commands"]
        if c["device_id"] == device_id and c["actuator_type"] == actuator_type
    ]
    if cmd_status:
        cmds = [c for c in cmds if c["status"] == cmd_status]
    return cmds[:limit]


# ── Dashboard services ─────────────────────────────────────────────


def get_overview(db) -> dict:
    store = _ensure_mock(db)
    devices = list(store["devices"].values())
    online = [d for d in devices if d["is_online"]]
    offline = [d for d in devices if not d["is_online"]]

    device_overviews = []
    for d in devices:
        readings = get_latest_readings(db, d["device_id"])
        current_readings = {r["sensor_type"]: {"value": r["value"], "unit": r["unit"]} for r in readings}
        statuses = get_actuator_statuses(db, d["device_id"])
        actuator_status = {s["actuator_type"]: s["status"] for s in statuses}
        device_overviews.append({
            "device_id": d["device_id"],
            "name": d["name"],
            "is_online": d["is_online"],
            "current_readings": current_readings,
            "actuator_status": actuator_status,
        })

    return {
        "summary": {
            "total_devices": len(devices),
            "online_devices": len(online),
            "offline_devices": len(offline),
            "active_alerts": 0,
        },
        "devices": device_overviews,
    }
