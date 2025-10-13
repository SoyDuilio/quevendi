from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str
    
    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 10080  # 7 días
    
    # Google Cloud TTS (AGREGAR ESTOS)
    GOOGLE_APPLICATION_CREDENTIALS: Optional[str] = None
    GOOGLE_TTS_API_KEY: Optional[str] = None
    
    # Configuración de voz (AGREGAR ESTOS)
    TTS_LANGUAGE: str = "es-PE"
    TTS_DEFAULT_VOICE: str = "es-PE-Standard-A"
    TTS_SPEED: float = 1.0
    
    # Alertas (AGREGAR ESTOS)
    ALERT_IDLE_TIME: int = 180
    ALERT_SLOW_SALES_THRESHOLD: int = 5
    ALERT_SLOW_SALES_HOURS: int = 2
    
    class Config:
        env_file = ".env"
        extra = "allow"  # AGREGAR ESTO si no existe

settings = Settings()