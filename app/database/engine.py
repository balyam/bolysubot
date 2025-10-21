from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
    AsyncSession,
    AsyncEngine
)
from config import settings

# Создаем асинхронный engine
engine: AsyncEngine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,  # Логирование SQL запросов в debug режиме
    pool_pre_ping=True,   # Проверка соединения перед использованием
    pool_size=10,
    max_overflow=20
)

# Session maker для создания сессий
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency для получения сессии БД.
    Используется в FastAPI и боте.
    """
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

