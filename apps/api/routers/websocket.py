"""
ATHENA Real-Time WebSocket Streaming Gateway
Streams live price ticks, agent signals, risk alerts, and order fills to dashboards.
"""

import asyncio
import json
from typing import List, Set
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from packages.event_bus.bus import event_bus
from packages.logging.logger import get_logger
from packages.schemas.events import Event

logger = get_logger("athena.websocket")
router = APIRouter(tags=["WebSocket"])


class ConnectionManager:
    """Manages active WebSocket dashboard client connections."""

    def __init__(self):
        self.active_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info(f"WebSocket client connected. Active clients: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)
        logger.info(f"WebSocket client disconnected. Active clients: {len(self.active_connections)}")

    async def broadcast(self, message: dict):
        dead_sockets: List[WebSocket] = []
        for connection in list(self.active_connections):
            try:
                await connection.send_text(json.dumps(message))
            except Exception:
                dead_sockets.append(connection)

        for s in dead_sockets:
            self.disconnect(s)


manager = ConnectionManager()


# Register event_bus subscriber to forward all events to connected WebSockets
async def forward_event_to_websockets(event: Event):
    await manager.broadcast(
        {
            "type": event.event_type.value,
            "timestamp": event.timestamp.isoformat() + "Z",
            "correlation_id": event.correlation_id,
            "payload": event.payload,
        }
    )


event_bus.subscribe_all(forward_event_to_websockets)


@router.websocket("/ws/stream")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Keep-alive heartbeat & client command listener
            data = await websocket.receive_text()
            try:
                msg = json.loads(data)
                if msg.get("action") == "ping":
                    await websocket.send_text(json.dumps({"type": "PONG", "timestamp": msg.get("timestamp")}))
            except Exception:
                pass
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.warning(f"WebSocket connection error: {str(e)}")
        manager.disconnect(websocket)
