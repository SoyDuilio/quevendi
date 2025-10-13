"""
Dependencies para la API de QueVendí
Contiene funciones reutilizables para endpoints
"""

from fastapi import Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.auth_service import AuthService
from app.models.user import User


async def get_current_user(
    request: Request,
    db: Session = Depends(get_db)
) -> User:
    """
    Obtener el usuario actual desde el token en la cookie
    
    Args:
        request: Request de FastAPI
        db: Sesión de base de datos
    
    Returns:
        Usuario autenticado
    
    Raises:
        HTTPException: Si no hay token o es inválido
    """
    # Obtener token de la cookie
    token = request.cookies.get("access_token")
    
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No autenticado. Por favor inicia sesión.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Remover "Bearer " si existe
    if token.startswith("Bearer "):
        token = token.replace("Bearer ", "")
    
    # Verificar token
    auth_service = AuthService(db)
    user = auth_service.get_current_user(token)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado. Por favor inicia sesión nuevamente.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario inactivo. Contacta al administrador.",
        )
    
    return user


def get_current_active_owner(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Verificar que el usuario actual es dueño (owner)
    
    Args:
        current_user: Usuario actual
    
    Returns:
        Usuario si es owner
    
    Raises:
        HTTPException: Si el usuario no es owner
    """
    if current_user.role != "owner":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso denegado. Solo el dueño puede realizar esta acción."
        )
    return current_user


def check_permission(permission: str):
    """
    Decorator para verificar permisos específicos
    
    Args:
        permission: Nombre del permiso a verificar
    
    Returns:
        Función de dependencia
    """
    def permission_checker(current_user: User = Depends(get_current_user)) -> User:
        # Owners tienen todos los permisos
        if current_user.role == "owner":
            return current_user
        
        # Verificar permiso específico
        if permission == "register_purchases":
            if not current_user.can_register_purchases:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="No tienes permiso para registrar compras."
                )
        
        elif permission == "view_analytics":
            if not current_user.can_view_analytics:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="No tienes permiso para ver reportes y analíticas."
                )
        
        return current_user
    
    return permission_checker