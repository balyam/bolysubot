"""Unique review per (user, contractor)

Revision ID: c3d4e5f6a7b8
Revises: a1b2c3d4e5f6
Create Date: 2026-11-21 13:00:00+00:00

"""
from typing import Sequence, Union

from alembic import op


revision: str = 'c3d4e5f6a7b8'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Если дубли уже есть — оставляем самый ранний отзыв, остальные удаляем
    op.execute("""
        DELETE FROM reviews r
        USING reviews older
        WHERE r.user_id = older.user_id
          AND r.contractor_id = older.contractor_id
          AND r.id > older.id
    """)
    # Удалённые дубли могли входить в рейтинг — пересчитываем
    op.execute("""
        UPDATE contractors c SET
            rating = COALESCE((
                SELECT AVG(r.rating) FROM reviews r
                WHERE r.contractor_id = c.id AND r.is_visible AND r.is_moderated
            ), 0),
            reviews_count = (
                SELECT COUNT(*) FROM reviews r
                WHERE r.contractor_id = c.id AND r.is_visible AND r.is_moderated
            )
    """)
    op.create_unique_constraint(
        'uq_reviews_user_contractor', 'reviews', ['user_id', 'contractor_id']
    )


def downgrade() -> None:
    op.drop_constraint('uq_reviews_user_contractor', 'reviews', type_='unique')
