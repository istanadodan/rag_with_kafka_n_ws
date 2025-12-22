# websocket/manager.py
from typing import Callable, Dict
from fastapi import WebSocket


class Session:
    def __init__(self, ws: WebSocket, role: str):
        self.ws = ws
        self.role = role


class WebSocketManager:
    def __init__(self):
        self.sessions: Dict[str, Session] = {}

    async def connect(self, client_id: str, ws: WebSocket, role: str):
        await ws.accept()
        self.sessions[client_id] = Session(ws, role)

    def disconnect(self, client_id: str):
        self.sessions.pop(client_id, None)

    async def broadcast(self, message: dict, predicate: Callable):
        for session in self.sessions.values():
            if predicate(session):
                await session.ws.send_json(message)


ws_manager = WebSocketManager()
