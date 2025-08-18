# app/models/users.py
from typing import Optional

from sqlalchemy import String, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.mixin import DateTimeMixin

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from app.models.collections import Collection


class User(Base, DateTimeMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(
        String(64), index=True, unique=True, nullable=False
    )
    password_hash: Mapped[Optional[str]] = mapped_column(String(256))
    # 一对多关系 User -> Collection
    collections: Mapped[list["Collection"]] = relationship(
        "Collection",
        back_populates="owner",
        cascade="all, delete-orphan",
        # lazy 默认是 "select"，但我们查 user 时不希望自动加载 collections，保持默认即可
    )

    def __repr__(self):
        return f"<User(id={self.id!r}, username={self.username!r})>"
