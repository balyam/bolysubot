from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, Text, Integer, ForeignKey, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base


class Category(Base):
    """Категории услуг"""
    __tablename__ = "categories"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text)
    parent_id: Mapped[Optional[int]] = mapped_column(ForeignKey("categories.id", ondelete="CASCADE"))
    icon: Mapped[Optional[str]] = mapped_column(String(10))  # emoji или код иконки
    order_index: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    parent: Mapped[Optional["Category"]] = relationship(
        "Category",
        remote_side="Category.id",
        back_populates="children"
    )
    children: Mapped[List["Category"]] = relationship(
        "Category",
        back_populates="parent",
        cascade="all, delete-orphan"
    )
    contractors: Mapped[List["Contractor"]] = relationship(
        "Contractor",
        secondary="contractor_categories",
        back_populates="categories"
    )
    search_logs: Mapped[List["SearchLog"]] = relationship("SearchLog", back_populates="category")
    
    def __repr__(self):
        return f"<Category {self.name}>"
    
    def __str__(self):
        return self.name

