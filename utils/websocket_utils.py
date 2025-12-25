# websocket/manager.py
from typing import Callable, Dict
from fastapi import WebSocket
from asyncio import Lock


class Session:
    def __init__(self, ws: WebSocket, role: str):
        self.ws = ws
        self.role = role


class WebSocketManager:
    def __init__(self):
        self.sessions: Dict[str, Session] = {}
        self._lock = Lock()

    async def connect(self, client_id: str, ws: WebSocket, role: str):
        async with self._lock:
            await ws.accept()
            self.sessions[client_id] = Session(ws, role)

    async def disconnect(self, client_id: str):
        async with self._lock:
            if client_id in self.sessions:
                await self.sessions[client_id].ws.close()
                self.sessions.pop(client_id, None)

    async def broadcast(self, message: dict, predicate: Callable):
        async with self._lock:
            targets = self.sessions.values()

        if not targets:
            return

        for session in self.sessions.values():
            if predicate(session):
                await session.ws.send_json(message)


ws_manager = WebSocketManager()
