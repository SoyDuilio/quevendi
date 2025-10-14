# app/core/database.py
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# ========================================
# CONVERTIR URL PARA PSYCOPG3
# ========================================
# Railway usa: postgresql://user:pass@host/db
# Necesitamos: postgresql+psycopg://user:pass@host/db

database_url = settings.DATABASE_URL

# Convertir automáticamente para usar psycopg (v3)
if database_url.startswith("postgresql://"):
    database_url = database_url.replace("postgresql://", "postgresql+psycopg://", 1)
elif database_url.startswith("postgres://"):
    # Railway a veces usa "postgres://" en lugar de "postgresql://"
    database_url = database_url.replace("postgres://", "postgresql+psycopg://", 1)

print(f"🔌 Conectando a base de datos...")
print(f"📡 URL (sanitizada): {database_url.split('@')[0]}@***")

# ========================================
# CREAR ENGINE
# ========================================
engine = create_engine(
    database_url,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,  # Verificar conexiones antes de usarlas
    echo=False  # Cambiar a True para debug SQL
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# ========================================
# DEPENDENCY PARA FASTAPI
# ========================================
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()