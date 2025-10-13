"""
Script para agregar productos de prueba a una tienda
Ejecutar: python scripts/seed_products.py
"""

import sys
import os

# Agregar la raíz del proyecto al path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.product import Product
from app.models.store import Store
from app.core.config import settings

print("=" * 60)
print("AGREGAR PRODUCTOS DE PRUEBA - QueVendí PRO")
print("=" * 60)

# Conectar a la base de datos
engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
db = SessionLocal()

# Productos típicos de bodega peruana
PRODUCTOS_BODEGA = [
    {
        "name": "Inca Kola 1L",
        "aliases": ["inka", "kola amarilla", "inca cola", "gaseosa amarilla"],
        "category": "Bebidas",
        "cost_price": 2.80,
        "sale_price": 3.50,
        "stock": 24
    },
    {
        "name": "Inca Kola 500ml",
        "aliases": ["inka mediana", "kola chica", "inca cola chica"],
        "category": "Bebidas",
        "cost_price": 1.50,
        "sale_price": 2.00,
        "stock": 36
    },
    {
        "name": "Coca Cola 1L",
        "aliases": ["coca", "cola"],
        "category": "Bebidas",
        "cost_price": 3.00,
        "sale_price": 3.80,
        "stock": 20
    },
    {
        "name": "Leche Gloria Entera 1L",
        "aliases": ["gloria", "leche gloria", "leche entera", "leche"],
        "category": "Lácteos",
        "cost_price": 3.50,
        "sale_price": 4.20,
        "stock": 18
    },
    {
        "name": "Pan Francés",
        "aliases": ["pan"],
        "category": "Panadería",
        "cost_price": 0.20,
        "sale_price": 0.30,
        "stock": 100
    },
    {
        "name": "Azúcar Cartavio 1kg",
        "aliases": ["azucar", "azúcar blanca", "cartavio"],
        "category": "Abarrotes",
        "cost_price": 4.50,
        "sale_price": 5.80,
        "stock": 12
    },
    {
        "name": "Aceite Primor 1L",
        "aliases": ["aceite", "primor"],
        "category": "Abarrotes",
        "cost_price": 8.00,
        "sale_price": 9.50,
        "stock": 15
    },
    {
        "name": "Arroz Costeño 1kg",
        "aliases": ["arroz", "costeño"],
        "category": "Abarrotes",
        "cost_price": 3.20,
        "sale_price": 4.00,
        "stock": 30
    },
    {
        "name": "Sal de Mesa 1kg",
        "aliases": ["sal"],
        "category": "Abarrotes",
        "cost_price": 1.00,
        "sale_price": 1.50,
        "stock": 25
    },
    {
        "name": "Fideo Don Vittorio 1kg",
        "aliases": ["fideo", "fideos", "don vittorio"],
        "category": "Abarrotes",
        "cost_price": 2.50,
        "sale_price": 3.20,
        "stock": 40
    },
    {
        "name": "Galletas Soda Field 6pack",
        "aliases": ["galletas", "soda", "field", "galletas soda"],
        "category": "Snacks",
        "cost_price": 3.50,
        "sale_price": 4.50,
        "stock": 22
    },
    {
        "name": "Atún Florida Entero",
        "aliases": ["atun", "florida"],
        "category": "Conservas",
        "cost_price": 3.00,
        "sale_price": 4.00,
        "stock": 28
    },
    {
        "name": "Papel Higiénico Suave 4un",
        "aliases": ["papel", "papel higienico", "suave"],
        "category": "Limpieza",
        "cost_price": 4.00,
        "sale_price": 5.50,
        "stock": 16
    },
    {
        "name": "Detergente Ariel 1kg",
        "aliases": ["detergente", "ariel", "jabón"],
        "category": "Limpieza",
        "cost_price": 8.50,
        "sale_price": 10.50,
        "stock": 12
    },
    {
        "name": "Cerveza Pilsen 650ml",
        "aliases": ["cerveza", "pilsen", "chela"],
        "category": "Bebidas",
        "cost_price": 3.50,
        "sale_price": 5.00,
        "stock": 24
    }
]

try:
    # Verificar que exista al menos una tienda
    stores = db.query(Store).all()
    
    if not stores:
        print("\n❌ Error: No hay tiendas en la base de datos")
        print("   Primero ejecuta: python scripts/create_first_user.py")
        sys.exit(1)
    
    # Si hay múltiples tiendas, mostrar opciones
    if len(stores) > 1:
        print("\n🏪 Tiendas disponibles:")
        for i, store in enumerate(stores, 1):
            print(f"   {i}. {store.commercial_name} (RUC: {store.ruc})")
        
        choice = int(input("\nSelecciona el número de la tienda: "))
        if choice < 1 or choice > len(stores):
            print("❌ Error: Opción inválida")
            sys.exit(1)
        
        store = stores[choice - 1]
    else:
        store = stores[0]
    
    print(f"\n📦 Agregando productos a: {store.commercial_name}")
    print(f"   Total de productos a agregar: {len(PRODUCTOS_BODEGA)}")
    
    # Verificar si ya hay productos
    existing_products = db.query(Product).filter(Product.store_id == store.id).count()
    if existing_products > 0:
        print(f"\n⚠️  Esta tienda ya tiene {existing_products} productos")
        response = input("¿Deseas agregar más productos de todas formas? (s/n): ")
        if response.lower() != 's':
            print("\n❌ Operación cancelada")
            sys.exit(0)
    
    print("\n" + "-" * 60)
    
    # Crear productos
    added = 0
    skipped = 0
    
    for producto_data in PRODUCTOS_BODEGA:
        # Verificar si el producto ya existe
        existing = db.query(Product).filter(
            Product.store_id == store.id,
            Product.name == producto_data["name"]
        ).first()
        
        if existing:
            print(f"⏭️  {producto_data['name']} - Ya existe, omitiendo...")
            skipped += 1
            continue
        
        # Crear producto
        product = Product(
            store_id=store.id,
            **producto_data
        )
        db.add(product)
        print(f"✅ {producto_data['name']} - S/ {producto_data['sale_price']:.2f} (Stock: {producto_data['stock']})")
        added += 1
    
    db.commit()
    
    print("-" * 60)
    print(f"\n✅ PRODUCTOS AGREGADOS EXITOSAMENTE")
    print(f"   Nuevos: {added}")
    print(f"   Omitidos: {skipped}")
    print(f"   Total en tienda: {db.query(Product).filter(Product.store_id == store.id).count()}")
    
    print("\n💡 Ahora puedes:")
    print("   1. Iniciar el servidor: uvicorn app.main:app --reload")
    print("   2. Acceder a: http://localhost:8000")
    print("   3. Probar venta por voz: 'vender dos inca kola'")
    print("=" * 60)

except Exception as e:
    db.rollback()
    print(f"\n❌ Error al agregar productos: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
finally:
    db.close()