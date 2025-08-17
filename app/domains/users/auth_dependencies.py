# app/domains/users/auth_dependencies.py
from fastapi import Depends, HTTPException, status
import jwt
from jwt.exceptions import PyJWTError
from app.core.config import settings
from app.core.security import oauth2_scheme
from app.domains.users.service_dependencies import get_user_service
from app.domains.users.user_service import UserService
from app.schemas.users import UserResponse


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    service: UserService = Depends(get_user_service),
) -> UserResponse:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]
        )
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except PyJWTError:
        raise credentials_exception

    user = await service.get_user_by_username(username)
    if user is None:
        raise credentials_exception
    return UserResponse.model_validate(user)
