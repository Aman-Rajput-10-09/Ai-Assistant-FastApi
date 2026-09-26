import logging
import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from core.exceptions import CredentialsException, ConflictException, NotFoundException, BadRequestException
from core.security import verify_password, hash_password, create_access_token, create_refresh_token, verify_token
from models.user import User
from models.auth_tokens import RefreshToken, PasswordResetToken, EmailVerificationToken
from repositories.user import user_repository, token_repository
from schemas.auth import RegisterRequest, Token
from core.config import settings

logger = logging.getLogger(__name__)


class AuthService:
    async def register_user(self, db: AsyncSession, register_data: RegisterRequest) -> User:
        """Register a new user, and generate an email verification token."""
        existing_user = await user_repository.get_by_email(db, register_data.email)
        if existing_user:
            raise ConflictException(detail="Email already registered")
            
        user = await user_repository.create_user(
            db,
            email=register_data.email,
            password_raw=register_data.password,
            full_name=register_data.full_name
        )
        
        # Create verification token
        verification_token = uuid.uuid4().hex
        await token_repository.create_email_verification_token(
            db, user_id=user.id, token_str=verification_token, expires_in_days=1
        )
        
        # Log token to simulate sending an email
        logger.info(f"Verification token created for user {user.email}: {verification_token}")
        print(f"[MOCK EMAIL] Verification Link: http://localhost:8000/api/v1/auth/verify?token={verification_token}")
        
        return user

    async def login_user(self, db: AsyncSession, email: str, password_raw: str) -> Token:
        """Authenticate user and return fresh Access and Refresh tokens."""
        user = await user_repository.get_by_email(db, email)
        if not user or not verify_password(password_raw, user.hashed_password):
            raise CredentialsException(detail="Invalid email or password")
            
        if not user.is_active:
            raise BadRequestException(detail="User account is deactivated")

        # Generate tokens
        access_token = create_access_token(subject=user.id)
        refresh_token_str = create_refresh_token(subject=user.id)
        
        # Save refresh token in database
        await token_repository.create_refresh_token(
            db, 
            user_id=user.id, 
            token_str=refresh_token_str, 
            expires_in_days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )
        
        return Token(access_token=access_token, refresh_token=refresh_token_str)

    async def refresh_access_token(self, db: AsyncSession, refresh_token_str: str) -> Token:
        """Verify the refresh token and return a new Access token and (rotated) Refresh token."""
        # 1. Parse token payload (JWT validation)
        payload = verify_token(refresh_token_str)
        if not payload or payload.get("type") != "refresh":
            raise CredentialsException(detail="Invalid refresh token")
            
        # 2. Check token in database (liveness, revocation checks)
        db_token = await token_repository.get_refresh_token(db, refresh_token_str)
        if not db_token:
            raise CredentialsException(detail="Refresh token is expired, revoked, or invalid")
            
        user_id = int(payload.get("sub"))
        user = await user_repository.get(db, user_id)
        if not user or not user.is_active:
            raise CredentialsException(detail="User account is invalid or deactivated")
            
        # 3. Revoke old refresh token (Token Rotation)
        await token_repository.revoke_refresh_token(db, refresh_token_str)
        
        # 4. Generate new tokens
        new_access_token = create_access_token(subject=user.id)
        new_refresh_token_str = create_refresh_token(subject=user.id)
        
        # Save new refresh token
        await token_repository.create_refresh_token(
            db,
            user_id=user.id,
            token_str=new_refresh_token_str,
            expires_in_days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )
        
        return Token(access_token=new_access_token, refresh_token=new_refresh_token_str)

    async def logout_user(self, db: AsyncSession, refresh_token_str: str) -> None:
        """Revoke a refresh token on logout."""
        await token_repository.revoke_refresh_token(db, refresh_token_str)

    async def forgot_password(self, db: AsyncSession, email: str) -> None:
        """Generate a password reset token and log to console."""
        user = await user_repository.get_by_email(db, email)
        if not user:
            # Prevent user enumeration by not throwing 404, just return silently
            logger.info(f"Password reset requested for non-existent email: {email}")
            return
            
        reset_token = uuid.uuid4().hex
        await token_repository.create_password_reset_token(
            db, user_id=user.id, token_str=reset_token, expires_in_minutes=60
        )
        
        logger.info(f"Password reset token created for user {user.email}: {reset_token}")
        print(f"[MOCK EMAIL] Password Reset Link: http://localhost:8000/api/v1/auth/reset-password?token={reset_token}")

    async def reset_password(self, db: AsyncSession, token_str: str, new_password_raw: str) -> None:
        """Reset user password using verification token."""
        db_token = await token_repository.get_password_reset_token(db, token_str)
        if not db_token:
            raise BadRequestException(detail="Invalid or expired reset token")
            
        user = await user_repository.get(db, db_token.user_id)
        if not user or not user.is_active:
            raise NotFoundException(detail="User not found or deactivated")
            
        # Update password
        user.hashed_password = hash_password(new_password_raw)
        db.add(user)
        
        # Mark token as used
        await token_repository.mark_password_reset_token_used(db, token_str)
        await db.commit()

    async def verify_email(self, db: AsyncSession, token_str: str) -> None:
        """Verify user email address using token."""
        db_token = await token_repository.get_email_verification_token(db, token_str)
        if not db_token:
            raise BadRequestException(detail="Invalid or expired email verification token")
            
        user = await user_repository.get(db, db_token.user_id)
        if not user or not user.is_active:
            raise NotFoundException(detail="User not found or deactivated")
            
        # Mark user as verified
        user.is_verified = True
        db.add(user)
        
        # Mark token as used
        await token_repository.mark_email_verification_token_used(db, token_str)
        await db.commit()


auth_service = AuthService()
