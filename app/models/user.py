from datetime import datetime
from typing import Optional, List
from sqlalchemy import BigInteger, String, Boolean, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base


class User(Base):
    """Пользователи бота"""
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False, index=True)
    username: Mapped[Optional[str]] = mapped_column(String(255))
    first_name: Mapped[Optional[str]] = mapped_column(String(255))
    last_name: Mapped[Optional[str]] = mapped_column(String(255))
    is_blocked: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    is_approved: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")  # Разрешён ли доступ
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")  # Является ли администратором
    invited_by_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))  # Кто пригласил
    invite_token: Mapped[Optional[str]] = mapped_column(String(50))  # Токен приглашения (если использовался)
    preferred_region_id: Mapped[Optional[int]] = mapped_column(ForeignKey("regions.id", ondelete="SET NULL"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    last_activity: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )
    
    # Relationships
    preferred_region: Mapped[Optional["Region"]] = relationship("Region", back_populates="users")
    reviews: Mapped[List["Review"]] = relationship("Review", back_populates="user")
    search_logs: Mapped[List["SearchLog"]] = relationship("SearchLog", back_populates="user")
    invited_by: Mapped[Optional["User"]] = relationship("User", remote_side="User.id", back_populates="invites")
    invites: Mapped[List["User"]] = relationship("User", back_populates="invited_by")
    
    def __repr__(self):
        return f"<User {self.telegram_id} ({self.username})>"

