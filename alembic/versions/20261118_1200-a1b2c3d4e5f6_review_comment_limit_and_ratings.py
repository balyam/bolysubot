"""Review comment limit (500) and rating recalculation

- reviews.comment: TEXT -> VARCHAR(500) (как в модели после коммита c8d402b)
- пересчёт contractors.rating / reviews_count только по одобренным
  и видимым отзывам (раньше учитывались и непромодерированные)

Revision ID: a1b2c3d4e5f6
Revises: cc21790a3e52
Create Date: 2026-11-18 12:00:00+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = 'cc21790a3e52'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Комментарии длиннее 500 символов (если остались с тех времён,
    # когда лимита не было) будут обрезаны
    op.alter_column(
        'reviews',
        'comment',
        existing_type=sa.Text(),
        type_=sa.String(length=500),
        existing_nullable=True,
        postgresql_using='left(comment, 500)',
    )

    op.execute(
        """
        UPDATE contractors c
        SET rating = COALESCE(s.avg_rating, 0),
            reviews_count = COALESCE(s.cnt, 0)
        FROM contractors c2
        LEFT JOIN (
            SELECT contractor_id, AVG(rating) AS avg_rating, COUNT(*) AS cnt
            FROM reviews
            WHERE is_moderated = true AND is_visible = true
            GROUP BY contractor_id
        ) s ON s.contractor_id = c2.id
        WHERE c.id = c2.id
        """
    )


def downgrade() -> None:
    op.alter_column(
        'reviews',
        'comment',
        existing_type=sa.String(length=500),
        type_=sa.Text(),
        existing_nullable=True,
    )
