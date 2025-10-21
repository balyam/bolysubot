from datetime import datetime
from typing import Optional
from sqlalchemy import String, Integer, ForeignKey, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base


class SearchLog(Base):
    """Логи поиска для статистики"""
    __tablename__ = "search_logs"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    query: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    region_id: Mapped[Optional[int]] = mapped_column(ForeignKey("regions.id", ondelete="SET NULL"))
    category_id: Mapped[Optional[int]] = mapped_column(ForeignKey("categories.id", ondelete="SET NULL"))
    results_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="search_logs")
    region: Mapped[Optional["Region"]] = relationship("Region", back_populates="search_logs")
    category: Mapped[Optional["Category"]] = relationship("Category", back_populates="search_logs")
    
    def __repr__(self):
        return f"<SearchLog {self.id}: '{self.query}' ({self.results_count} results)>"

