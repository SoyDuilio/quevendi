"""
Endpoints de autenticación para QueVendí
"""

from fastapi import APIRouter, Depends, HTTPException, status, Response, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.user import Token, UserResponse
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """
    Mostrar página de login
    """
    return templates.TemplateResponse("login.html", {"request": request})


@router.post("/login")
async def login(
    request: Request,
    response: Response,
    dni: str = Form(...),
    pin: str = Form(...),
    db: Session = Depends(get_db)
):
    """
    Procesar login y crear sesión
    
    Args:
        dni: DNI del usuario (8 dígitos)
        pin: PIN del usuario (4 dígitos)
        db: Sesión de base de datos
    
    Returns:
        Redirección a /home o error
    """
    # Validar formato
    if len(dni) != 8 or not dni.isdigit():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="DNI debe tener 8 dígitos"
        )
    
    if len(pin) != 4 or not pin.isdigit():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="PIN debe tener 4 dígitos"
        )
    
    # Autenticar usuario
    auth_service = AuthService(db)
    user = auth_service.authenticate_user(dni, pin)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="DNI o PIN incorrectos"
        )
    
    # Crear token
    access_token = auth_service.create_access_token_for_user(user)
    
    # Guardar token en cookie
    response = RedirectResponse(url="/home", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(
        key="access_token",
        value=f"Bearer {access_token}",
        httponly=True,
        max_age=60 * 60 * 24 * 7,  # 7 días
        samesite="lax"
    )
    
    return response


@router.post("/logout")
async def logout(response: Response):
    """
    Cerrar sesión eliminando cookie
    """
    response = RedirectResponse(url="/auth/login", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie("access_token")
    return response


@router.get("/logout")
async def logout_get(response: Response):
    """
    Cerrar sesión vía GET (para enlaces)
    """
    response = RedirectResponse(url="/auth/login", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie("access_token")
    return response