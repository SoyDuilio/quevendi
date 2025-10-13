"""
Endpoints de ventas para QueVendí
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.sale import SaleCreate, SaleResponse
from app.services.sale_service import SaleService
from app.services.voice_service import VoiceService
from app.services.product_service import ProductService
from app.api.dependencies import get_current_user
from app.models.user import User
from typing import List
from datetime import datetime
from pydantic import BaseModel

router = APIRouter(prefix="/sales", tags=["sales"])

class VoiceCommandRequest(BaseModel):
    """Comando de voz"""
    text: str

@router.post("/voice/parse")
async def parse_voice_command(
    command: VoiceCommandRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Parsear comando de voz y procesar acción
    Soporta: ventas, agregar, cambiar, cancelar, confirmar
    """
    parsed = VoiceService.parse_command(command.text)
    
    if not parsed:
        raise HTTPException(
            status_code=400,
            detail="No se pudo entender el comando"
        )
    
    # Comandos simples
    if parsed['type'] in ['cancel', 'confirm']:
        return {
            "type": parsed['type'],
            "message": "Comando recibido"
        }
    
    # Cambio de precio
    if parsed['type'] == 'change_price':
        return {
            "type": "change_price",
            "product_query": parsed['product_query'],
            "new_price": parsed['new_price']
        }
    
    # Cambio de producto
    if parsed['type'] == 'change_product':
        product_service = ProductService(db)
        products = product_service.get_products_by_store(current_user.store_id)
        
        # Buscar ambos productos
        old_product = VoiceService.find_product_fuzzy(parsed['old_product'], products)
        new_product = VoiceService.find_product_fuzzy(parsed['new_product'], products)
        
        if not old_product:
            raise HTTPException(404, detail=f"No se encontró: {parsed['old_product']}")
        if not new_product:
            raise HTTPException(404, detail=f"No se encontró: {parsed['new_product']}")
        
        return {
            "type": "change_product",
            "old_product": {
                "id": old_product.id,
                "name": old_product.name
            },
            "new_product": {
                "id": new_product.id,
                "name": new_product.name,
                "price": new_product.sale_price
            }
        }
    
    # Venta o agregar productos
    product_service = ProductService(db)
    products = product_service.get_products_by_store(current_user.store_id)
    
    cart_items = []
    not_found = []
    
    for item in parsed['items']:
        product = VoiceService.find_product_fuzzy(item['product_query'], products)
        
        if not product:
            not_found.append(item['product_query'])
            continue
        
        if product.stock < item['quantity']:
            raise HTTPException(
                status_code=400,
                detail=f"{product.name}: Stock insuficiente. Solo hay {product.stock}"
            )
        
        subtotal = product.sale_price * item['quantity']
        unit = getattr(product, 'unit', 'unidad')
        
        cart_items.append({
            "product": {
                "id": product.id,
                "name": product.name,
                "price": product.sale_price,
                "stock": product.stock,
                "category": product.category,
                "unit": unit
            },
            "quantity": item['quantity'],
            "subtotal": subtotal
        })
    
    if not cart_items:
        raise HTTPException(
            status_code=404,
            detail=f"No se encontraron: {', '.join(not_found)}"
        )
    
    response = {
        "type": parsed['type'],
        "items": cart_items,
        "total": sum(item['subtotal'] for item in cart_items)
    }
    
    if not_found:
        response["warning"] = f"No se encontraron: {', '.join(not_found)}"
    
    return response

@router.post("/", response_model=SaleResponse)
async def create_sale(
    sale_data: SaleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Crear venta"""
    sale_service = SaleService(db)
    sale = sale_service.create_sale(sale_data, current_user.id, current_user.store_id)
    return sale_service.to_response(sale)

@router.get("/today", response_model=List[SaleResponse])
async def get_today_sales(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Ventas del día"""
    sale_service = SaleService(db)
    sales = sale_service.get_sales_by_date(current_user.store_id)
    return [sale_service.to_response(sale) for sale in sales]

@router.get("/today/total")
async def get_today_total(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Total del día"""
    sale_service = SaleService(db)
    sales = sale_service.get_sales_by_date(current_user.store_id)
    
    total = sum(sale.total for sale in sales)
    
    return {
        "total": round(total, 2),
        "count": len(sales),
        "date": datetime.now().date().isoformat()
    }

@router.get("/stats/today")
async def get_today_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Estadísticas del día para alertas"""
    sale_service = SaleService(db)
    product_service = ProductService(db)
    
    sales = sale_service.get_sales_by_date(current_user.store_id)
    products = product_service.get_products_by_store(current_user.store_id)
    
    # Productos agotados o cerca
    low_stock = []
    for p in products:
        if p.stock == 0:
            low_stock.append({"name": p.name, "stock": 0})
        elif p.min_stock_alert and p.stock <= p.min_stock_alert:
            low_stock.append({"name": p.name, "stock": p.stock})
    
    return {
        "sales_count": len(sales),
        "total": sum(s.total for s in sales),
        "low_stock": low_stock,
        "last_sale": sales[0].created_at if sales else None
    }