from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

from app.config import get_settings

settings = get_settings()

SQLALCHEMY_DATABASE_URL = settings.database_url

# 同期エンジン用URL（psycopg2を使用）
if SQLALCHEMY_DATABASE_URL.startswith("postgresql+asyncpg://"):
    SYNC_DATABASE_URL = SQLALCHEMY_DATABASE_URL.replace(
        "postgresql+asyncpg://", "postgresql://"
    )
elif SQLALCHEMY_DATABASE_URL.startswith("sqlite+aiosqlite://"):
    SYNC_DATABASE_URL = SQLALCHEMY_DATABASE_URL.replace(
        "sqlite+aiosqlite://", "sqlite://"
    )
else:
    SYNC_DATABASE_URL = SQLALCHEMY_DATABASE_URL

# 非同期エンジン用URL（asyncpgを使用）
if SQLALCHEMY_DATABASE_URL.startswith("postgresql://"):
    ASYNC_DATABASE_URL = SQLALCHEMY_DATABASE_URL.replace(
        "postgresql://", "postgresql+asyncpg://"
    )
elif SQLALCHEMY_DATABASE_URL.startswith("postgresql+asyncpg://"):
    ASYNC_DATABASE_URL = SQLALCHEMY_DATABASE_URL
else:
    ASYNC_DATABASE_URL = SQLALCHEMY_DATABASE_URL

engine = create_engine(SYNC_DATABASE_URL)
async_engine = create_async_engine(ASYNC_DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
AsyncSessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=async_engine, class_=AsyncSession
)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_async_db():
    async with AsyncSessionLocal() as session:
        yield session
