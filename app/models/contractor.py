from datetime import datetime
from typing import Optional, List
from decimal import Decimal
from sqlalchemy import String, Text, Boolean, Integer, Numeric, ForeignKey, DateTime, func, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin


class Contractor(Base, TimestampMixin):
    """Исполнители"""
    __tablename__ = "contractors"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text)
    phone: Mapped[str] = mapped_column(String(20), nullable=False)
    additional_phones: Mapped[Optional[List[str]]] = mapped_column(JSON)  # массив дополнительных телефонов
    telegram_username: Mapped[Optional[str]] = mapped_column(String(255))
    address: Mapped[Optional[str]] = mapped_column(String(500))
    
    # Геолокация
    region_id: Mapped[int] = mapped_column(ForeignKey("regions.id", ondelete="RESTRICT"), nullable=False)
    latitude: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 8))
    longitude: Mapped[Optional[Decimal]] = mapped_column(Numeric(11, 8))
    
    # Рейтинг и статистика
    rating: Mapped[Decimal] = mapped_column(Numeric(3, 2), default=0, server_default="0")
    reviews_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    views_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    
    # Статус
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    
    # Премиум подписка
    is_premium: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    premium_until: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Relationships
    region: Mapped["Region"] = relationship("Region", back_populates="contractors")
    categories: Mapped[List["Category"]] = relationship(
        "Category",
        secondary="contractor_categories",
        back_populates="contractors"
    )
    photos: Mapped[List["ContractorPhoto"]] = relationship(
        "ContractorPhoto",
        back_populates="contractor",
        cascade="all, delete-orphan",
        order_by="ContractorPhoto.order_index"
    )
    reviews: Mapped[List["Review"]] = relationship(
        "Review",
        back_populates="contractor",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self):
        return f"<Contractor {self.name} (Region: {self.region_id})>"
    
    def __str__(self):
        return self.name

