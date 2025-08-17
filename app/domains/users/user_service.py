# app/domains/users/user_service.py
from datetime import timedelta

from loguru import logger

from app.core.config import settings
from app.core.exceptions import UnauthorizedException
from app.core.security import create_access_token, verify_password
from app.domains.users.user_repository import UserRepository
from app.schemas.users import UserCreate, UserInDB, UserResponse
from app.schemas.auth import LoginData, Token


class UserService:
    """Service for handling user business logic."""

    def __init__(self, repository: UserRepository):
        self.repository = repository

    async def create_user(self, user_data: UserCreate) -> UserResponse:
        """Create a new user."""
        new_user = await self.repository.create(user_data)
        return UserResponse.model_validate(new_user)

    async def authenticate(self, login_data: LoginData) -> Token:
        """Authenticate user and return token."""
        # Get user
        user = await self.repository.get_by_username(login_data.username)

        # Verify credentials
        if not user or not verify_password(
            login_data.password, str(user.password_hash)
        ):
            raise UnauthorizedException(detail="Incorrect username or password")

        # Create access token
        access_token = create_access_token(
            data={"sub": str(user.username)},
            expires_delta=timedelta(minutes=settings.JWT_EXPIRATION),
        )

        logger.info(f"User authenticated: {user.username}")
        return Token(access_token=access_token)

    async def get_user(self, user_id: int) -> UserResponse:
        """Get user by ID."""
        user = await self.repository.get_by_id(user_id)
        return UserResponse.model_validate(user)

    async def get_user_by_username(self, username: str) -> UserInDB:
        """Get user by username."""
        user = await self.repository.get_by_username(username)
        return UserInDB.model_validate(user)
