from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import get_db
from core.exceptions import CredentialsException, PermissionDeniedException
from core.security import verify_token
from models.user import User
from repositories.user import user_repository

# OAuth2 scheme for extracting Bearer tokens
reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/token"
)


async def get_current_user(
    db: AsyncSession = Depends(get_db), token: str = Depends(reusable_oauth2)
) -> User:
    """Dependency to extract and verify the current user from JWT."""
    payload = verify_token(token)
    if not payload or payload.get("type") != "access":
        raise CredentialsException(detail="Could not validate access token credentials")
        
    user_id = payload.get("sub")
    if not user_id:
        raise CredentialsException(detail="Token missing subject identifier")
        
    user = await user_repository.get(db, int(user_id))
    if not user:
        raise CredentialsException(detail="User not found")
        
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Dependency to verify user is active."""
    if not current_user.is_active:
        raise PermissionDeniedException(detail="Inactive user account")
    return current_user


async def get_current_verified_user(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """Dependency to verify user email is verified."""
    if not current_user.is_verified:
        raise PermissionDeniedException(detail="Please verify your email address to unlock AI scheduling features")
    return current_user


async def check_admin_user(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """Dependency to verify admin privileges."""
    if current_user.role != "admin":
        raise PermissionDeniedException(detail="Admin access required")
    return current_user
