"""
Script para crear el primer usuario y tienda en QueVendí
Ejecutar: python scripts/create_first_user.py
"""

import sys
import os

# Agregar la raíz del proyecto al path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.user import User
from app.models.store import Store
from app.core.security import get_pin_hash
from app.core.config import settings

print("=" * 60)
print("CREAR PRIMER USUARIO Y TIENDA - QueVendí PRO")
print("=" * 60)

# Conectar a la base de datos
engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
db = SessionLocal()

try:
    # Verificar si ya existe una tienda
    existing_store = db.query(Store).first()
    if existing_store:
        print("\n⚠️  Ya existe una tienda en la base de datos:")
        print(f"   Nombre: {existing_store.commercial_name}")
        print(f"   RUC: {existing_store.ruc}")
        
        response = input("\n¿Deseas crear otra tienda? (s/n): ")
        if response.lower() != 's':
            print("\n❌ Operación cancelada")
            sys.exit(0)
    
    print("\n📝 Ingresa los datos de la tienda:")
    
    # Datos de la tienda
    ruc = input("RUC (11 dígitos): ").strip()
    if len(ruc) != 11 or not ruc.isdigit():
        print("❌ Error: RUC debe tener 11 dígitos")
        sys.exit(1)
    
    business_name = input("Razón Social: ").strip()
    commercial_name = input("Nombre Comercial: ").strip()
    address = input("Dirección: ").strip()
    
    # Crear tienda
    store = Store(
        ruc=ruc,
        business_name=business_name,
        commercial_name=commercial_name,
        address=address,
        plan="freemium"
    )
    db.add(store)
    db.flush()  # Para obtener el ID de la tienda
    
    print(f"\n✅ Tienda creada: {commercial_name}")
    print(f"   ID: {store.id}")
    
    # Datos del usuario
    print("\n📝 Ingresa los datos del usuario dueño:")
    
    dni = input("DNI (8 dígitos): ").strip()
    if len(dni) != 8 or not dni.isdigit():
        print("❌ Error: DNI debe tener 8 dígitos")
        sys.exit(1)
    
    # Verificar si el DNI ya existe
    existing_user = db.query(User).filter(User.dni == dni).first()
    if existing_user:
        print(f"❌ Error: Ya existe un usuario con DNI {dni}")
        sys.exit(1)
    
    pin = input("PIN (4 dígitos): ").strip()
    if len(pin) != 4 or not pin.isdigit():
        print("❌ Error: PIN debe tener 4 dígitos")
        sys.exit(1)
    
    full_name = input("Nombre completo: ").strip()
    phone = input("Teléfono (opcional): ").strip()
    
    # Crear usuario
    user = User(
        dni=dni,
        pin_hash=get_pin_hash(pin),
        full_name=full_name,
        phone=phone if phone else None,
        store_id=store.id,
        role="owner",
        can_register_purchases=True,
        can_view_analytics=True
    )
    db.add(user)
    db.commit()
    
    print("\n" + "=" * 60)
    print("✅ USUARIO CREADO EXITOSAMENTE")
    print("=" * 60)
    print(f"\n🏪 TIENDA:")
    print(f"   Nombre: {store.commercial_name}")
    print(f"   RUC: {store.ruc}")
    print(f"   Dirección: {store.address}")
    print(f"   Plan: {store.plan}")
    
    print(f"\n👤 USUARIO:")
    print(f"   Nombre: {user.full_name}")
    print(f"   DNI: {user.dni}")
    print(f"   PIN: {pin}")
    print(f"   Rol: {user.role}")
    print(f"   Teléfono: {user.phone or 'No especificado'}")
    
    print("\n🔑 CREDENCIALES DE ACCESO:")
    print(f"   DNI: {dni}")
    print(f"   PIN: {pin}")
    
    print("\n💡 Ahora puedes:")
    print("   1. Ejecutar: python scripts/seed_products.py")
    print("   2. Iniciar el servidor: uvicorn app.main:app --reload")
    print("   3. Acceder con las credenciales mostradas arriba")
    print("=" * 60)

except Exception as e:
    db.rollback()
    print(f"\n❌ Error al crear usuario: {e}")
    sys.exit(1)
finally:
    db.close()