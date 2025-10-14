# app/main.py
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
from contextlib import asynccontextmanager
from app.core.config import settings
from app.api.v1 import auth, sales, products, voice
import os

# ========================================
# CONFIGURAR TEMPLATES CON RUTA ABSOLUTA
# ========================================
BASE_DIR = Path(__file__).resolve().parent.parent  # C:\QUEVENDI
TEMPLATES_DIR = BASE_DIR / "app" / "templates"  # ⬅️ Agregamos /app/
STATIC_DIR = BASE_DIR / "static"

print(f"📂 BASE_DIR: {BASE_DIR}")
print(f"📂 TEMPLATES_DIR: {TEMPLATES_DIR}")
print(f"📂 STATIC_DIR: {STATIC_DIR}")

# Verificar que templates existe
if not TEMPLATES_DIR.exists():
    print(f"⚠️ ERROR: No se encuentra el directorio templates en {TEMPLATES_DIR}")
    print(f"   Asegúrate de que la estructura sea:")
    print(f"   {BASE_DIR}/")
    print(f"   ├── app/")
    print(f"   ├── templates/")
    print(f"   └── static/")
else:
    print(f"✅ Templates encontrado")
    # Listar archivos en templates
    template_files = list(TEMPLATES_DIR.glob("*.html"))
    print(f"   Archivos: {[f.name for f in template_files]}")

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# ========================================
# LIFESPAN EVENT
# ========================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    # ========== STARTUP ==========
    print("\n" + "="*60)
    print("🚀 SERVIDOR INICIADO")
    print("="*60)
    
    # Listar todas las rutas registradas
    print("\n📍 RUTAS REGISTRADAS:")
    print("-"*60)
    
    routes_by_type = {"HTML": [], "API": [], "STATIC": [], "OTHER": []}
    
    for route in app.routes:
        if hasattr(route, 'methods') and hasattr(route, 'path'):
            methods = ', '.join(sorted(route.methods))
            path = route.path
            
            # Clasificar rutas
            if path.startswith('/api/'):
                routes_by_type["API"].append(f"  {methods:12} {path}")
            elif path.startswith('/static'):
                routes_by_type["STATIC"].append(f"  {methods:12} {path}")
            elif any(x in path for x in ['/auth/', '/home', '/products', '/']):
                routes_by_type["HTML"].append(f"  {methods:12} {path}")
            else:
                routes_by_type["OTHER"].append(f"  {methods:12} {path}")
    
    # Mostrar rutas organizadas
    if routes_by_type["HTML"]:
        print("\n📄 RUTAS HTML (Templates):")
        for route in sorted(routes_by_type["HTML"]):
            print(route)
    
    if routes_by_type["API"]:
        print("\n🔌 RUTAS API:")
        for route in sorted(routes_by_type["API"]):
            print(route)
    
    if routes_by_type["STATIC"]:
        print("\n📁 RUTAS ESTÁTICAS:")
        for route in routes_by_type["STATIC"]:
            print(route)
    
    if routes_by_type["OTHER"]:
        print("\n🔧 OTRAS RUTAS:")
        for route in sorted(routes_by_type["OTHER"]):
            print(route)
    
    print("\n" + "="*60)
    print(f"✅ Servidor listo en: http://0.0.0.0:{os.getenv('PORT', '8080')}")
    print("="*60 + "\n")
    
    yield
    
    # ========== SHUTDOWN ==========
    print("\n👋 Servidor detenido")

# ========================================
# CREAR APP
# ========================================
app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    lifespan=lifespan
)

# ========================================
# CORS
# ========================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ========================================
# ARCHIVOS ESTÁTICOS - MONTAR PRIMERO
# ========================================
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
    print(f"📁 Archivos estáticos montados: {STATIC_DIR}")
else:
    print(f"⚠️ Directorio static/ no encontrado en: {STATIC_DIR}")

# ========================================
# ROUTERS API - CON PREFIX /api
# ========================================
app.include_router(auth.router, prefix="/api")
app.include_router(products.router, prefix="/api")
app.include_router(sales.router, prefix="/api")
app.include_router(voice.router, prefix="/api")

# ========================================
# RUTAS DE TEMPLATES (HTML)
# ========================================
@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Redirigir a login"""
    return RedirectResponse(url="/auth/login")

@app.get("/auth/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Página de login"""
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/home", response_class=HTMLResponse)
async def home_page(request: Request):
    """Página principal"""
    return templates.TemplateResponse("home.html", {"request": request})

@app.get("/products", response_class=HTMLResponse)
async def products_page(request: Request):
    """Página de productos"""
    return templates.TemplateResponse("products.html", {"request": request})

# ========================================
# HEALTH CHECK
# ========================================
@app.get("/health")
async def health():
    """Health check para Railway"""
    return {"status": "healthy"}