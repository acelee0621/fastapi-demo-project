# app/models/collections.py
from typing import Optional

from sqlalchemy import String, Integer, Text, UniqueConstraint, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.mixin import DateTimeMixin

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from app.models.users import User
    from app.models.heroes import Hero


class Collection(Base, DateTimeMixin):
    __tablename__ = "collections"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(
        String(256), nullable=False
    )
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # 外键：关联到 User 表
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), index=True, nullable=False
    )
    # 多对一关系：Collection -> User
    owner: Mapped["User"] = relationship("User", back_populates="collections")

    # 多对多关系：Collection -> Hero
    heroes: Mapped[list["Hero"]] = relationship(
        "Hero",
        secondary="collection_hero",       
        lazy="selectin",
    )

    # 表级约束：确保每个用户的收藏标题唯一
    __table_args__ = (
        UniqueConstraint("title", "user_id", name="unique_user_collections_title"),
    )

    def __repr__(self) -> str:
        return f"<Collection(id={self.id!r}, title={self.title!r})>"


class CollectionHero(Base):
    __tablename__ = "collection_hero"

    collection_id: Mapped[int] = mapped_column(
        ForeignKey("collections.id"), primary_key=True
    )
    hero_id: Mapped[int] = mapped_column(ForeignKey("heroes.id"), primary_key=True)
