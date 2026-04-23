from fastapi import WebSocket
from typing import Dict, List

class ConnectionManager:
    def __init__(self):
        # multiple connections per student
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, student_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.setdefault(student_id, []).append(websocket)
        print(f"[WS] {student_id} connected")

    def disconnect(self, student_id: str, websocket: WebSocket):
        if student_id in self.active_connections:
            if websocket in self.active_connections[student_id]:
                self.active_connections[student_id].remove(websocket)

            if not self.active_connections[student_id]:
                del self.active_connections[student_id]

        print(f"[WS] {student_id} disconnected")

    async def push(self, student_id: str, data: dict):
        connections = self.active_connections.get(student_id, [])
        for ws in connections:
            try:
                await ws.send_json(data)
            except:
                self.disconnect(student_id, ws)

    async def broadcast(self, data: dict):
        for student_id in list(self.active_connections.keys()):
            await self.push(student_id, data)