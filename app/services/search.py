from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, and_, func
from sqlalchemy.orm import selectinload

from app.models import Contractor, Category, SearchLog, contractor_category_table


async def search_contractors(
    session: AsyncSession,
    query: str,
    region_id: Optional[int] = None,
    category_id: Optional[int] = None,
    limit: int = 50
) -> List[Contractor]:
    """
    Поиск исполнителей
    
    Args:
        session: Сессия БД
        query: Поисковый запрос
        region_id: ID региона (фильтр)
        category_id: ID категории (фильтр)
        limit: Максимальное количество результатов
    
    Returns:
        Список исполнителей
    """
    
    # Базовый запрос
    stmt = select(Contractor).where(Contractor.is_active == True)
    
    # Фильтр по региону
    if region_id:
        stmt = stmt.where(Contractor.region_id == region_id)
    
    # Фильтр по категории
    if category_id:
        stmt = stmt.join(
            contractor_category_table,
            Contractor.id == contractor_category_table.c.contractor_id
        ).where(contractor_category_table.c.category_id == category_id)
    
    # Поиск по тексту
    if query:
        search_pattern = f"%{query.lower()}%"
        stmt = stmt.where(
            or_(
                func.lower(Contractor.name).like(search_pattern),
                func.lower(Contractor.description).like(search_pattern)
            )
        )
    
    # Сортировка: премиум сверху, затем по рейтингу
    stmt = stmt.order_by(
        Contractor.is_premium.desc(),
        Contractor.rating.desc(),
        Contractor.created_at.desc()
    )
    
    # Ограничение
    stmt = stmt.limit(limit)
    
    # Загружаем связанные данные
    stmt = stmt.options(
        selectinload(Contractor.region),
        selectinload(Contractor.categories),
        selectinload(Contractor.photos)
    )
    
    result = await session.execute(stmt)
    return result.scalars().all()


async def log_search(
    session: AsyncSession,
    user_id: int,
    query: str,
    region_id: Optional[int] = None,
    category_id: Optional[int] = None,
    results_count: int = 0
):
    """Логировать поисковый запрос"""
    search_log = SearchLog(
        user_id=user_id,
        query=query,
        region_id=region_id,
        category_id=category_id,
        results_count=results_count
    )
    session.add(search_log)
    await session.commit()

