import os
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "AI Trading Copilot"
    API_V1_STR: str = "/api/v1"
    
    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        "postgresql://postgres:postgres@localhost:5432/postgres"
    )
    
    # Security & Auth
    SUPABASE_JWT_SECRET: str = os.getenv("SUPABASE_JWT_SECRET", "super-secret-supabase-jwt-token-key-must-be-long-and-secure")
    JWT_ALGORITHM: str = "HS256"
    
    # External services API
    AI_SERVICE_URL: str = os.getenv("AI_SERVICE_URL", "http://localhost:8001")
    FORECAST_SERVICE_URL: str = os.getenv("FORECAST_SERVICE_URL", "http://localhost:8002")
    
    # Binance Websocket url
    BINANCE_WS_URL: str = "wss://stream.binance.com:9443/ws"
    
    # CORS Origins
    BACKEND_CORS_ORIGINS: List[str] = ["*"]
    
    model_config = SettingsConfigDict(case_sensitive=True)

settings = Settings()
