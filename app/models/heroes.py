# app/models/heroes.py
from sqlalchemy import String, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.models.mixin import DateTimeMixin

class Hero(Base, DateTimeMixin):
    __tablename__ = "heroes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    alias: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    powers: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    def __repr__(self) -> str:
        return f"<Hero(id={self.id!r}, name={self.name!r}, alias={self.alias!r})>"