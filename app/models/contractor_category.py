from sqlalchemy import Table, Column, Integer, ForeignKey
from app.models.base import Base

# Таблица связи многие-ко-многим между исполнителями и категориями
contractor_category_table = Table(
    "contractor_categories",
    Base.metadata,
    Column("id", Integer, primary_key=True),
    Column("contractor_id", Integer, ForeignKey("contractors.id", ondelete="CASCADE"), nullable=False),
    Column("category_id", Integer, ForeignKey("categories.id", ondelete="CASCADE"), nullable=False),
)

