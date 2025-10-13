"""Alembic environment configuration for QueVendí"""

from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context
import sys
import os

# Agregar app al path para importar modelos
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Importar configuración y base
from app.core.config import settings
from app.core.database import Base

# Importar TODOS los modelos (para que Alembic los detecte)
from app.models.user import User
from app.models.store import Store
from app.models.product import Product
from app.models.sale import Sale, SaleItem

# Configuración de Alembic
config = context.config

# Sobreescribir la URL de la base de datos con la del .env
config.set_main_option('sqlalchemy.url', settings.DATABASE_URL)

# Interpretar el archivo de logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Metadata de los modelos
target_metadata = Base.metadata

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, 
            target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()