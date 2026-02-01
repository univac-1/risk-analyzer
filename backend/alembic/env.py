from logging.config import fileConfig
import os

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

from app.models.database import Base
from app.models.job import AnalysisJob, Video, RiskItem

target_metadata = Base.metadata

def get_url():
    url = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:postgres@localhost:5432/video_risk_analyzer"
    )
    # Convert async driver to sync driver for Alembic
    # asyncpg -> psycopg2 (or default postgresql driver)
    if "+asyncpg" in url:
        url = url.replace("postgresql+asyncpg", "postgresql+psycopg2")
    elif "+aiosqlite" in url:
        url = url.replace("sqlite+aiosqlite", "sqlite")
    return url


def run_migrations_offline() -> None:
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = get_url()
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
