# websocket/manager.py
from typing import Callable, Dict
from fastapi import WebSocket
from utils.stomp_codec import build_frame, pars_stomp_text
import asyncio


class Session:
    def __init__(self, ws: WebSocket, role: str):
        self.ws = ws
        self.role = role


class WebSocketManager:
    def __init__(self):
        self.sessions: Dict[str, Session] = {}
        self._lock = asyncio.Lock()

    async def connect(self, client_id: str, ws: WebSocket, role: str):
        async with self._lock:
            await ws.accept()
            self.sessions[client_id] = Session(ws, role)

    async def disconnect(self, client_id: str):
        async with self._lock:
            if client_id in self.sessions:
                self.sessions.pop(client_id, None)

    async def broadcast(self, message: dict, predicate: Callable):
        async with self._lock:
            targets = self.sessions.values()

        if not targets:
            return

        for session in targets:
            if predicate(session):
                await session.ws.send_json(message)


ws_manager = WebSocketManager()


class Hub:
    def __init__(self) -> None:
        self._subs: dict[str, set[WebSocket]] = {}
        self._lock = asyncio.Lock()

    async def subscribe(self, ws: WebSocket, destination: str) -> None:
        async with self._lock:
            self._subs.setdefault(destination, set()).add(ws)

    async def cleanup(self, ws: WebSocket) -> None:
        async with self._lock:
            for dest in list(self._subs.keys()):
                self._subs[dest].discard(ws)
                if not self._subs[dest]:
                    self._subs.pop(dest, None)

    async def broadcast(self, destination: str, body_json: str) -> None:
        async with self._lock:
            targets = list(self._subs.get(destination, set()))

        if not targets:
            return

        msg = build_frame(
            "MESSAGE",
            headers={"destination": destination, "content-type": "application/json"},
            body=body_json,
        )

        for ws in targets:
            try:
                await ws.send_text(msg)
            except Exception:
                await self.cleanup(ws)


hub = Hub()
