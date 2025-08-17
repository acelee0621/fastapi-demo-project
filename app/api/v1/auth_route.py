# app/api/v1/auth_route.py
from fastapi import Depends, APIRouter, status
from fastapi.security import OAuth2PasswordRequestForm
from loguru import logger

from app.domains.users.service_dependencies import get_user_service
from app.domains.users.auth_dependencies import get_current_user
from app.domains.users.user_service import UserService
from app.schemas.auth import LoginData, Token
from app.schemas.users import UserCreate, UserResponse


router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    service: UserService = Depends(get_user_service),
) -> Token:
    """Authenticate user and return token."""
    login_data = LoginData(username=form_data.username, password=form_data.password)
    logger.debug(f"Login attempt: {login_data.username}")
    login_session = await service.authenticate(login_data)
    return login_session


@router.post(
    "/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED
)
async def register(
    user_data: UserCreate, service: UserService = Depends(get_user_service)
) -> UserResponse:
    logger.debug(f"Registering user: {user_data.username}")
    try:
        new_user = await service.create_user(user_data)
        logger.info(f"Created user {new_user.id}")
        return new_user
    except Exception as e:
        logger.error(f"Failed to create hero: {str(e)}")
        raise


@router.get("/me", response_model=UserResponse)
async def get_me(user: UserResponse = Depends(get_current_user)) -> UserResponse:
    """Get current authenticated user."""
    return user
