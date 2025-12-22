from fastapi import WebSocket, APIRouter, WebSocketDisconnect
from utils.websocket_utils import ws_manager
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
                await ws.send_text(f"Message text was: {data}")
            logging.info(f"Message text was: {data}")
    except WebSocketDisconnect as e:
        logging.error(e)
    finally:
        ws_manager.disconnect(client_id)
