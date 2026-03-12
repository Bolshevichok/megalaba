"""WebSocket connection manager for real-time greenhouse updates.

Manages per-greenhouse WebSocket connections and broadcasts
sensor_update, actuator_update, and device_status events.
"""

import logging
from collections import defaultdict

from fastapi import WebSocket
from jose import JWTError, jwt

from app.config import settings

logger = logging.getLogger("greenhouse.ws")


class ConnectionManager:
    """Manages WebSocket connections grouped by greenhouse ID.

    Attributes:
        connections: Dict mapping greenhouse_id to set of WebSocket connections.
    """

    def __init__(self):
        """Initialize the connection manager with empty connection store."""
        self.connections: dict[int, set[WebSocket]] = defaultdict(set)

    async def connect(self, websocket: WebSocket, greenhouse_id: int) -> bool:
        """Accept a WebSocket connection and authenticate via first message.

        The client must send a JSON message with a valid JWT token
        as the first message: {"token": "<jwt_access_token>"}.

        Args:
            websocket: WebSocket connection.
            greenhouse_id: Greenhouse to subscribe to.

        Returns:
            True if authenticated, False otherwise.
        """
        await websocket.accept()

        try:
            data = await websocket.receive_json()
            token = data.get("token", "")
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
            if payload.get("type") != "access":
                await websocket.close(code=4001, reason="Invalid token")
                return False
        except (JWTError, Exception):
            await websocket.close(code=4001, reason="Authentication failed")
            return False

        self.connections[greenhouse_id].add(websocket)
        logger.info("WebSocket connected to greenhouse %s", greenhouse_id)
        return True

    def disconnect(self, websocket: WebSocket, greenhouse_id: int):
        """Remove a WebSocket connection.

        Args:
            websocket: WebSocket to remove.
            greenhouse_id: Greenhouse the socket was subscribed to.
        """
        self.connections[greenhouse_id].discard(websocket)
        if not self.connections[greenhouse_id]:
            del self.connections[greenhouse_id]

    async def broadcast(self, greenhouse_id: int, message: dict):
        """Broadcast a message to all connections for a greenhouse.

        Args:
            greenhouse_id: Target greenhouse.
            message: Dict with 'type' and 'data' fields.
        """
        dead = []
        for ws in self.connections.get(greenhouse_id, set()):
            try:
                await ws.send_json(message)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.connections[greenhouse_id].discard(ws)


ws_manager = ConnectionManager()
