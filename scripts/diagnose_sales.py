"""
Script de diagnóstico para identificar problemas en ventas
Ejecutar: python scripts/diagnose_sales.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
from app.models.sale import Sale, SaleItem
from app.models.product import Product
from app.core.config import settings
from datetime import datetime

print("=" * 70)
print("DIAGNÓSTICO DE VENTAS - QueVendí PRO")
print("=" * 70)

engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
db = SessionLocal()

try:
    # 1. Contar ventas totales
    total_sales = db.query(Sale).count()
    print(f"\n📊 Total de ventas en la base de datos: {total_sales}")
    
    if total_sales == 0:
        print("\n⚠️  No hay ventas registradas")
        sys.exit(0)
    
    # 2. Análisis detallado de cada venta
    print("\n" + "─" * 70)
    print("ANÁLISIS DETALLADO DE VENTAS")
    print("─" * 70)
    
    sales = db.query(Sale).order_by(Sale.created_at.desc()).limit(10).all()
    
    for sale in sales:
        print(f"\n🧾 Venta ID: {sale.id}")
        print(f"   Fecha: {sale.sale_date}")
        print(f"   Total guardado: S/ {sale.total:.2f}")
        print(f"   Usuario: {sale.user.full_name}")
        print(f"   Método pago: {sale.payment_method}")
        
        # Calcular total de items
        items_total = sum(item.subtotal for item in sale.items)
        print(f"   Suma de items: S/ {items_total:.2f}")
        
        # Verificar discrepancia
        if abs(sale.total - items_total) > 0.01:
            print(f"   ⚠️  DISCREPANCIA: {sale.total:.2f} ≠ {items_total:.2f}")
        else:
            print(f"   ✓ Totales coinciden")
        
        # Listar items
        print(f"   Items ({len(sale.items)}):")
        for item in sale.items:
            print(f"      - {item.quantity}x {item.product.name} = S/ {item.subtotal:.2f}")
    
    # 3. Verificar duplicados
    print("\n" + "─" * 70)
    print("VERIFICACIÓN DE DUPLICADOS")
    print("─" * 70)
    
    duplicates = db.query(
        Sale.user_id,
        Sale.total,
        Sale.sale_date,
        func.count(Sale.id).label('count')
    ).group_by(
        Sale.user_id,
        Sale.total,
        Sale.sale_date
    ).having(
        func.count(Sale.id) > 1
    ).all()
    
    if duplicates:
        print(f"\n⚠️  Se encontraron {len(duplicates)} grupos de ventas duplicadas:")
        for dup in duplicates:
            print(f"   - Usuario {dup.user_id}, Total S/ {dup.total}, {dup.count} veces")
    else:
        print("\n✓ No se encontraron ventas duplicadas")
    
    # 4. Verificar items huérfanos
    print("\n" + "─" * 70)
    print("VERIFICACIÓN DE ITEMS HUÉRFANOS")
    print("─" * 70)
    
    orphan_items = db.query(SaleItem).filter(
        ~SaleItem.sale_id.in_(db.query(Sale.id))
    ).count()
    
    if orphan_items > 0:
        print(f"\n⚠️  Se encontraron {orphan_items} items sin venta asociada")
    else:
        print("\n✓ No hay items huérfanos")
    
    # 5. Resumen por día
    print("\n" + "─" * 70)
    print("RESUMEN POR DÍA")
    print("─" * 70)
    
    from sqlalchemy import func, cast, Date
    
    daily_summary = db.query(
        cast(Sale.sale_date, Date).label('date'),
        func.count(Sale.id).label('count'),
        func.sum(Sale.total).label('total')
    ).group_by(
        cast(Sale.sale_date, Date)
    ).order_by(
        cast(Sale.sale_date, Date).desc()
    ).limit(7).all()
    
    print("\nÚltimos 7 días:")
    for day in daily_summary:
        print(f"   {day.date}: {day.count} ventas = S/ {day.total:.2f}")
    
    # 6. Verificar timezone
    print("\n" + "─" * 70)
    print("VERIFICACIÓN DE TIMEZONE")
    print("─" * 70)
    
    print(f"\nFecha/hora actual del sistema: {datetime.now()}")
    
    latest_sale = db.query(Sale).order_by(Sale.created_at.desc()).first()
    if latest_sale:
        print(f"Última venta registrada:")
        print(f"   sale_date: {latest_sale.sale_date}")
        print(f"   created_at: {latest_sale.created_at}")
        
        diff = datetime.now() - latest_sale.created_at.replace(tzinfo=None)
        print(f"   Diferencia con ahora: {diff}")
    
    print("\n" + "=" * 70)
    print("✓ DIAGNÓSTICO COMPLETADO")
    print("=" * 70)
    
except Exception as e:
    print(f"\n❌ Error durante el diagnóstico: {e}")
    import traceback
    traceback.print_exc()
finally:
    db.close()