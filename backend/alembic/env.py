"""Alembic environment configuration for migrations."""

import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import create_engine

from app.database import Base
from app.models import *  # noqa: F401,F403 - import all models for autogenerate

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

db_url = os.environ.get("DATABASE_URL", config.get_main_option("sqlalchemy.url"))


def run_migrations_offline():
    """Run migrations in 'offline' mode."""
    context.configure(url=db_url, target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    """Run migrations in 'online' mode."""
    connectable = create_engine(db_url)
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
