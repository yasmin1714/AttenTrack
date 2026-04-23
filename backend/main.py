from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import asyncio

from routes import attention, student, parent, admin
from frame_processor import router as frame_router
from websocket_manager import ConnectionManager
from auth import router as auth_router

app = FastAPI()

# WebSocket Manager
manager = ConnectionManager()

@app.on_event("startup")
async def startup():
    app.state.manager = manager

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth_router)       # /api/auth/...
app.include_router(attention.router)
app.include_router(student.router)
app.include_router(parent.router)
app.include_router(admin.router)
app.include_router(frame_router)      # /api/process-frame

# WebSocket
@app.websocket("/ws/{student_id}")
async def websocket_endpoint(websocket: WebSocket, student_id: str):
    await manager.connect(student_id, websocket)
    try:
        while True:
            await asyncio.sleep(30)
    except WebSocketDisconnect:
        manager.disconnect(student_id, websocket)

@app.get("/")
def home():
    return {"status": "AttenTrack Backend Running"}
