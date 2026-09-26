from datetime import datetime, timezone, timedelta
from typing import Optional
from sqlalchemy import select, update, and_
from sqlalchemy.ext.asyncio import AsyncSession
from models.user import User
from models.auth_tokens import RefreshToken, PasswordResetToken, EmailVerificationToken
from repositories.base import BaseRepository
from core.security import hash_password


class UserRepository(BaseRepository[User]):
    def __init__(self):
        super().__init__(User)

    async def get_by_email(self, db: AsyncSession, email: str) -> Optional[User]:
        stmt = select(User).where(User.email == email)
        res = await db.execute(stmt)
        return res.scalars().first()

    async def create_user(self, db: AsyncSession, *, email: str, password_raw: str, full_name: Optional[str] = None) -> User:
        hashed = hash_password(password_raw)
        db_obj = User(
            email=email,
            hashed_password=hashed,
            full_name=full_name
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj


class TokenRepository:
    # Refresh Token Operations
    async def create_refresh_token(
        self, db: AsyncSession, *, user_id: int, token_str: str, expires_in_days: int
    ) -> RefreshToken:
        expires_at = datetime.now(timezone.utc) + timedelta(days=expires_in_days)
        db_obj = RefreshToken(
            user_id=user_id,
            token=token_str,
            expires_at=expires_at
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def get_refresh_token(self, db: AsyncSession, token_str: str) -> Optional[RefreshToken]:
        stmt = select(RefreshToken).where(
            and_(
                RefreshToken.token == token_str,
                RefreshToken.is_revoked == False,
                RefreshToken.expires_at > datetime.now(timezone.utc)
            )
        )
        res = await db.execute(stmt)
        return res.scalars().first()

    async def revoke_refresh_token(self, db: AsyncSession, token_str: str) -> bool:
        stmt = (
            update(RefreshToken)
            .where(RefreshToken.token == token_str)
            .values(is_revoked=True)
        )
        await db.execute(stmt)
        await db.commit()
        return True

    # Password Reset Token Operations
    async def create_password_reset_token(
        self, db: AsyncSession, *, user_id: int, token_str: str, expires_in_minutes: int = 60
    ) -> PasswordResetToken:
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=expires_in_minutes)
        db_obj = PasswordResetToken(
            user_id=user_id,
            token=token_str,
            expires_at=expires_at
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def get_password_reset_token(self, db: AsyncSession, token_str: str) -> Optional[PasswordResetToken]:
        stmt = select(PasswordResetToken).where(
            and_(
                PasswordResetToken.token == token_str,
                PasswordResetToken.is_used == False,
                PasswordResetToken.expires_at > datetime.now(timezone.utc)
            )
        )
        res = await db.execute(stmt)
        return res.scalars().first()

    async def mark_password_reset_token_used(self, db: AsyncSession, token_str: str) -> bool:
        stmt = (
            update(PasswordResetToken)
            .where(PasswordResetToken.token == token_str)
            .values(is_used=True)
        )
        await db.execute(stmt)
        await db.commit()
        return True

    # Email Verification Token Operations
    async def create_email_verification_token(
        self, db: AsyncSession, *, user_id: int, token_str: str, expires_in_days: int = 1
    ) -> EmailVerificationToken:
        expires_at = datetime.now(timezone.utc) + timedelta(days=expires_in_days)
        db_obj = EmailVerificationToken(
            user_id=user_id,
            token=token_str,
            expires_at=expires_at
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def get_email_verification_token(self, db: AsyncSession, token_str: str) -> Optional[EmailVerificationToken]:
        stmt = select(EmailVerificationToken).where(
            and_(
                EmailVerificationToken.token == token_str,
                EmailVerificationToken.is_used == False,
                EmailVerificationToken.expires_at > datetime.now(timezone.utc)
            )
        )
        res = await db.execute(stmt)
        return res.scalars().first()

    async def mark_email_verification_token_used(self, db: AsyncSession, token_str: str) -> bool:
        stmt = (
            update(EmailVerificationToken)
            .where(EmailVerificationToken.token == token_str)
            .values(is_used=True)
        )
        await db.execute(stmt)
        await db.commit()
        return True


user_repository = UserRepository()
token_repository = TokenRepository()
