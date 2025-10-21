from datetime import datetime
from typing import Optional
from sqlalchemy import String, Boolean, Integer, ForeignKey, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base


class ContractorPhoto(Base):
    """Фотографии исполнителей"""
    __tablename__ = "contractor_photos"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    contractor_id: Mapped[int] = mapped_column(ForeignKey("contractors.id", ondelete="CASCADE"), nullable=False)
    file_id: Mapped[str] = mapped_column(String(255), nullable=False)  # Telegram file_id
    file_path: Mapped[Optional[str]] = mapped_column(String(500))  # Путь к файлу на диске
    is_main: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    order_index: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    contractor: Mapped["Contractor"] = relationship("Contractor", back_populates="photos")
    
    def __repr__(self):
        return f"<ContractorPhoto {self.id} for Contractor {self.contractor_id}>"

