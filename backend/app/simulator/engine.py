"""Simulator engine for generating fake sensor readings.

Runs an asyncio background loop that periodically generates sensor
readings for all devices in the database using physics-based models.
"""

import asyncio
import logging
import time
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import (
    ActuatorType,
    Device,
    SensorReading,
    SensorType,
)
from app.simulator.sensors import HumidityModel, LightModel, TemperatureModel

logger = logging.getLogger("greenhouse.simulator")

MODEL_MAP: dict[str, TemperatureModel | HumidityModel | LightModel] = {
    "temperature": TemperatureModel(),
    "humidity": HumidityModel(),
    "light": LightModel(),
}


class SimulatorEngine:
    """Background engine that generates simulated sensor data.

    Manages an asyncio task that polls the database every 5 seconds,
    generates readings for each sensor using the appropriate physics
    model, and persists results back to the database.

    Attributes:
        running: Whether the simulator loop is currently active.
        task: Reference to the running asyncio Task, or None.
        start_time: Unix timestamp when the simulator was started.
        readings_generated: Total number of sensor readings created.
        devices_count: Number of devices found on last DB poll.
    """

    def __init__(self) -> None:
        """Initialize the simulator engine in stopped state."""
        self.running: bool = False
        self.task: asyncio.Task | None = None
        self.start_time: float = 0.0
        self.readings_generated: int = 0
        self.devices_count: int = 0

    def start(self) -> dict:
        """Start the simulator background task.

        If the simulator is already running, returns current status
        without starting a duplicate task (idempotent).

        Returns:
            Dict with 'status' and 'devices_count' keys.
        """
        if self.running:
            logger.info("Simulator already running, returning current status")
            return {"status": "running", "devices_count": self.devices_count}

        self.running = True
        self.start_time = time.time()
        self.readings_generated = 0

        db: Session = SessionLocal()
        try:
            self.devices_count = db.query(Device).count()
        finally:
            db.close()

        self.task = asyncio.create_task(self._run_loop())
        logger.info(
            "Simulator started with %d devices", self.devices_count
        )
        return {"status": "running", "devices_count": self.devices_count}

    def stop(self) -> dict:
        """Stop the simulator background task.

        Cancels the asyncio task and resets the running flag.

        Returns:
            Dict with 'status' key set to 'stopped'.
        """
        if self.task is not None:
            self.task.cancel()
            self.task = None
        self.running = False
        logger.info("Simulator stopped")
        return {"status": "stopped"}

    def get_status(self) -> dict:
        """Get current simulator status.

        Returns:
            Dict with status, uptime_seconds, devices_count,
            and readings_generated.
        """
        uptime = time.time() - self.start_time if self.running else 0.0
        return {
            "status": "running" if self.running else "stopped",
            "uptime_seconds": round(uptime, 2),
            "devices_count": self.devices_count,
            "readings_generated": self.readings_generated,
        }

    async def _run_loop(self) -> None:
        """Run the main simulator loop.

        Polls the database every 5 seconds, iterates over all devices
        and their sensors, generates readings using the matching model,
        and saves them to the database. Actuator states for each device
        are collected and passed to the models for realistic coupling.
        """
        logger.info("Simulator loop started")
        try:
            while self.running:
                db: Session = SessionLocal()
                try:
                    elapsed = time.time() - self.start_time
                    devices = db.query(Device).all()
                    self.devices_count = len(devices)

                    for device in devices:
                        # Collect actuator states for this device
                        actuator_states: dict[str, str] = {}
                        for actuator in device.actuators:
                            atype = (
                                db.query(ActuatorType)
                                .filter(ActuatorType.id == actuator.actuator_type_id)
                                .first()
                            )
                            if atype and actuator.status:
                                actuator_states[atype.name] = actuator.status.value

                        # Generate readings for each sensor
                        for sensor in device.sensors:
                            stype = (
                                db.query(SensorType)
                                .filter(SensorType.id == sensor.sensor_type_id)
                                .first()
                            )
                            if stype is None:
                                continue

                            model = MODEL_MAP.get(stype.name)
                            if model is None:
                                logger.warning(
                                    "No model for sensor type '%s'", stype.name
                                )
                                continue

                            value = model.generate(elapsed, actuator_states)
                            reading = SensorReading(
                                sensor_id=sensor.id,
                                value=value,
                                recorded_at=datetime.now(timezone.utc),
                            )
                            db.add(reading)
                            self.readings_generated += 1

                    db.commit()
                    logger.debug(
                        "Generated readings for %d devices (total: %d)",
                        self.devices_count,
                        self.readings_generated,
                    )
                except Exception:
                    db.rollback()
                    logger.exception("Error in simulator loop")
                finally:
                    db.close()

                await asyncio.sleep(5)
        except asyncio.CancelledError:
            logger.info("Simulator loop cancelled")


simulator_engine = SimulatorEngine()
