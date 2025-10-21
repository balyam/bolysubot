from datetime import datetime
from typing import Optional
from sqlalchemy import String, Text, Integer, BigInteger, Boolean, ForeignKey, DateTime, func, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin


class Review(Base, TimestampMixin):
    """Отзывы об исполнителях"""
    __tablename__ = "reviews"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    contractor_id: Mapped[int] = mapped_column(ForeignKey("contractors.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    user_name: Mapped[Optional[str]] = mapped_column(String(255))  # Имя пользователя из Telegram
    rating: Mapped[int] = mapped_column(Integer, nullable=False)  # 1-5 звёзд
    comment: Mapped[Optional[str]] = mapped_column(Text)
    is_moderated: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    is_visible: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    
    # Relationships
    contractor: Mapped["Contractor"] = relationship("Contractor", back_populates="reviews")
    user: Mapped["User"] = relationship("User", back_populates="reviews")
    
    # Ограничение на рейтинг (1-5)
    __table_args__ = (
        CheckConstraint("rating >= 1 AND rating <= 5", name="check_rating_range"),
    )
    
    def __repr__(self):
        return f"<Review {self.id} for Contractor {self.contractor_id} (Rating: {self.rating})>"

