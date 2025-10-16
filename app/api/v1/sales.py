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

from fastapi.responses import HTMLResponse

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
    Soporta: ventas, agregar, cambiar, cancelar, confirmar, quitar
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
    
    # ========================================
    # COMANDO: REMOVE (quitar producto)
    # ========================================
    if parsed['type'] == 'remove':
        product_service = ProductService(db)
        products = product_service.get_products_by_store(current_user.store_id)
        
        # Limpiar opciones ambiguas previas
        VoiceService._last_ambiguous_options = []
        
        product = VoiceService.find_product_fuzzy(parsed['product_query'], products)
        
        # Verificar ambigüedad
        if product is None and VoiceService._last_ambiguous_options:
            return {
                "type": "ambiguous_remove",
                "product_query": parsed['product_query'],
                "options": [
                    {
                        "id": p.id,
                        "name": p.name,
                        "price": p.sale_price
                    }
                    for p in VoiceService._last_ambiguous_options
                ],
                "message": f"¿Cuál {parsed['product_query']} quieres eliminar?"
            }
        
        if not product:
            raise HTTPException(
                status_code=404,
                detail=f"No se encontró: {parsed['product_query']}"
            )
        
        return {
            "type": "remove",
            "product": {
                "id": product.id,
                "name": product.name
            },
            "message": f"Eliminar {product.name} del carrito"
        }
    
    # ========================================
    # COMANDO: CHANGE_PRICE (cambiar precio)
    # ========================================
    if parsed['type'] == 'change_price':
        product_service = ProductService(db)
        products = product_service.get_products_by_store(current_user.store_id)
        
        # Limpiar opciones ambiguas previas
        VoiceService._last_ambiguous_options = []
        
        # Buscar el producto para verificar que existe
        product = VoiceService.find_product_fuzzy(parsed['product_query'], products)
        
        # Verificar ambigüedad
        if product is None and VoiceService._last_ambiguous_options:
            return {
                "type": "ambiguous_price",
                "product_query": parsed['product_query'],
                "new_price": parsed['new_price'],
                "options": [
                    {
                        "id": p.id,
                        "name": p.name,
                        "price": p.sale_price
                    }
                    for p in VoiceService._last_ambiguous_options
                ],
                "message": f"¿A cuál {parsed['product_query']} cambiar el precio?"
            }
        
        if not product:
            raise HTTPException(
                status_code=404,
                detail=f"No se encontró: {parsed['product_query']}"
            )
        
        return {
            "type": "change_price",
            "product": {
                "id": product.id,
                "name": product.name,
                "current_price": product.sale_price
            },
            "new_price": parsed['new_price']
        }
    
    # ========================================
    # COMANDO: CHANGE_PRODUCT (cambiar X por Y)
    # ========================================
    if parsed['type'] == 'change_product':
        product_service = ProductService(db)
        products = product_service.get_products_by_store(current_user.store_id)
        
        # Buscar producto viejo
        VoiceService._last_ambiguous_options = []
        old_product = VoiceService.find_product_fuzzy(parsed['old_product'], products)
        
        if old_product is None and VoiceService._last_ambiguous_options:
            return {
                "type": "ambiguous_change_old",
                "old_product_query": parsed['old_product'],
                "new_product_query": parsed['new_product'],
                "options": [
                    {
                        "id": p.id,
                        "name": p.name,
                        "price": p.sale_price
                    }
                    for p in VoiceService._last_ambiguous_options
                ],
                "message": f"¿Cuál {parsed['old_product']} quieres cambiar?"
            }
        
        if not old_product:
            raise HTTPException(404, detail=f"No se encontró: {parsed['old_product']}")
        
        # Buscar producto nuevo
        VoiceService._last_ambiguous_options = []
        new_product = VoiceService.find_product_fuzzy(parsed['new_product'], products)
        
        if new_product is None and VoiceService._last_ambiguous_options:
            return {
                "type": "ambiguous_change_new",
                "old_product": {
                    "id": old_product.id,
                    "name": old_product.name
                },
                "new_product_query": parsed['new_product'],
                "options": [
                    {
                        "id": p.id,
                        "name": p.name,
                        "price": p.sale_price
                    }
                    for p in VoiceService._last_ambiguous_options
                ],
                "message": f"¿Por cuál {parsed['new_product']} cambiar?"
            }
        
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
    
    # ========================================
    # COMANDO: SALE / ADD (venta o agregar)
    # ========================================
    product_service = ProductService(db)
    products = product_service.get_products_by_store(current_user.store_id)
    
    cart_items = []
    not_found = []
    ambiguous_items = []  # ✅ NUEVO: Lista de items ambiguos
    
    for item in parsed['items']:
        # Limpiar opciones ambiguas previas antes de cada búsqueda
        VoiceService._last_ambiguous_options = []
        
        product = VoiceService.find_product_fuzzy(item['product_query'], products)
        
        # ✅ NUEVO: Verificar si hay ambigüedad
        if product is None and VoiceService._last_ambiguous_options:
            ambiguous_items.append({
                'query': item['product_query'],
                'quantity': item['quantity'],
                'options': [
                    {
                        'id': p.id,
                        'name': p.name,
                        'price': p.sale_price,
                        'stock': p.stock
                    }
                    for p in VoiceService._last_ambiguous_options
                ]
            })
            continue
        
        if not product:
            not_found.append(item['product_query'])
            continue
        
        # Verificar stock
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
    
    # ✅ NUEVO: Si hay items ambiguos, devolver para que el usuario elija
    if ambiguous_items:
        return {
            "type": "ambiguous",
            "ambiguous_items": ambiguous_items,
            "found_items": cart_items,  # Items que sí se encontraron
            "message": "Hay varios productos que coinciden. ¿Cuál quieres?"
        }
    
    # Si no se encontró nada
    if not cart_items:
        raise HTTPException(
            status_code=404,
            detail=f"No se encontraron: {', '.join(not_found)}"
        )
    
    # Respuesta exitosa
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

"""
Endpoints de ventas para QueVendí
AGREGAR estos nuevos endpoints HTML al archivo sales.py existente
"""

@router.get("/today/html", response_class=HTMLResponse)
async def get_today_sales_html(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Ventas del día en formato HTML para HTMX
    """
    sale_service = SaleService(db)
    sales = sale_service.get_sales_by_date(current_user.store_id)
    
    # ✅ SI NO HAY VENTAS: Devolver empty state
    if not sales or len(sales) == 0:
        return HTMLResponse(content="""
            <div class="empty-state">
                <div class="empty-icon">📭</div>
                <div class="empty-title">No hay ventas hoy</div>
                <div class="empty-subtitle">Las ventas aparecerán aquí automáticamente</div>
            </div>
        """)
    
    # ✅ SI HAY VENTAS: Generar HTML de cada venta
    html_items = []
    for sale in sales:
        # Obtener items de la venta
        items_text = ", ".join([
            f"{item.quantity}x {item.product.name}" 
            for item in sale.items
        ])
        
        # Emoji según método de pago
        payment_emoji = {
            'efectivo': '💵',
            'yape': '💳',
            'plin': '📱'
        }.get(sale.payment_method, '💰')
        
        # Formatear hora
        time_str = sale.created_at.strftime('%H:%M')
        
        # Generar HTML de la venta
        html_items.append(f"""
            <div class="sale-card">
                <div class="sale-header">
                    <span class="sale-time">{time_str}</span>
                    <span class="sale-payment">{payment_emoji}</span>
                    <span class="sale-total">S/. {sale.total:.2f}</span>
                </div>
                <div class="sale-items">{items_text}</div>
            </div>
        """)
    
    return HTMLResponse(content="\n".join(html_items))


@router.get("/today/total/html", response_class=HTMLResponse)
async def get_today_total_html(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Resumen del día en formato HTML para HTMX
    """
    sale_service = SaleService(db)
    sales = sale_service.get_sales_by_date(current_user.store_id)
    
    count = len(sales)
    total = sum(sale.total for sale in sales) if sales else 0.0
    
    return HTMLResponse(content=f"""
        <div class="summary-item">
            <div class="summary-label">Ventas</div>
            <div class="summary-value">{count}</div>
        </div>
        <div class="summary-divider"></div>
        <div class="summary-item">
            <div class="summary-label">Total</div>
            <div class="summary-value">S/. {total:.2f}</div>
        </div>
    """)