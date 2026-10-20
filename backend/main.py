import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from backend.app.core.config import settings
from backend.app.api.endpoints import router as api_router
from backend.app.services.binance_ws import binance_ws_manager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize background connection to Binance WebSocket
    await binance_ws_manager.start()
    # Startup AI engine in background
    try:
        import threading
        from ai.app import load_qwen_model
        threading.Thread(target=load_qwen_model, daemon=True).start()
    except Exception as e:
        print(f"AI engine background loader note: {e}")
    yield
    # Shutdown: Clean up background tasks
    await binance_ws_manager.stop()

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan
)

# CORS configuration
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Register REST endpoints
app.include_router(api_router, prefix=settings.API_V1_STR)

# Register AI Analysis & History endpoints (/analyze, /history)
try:
    from ai.app import app as ai_app
    app.include_router(ai_app.router, tags=["AI Engine"])
except Exception as e:
    print(f"Warning: Could not include AI app router: {e}")

@app.get("/")
def read_root():
    return {"message": "AI Trading Copilot API is running."}

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "AI Trading Copilot Gateway"}

# WebSocket Endpoint for streaming ticks and alerts to UI Client
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await binance_ws_manager.connect_client(websocket)
    try:
        while True:
            # Keep connection alive; receive (and discard) any client messages
            await websocket.receive_text()
    except WebSocketDisconnect:
        binance_ws_manager.disconnect_client(websocket)
    except Exception as e:
        print(f"Error on Client websocket: {str(e)}")
        binance_ws_manager.disconnect_client(websocket)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
