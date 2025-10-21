from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, Boolean, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base


class Region(Base):
    """Регионы/Города"""
    __tablename__ = "regions"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    region: Mapped[Optional[str]] = mapped_column(String(255))  # область/край
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    contractors: Mapped[List["Contractor"]] = relationship("Contractor", back_populates="region")
    users: Mapped[List["User"]] = relationship("User", back_populates="preferred_region")
    search_logs: Mapped[List["SearchLog"]] = relationship("SearchLog", back_populates="region")
    
    def __repr__(self):
        return f"<Region {self.name}>"
    
    def __str__(self):
        return self.name

