"""Routes for simulator control.

Provides endpoints to start, stop, and query the status of the
greenhouse sensor data simulator. No authentication required.
"""

from fastapi import APIRouter

from app.simulator.engine import simulator_engine

router = APIRouter(tags=["simulator"])


@router.post("/simulator/start")
async def start_simulator() -> dict:
    """Start the simulator engine.

    If the simulator is already running, returns the current status
    without restarting (idempotent behaviour).

    Returns:
        Dict with 'status' and 'devices_count'.
    """
    return simulator_engine.start()


@router.post("/simulator/stop")
async def stop_simulator() -> dict:
    """Stop the simulator engine.

    Returns:
        Dict with 'status' set to 'stopped'.
    """
    return simulator_engine.stop()


@router.get("/simulator/status")
async def simulator_status() -> dict:
    """Get current simulator status.

    Returns:
        Dict with status, uptime_seconds, devices_count,
        and readings_generated.
    """
    return simulator_engine.get_status()
