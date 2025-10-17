# app/core/database.py
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# ========================================
# DETECTAR QUÉ DRIVER USAR
# ========================================
database_url = settings.DATABASE_URL

# Intentar detectar qué driver de PostgreSQL está disponible
try:
    import psycopg  # psycopg3
    # Si tenemos psycopg3, convertir URL
    if database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+psycopg://", 1)
    elif database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql+psycopg://", 1)
    print("🔌 Usando psycopg3 (moderno)")
    
except ImportError:
    # Si no tiene psycopg3, usar psycopg2 (local)
    try:
        import psycopg2  # psycopg2
        # Normalizar URL para psycopg2
        if database_url.startswith("postgres://"):
            database_url = database_url.replace("postgres://", "postgresql://", 1)
        print("🔌 Usando psycopg2 (legacy)")
        
    except ImportError:
        print("❌ ERROR: No se encontró ningún driver de PostgreSQL")
        print("   Instala uno de estos:")
        print("   - pip install psycopg[binary]  (recomendado)")
        print("   - pip install psycopg2-binary")
        raise

print(f"📡 Conectando a: {database_url.split('@')[0]}@***")

# ========================================
# CREAR ENGINE
# ========================================
# Forzar uso de psycopg2 en lugar de psycopg3
if database_url and database_url.startswith("postgresql://"):
    database_url = database_url.replace("postgresql://", "postgresql+psycopg2://", 1)


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
