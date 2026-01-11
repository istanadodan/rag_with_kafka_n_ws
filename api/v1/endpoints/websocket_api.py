from fastapi import WebSocket, APIRouter, WebSocketDisconnect
from infra.messaging.websocket.session import ws_manager
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(ws: WebSocket, client_id: str, role: str):
    await ws_manager.connect(client_id, ws, role)
    try:
        while True:
            data = await ws.receive_text()
            if data:
                await ws_manager.broadcast(
                    message=dict(value=dict(answer=f"Message text was: {data}")),
                    predicate=lambda x: x.client_id == client_id,
                )
            logging.info(f"Message text was: {data}")
    except WebSocketDisconnect as e:
        logging.error(e)
    finally:
        await ws_manager.disconnect(client_id)
