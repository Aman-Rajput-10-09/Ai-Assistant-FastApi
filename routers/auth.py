from fastapi import APIRouter, Depends, status, BackgroundTasks
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import get_db
from services.auth import auth_service
from schemas.auth import (
    RegisterRequest,
    LoginRequest,
    Token,
    RefreshTokenRequest,
    ForgotPasswordRequest,
    ResetPasswordRequest,
    EmailVerificationRequest
)
from schemas.user import UserRead

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register(register_data: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """Register a new user account."""
    return await auth_service.register_user(db, register_data)


@router.post("/login", response_model=Token)
async def login(login_data: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Authenticate and return Access/Refresh tokens."""
    return await auth_service.login_user(db, login_data.email, login_data.password)


@router.post("/token", response_model=Token)
async def swagger_token_login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """OAuth2-compatible login used by Swagger UI's Authorize dialog."""
    return await auth_service.login_user(db, form_data.username, form_data.password)


@router.post("/refresh", response_model=Token)
async def refresh(refresh_data: RefreshTokenRequest, db: AsyncSession = Depends(get_db)):
    """Verify refresh token and return new tokens."""
    return await auth_service.refresh_access_token(db, refresh_data.refresh_token)


@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(refresh_data: RefreshTokenRequest, db: AsyncSession = Depends(get_db)):
    """Revoke refresh token on logout."""
    await auth_service.logout_user(db, refresh_data.refresh_token)
    return {"message": "Logged out successfully"}


@router.post("/forgot-password", status_code=status.HTTP_200_OK)
async def forgot_password(forgot_data: ForgotPasswordRequest, db: AsyncSession = Depends(get_db)):
    """Request a password reset link (simulated via mock emails)."""
    await auth_service.forgot_password(db, forgot_data.email)
    return {"message": "If the email exists, a password reset link has been logged"}


@router.post("/reset-password", status_code=status.HTTP_200_OK)
async def reset_password(reset_data: ResetPasswordRequest, db: AsyncSession = Depends(get_db)):
    """Reset user password using token."""
    await auth_service.reset_password(db, reset_data.token, reset_data.new_password)
    return {"message": "Password reset completed successfully"}


@router.post("/verify", status_code=status.HTTP_200_OK)
async def verify_email(verify_data: EmailVerificationRequest, db: AsyncSession = Depends(get_db)):
    """Verify email verification token."""
    await auth_service.verify_email(db, verify_data.token)
    return {"message": "Email address verified successfully"}
