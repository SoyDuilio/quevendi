from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1 import auth, sales, products, voice
from app.api.dependencies import get_current_user
from app.core.database import get_db
from sqlalchemy.orm import Session
from fastapi import Depends

app = FastAPI(
    title="QueVendí PRO",
    description="Sistema de ventas por voz para bodegas",
    version="0.1.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates
templates = Jinja2Templates(directory="app/templates")

# Routers
app.include_router(auth.router)
app.include_router(sales.router)
app.include_router(voice.router, prefix="/api/v1")
app.include_router(products.router)

# Root redirect
@app.get("/")
async def root():
    return RedirectResponse(url="/home")

# Home page
@app.get("/home", response_class=HTMLResponse)
async def home(
    request: Request,
    db: Session = Depends(get_db)
):
    try:
        current_user = await get_current_user(request, db)
        return templates.TemplateResponse(
            "home.html",
            {
                "request": request,
                "user": current_user,
                "store": current_user.store
            }
        )
    except:
        return RedirectResponse(url="/auth/login")

# Health check
@app.get("/health")
async def health():
    return {"status": "ok"}

"""
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)"""