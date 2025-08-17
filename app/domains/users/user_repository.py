# app/domains/users/user_repository.py
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.core.exceptions import AlreadyExistsException, NotFoundException

from app.core.security import get_password_hash
from app.models.users import User
from app.schemas.users import UserCreate


class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, user_data: UserCreate) -> User:
        # Check if user exists
        existing_user = await self.get_by_username(user_data.username)
        if existing_user:
            raise AlreadyExistsException("Username already registered")
        # Create user
        new_user = User(
            username=user_data.username,
            password_hash=get_password_hash(user_data.password),  # 加密密码
        )
        self.session.add(new_user)
        await self.session.commit()
        await self.session.refresh(new_user)
        logger.info(f"Created user: {new_user.username}")
        return new_user

    async def get_by_id(self, user_id: int) -> User:
        query = select(User).where(User.id == user_id)
        result = await self.session.scalars(query)
        user = result.one_or_none()
        if not user:
            raise NotFoundException("User not found")
        return user

    async def get_by_username(self, username: str) -> User | None:
        query = select(User).where(User.username == username)
        result = await self.session.scalars(query)
        user = result.one_or_none()
        return user
