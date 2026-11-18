from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from app.models import Contractor, Review


def _rating_stats_stmt(contractor_id: int):
    """В рейтинг идут только одобренные модератором и видимые отзывы"""
    return select(
        func.avg(Review.rating).label("avg_rating"),
        func.count(Review.id).label("count")
    ).where(
        Review.contractor_id == contractor_id,
        Review.is_visible == True,
        Review.is_moderated == True
    )


def _update_stmt(contractor_id: int, stats):
    avg_rating = float(stats.avg_rating) if stats.avg_rating else 0
    return (
        update(Contractor)
        .where(Contractor.id == contractor_id)
        .values(rating=avg_rating, reviews_count=stats.count)
    )


async def update_contractor_rating(session: AsyncSession, contractor_id: int) -> None:
    """Пересчитать рейтинг исполнителя (async, для бота)"""
    stats = (await session.execute(_rating_stats_stmt(contractor_id))).one()
    await session.execute(_update_stmt(contractor_id, stats))


def update_contractor_rating_sync(session: Session, contractor_id: int) -> None:
    """Пересчитать рейтинг исполнителя (sync, для админки)"""
    stats = session.execute(_rating_stats_stmt(contractor_id)).one()
    session.execute(_update_stmt(contractor_id, stats))
