import secrets
from uuid import UUID

import structlog
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, generate_otp, hash_token, verify_otp
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.repositories.refresh_token import RefreshTokenRepository
from app.repositories.user import UserRepository
from app.schemas.auth import (
    RequestOTPResponse,
    TokenResponse,
    VerifyOTPRequest,
)
from app.schemas.user import UserRead

log = structlog.get_logger(__name__)


class AuthService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._user_repo = UserRepository(session)
        self._token_repo = RefreshTokenRepository(session)

    async def request_otp(self, country_code: str, phone_number: str) -> RequestOTPResponse:
        """Generate and 'send' (print) an OTP for the given phone number."""
        generate_otp()  # mock — prints OTP to stdout; real impl would send SMS
        log.info("OTP requested", country_code=country_code, phone_number=phone_number)
        return RequestOTPResponse(
            country_code=country_code,
            phone_number=phone_number,
            message="OTP sent successfully",
        )

    async def verify_otp_and_login(self, payload: VerifyOTPRequest) -> TokenResponse:
        """Validate OTP, upsert user, issue access + refresh tokens."""
        if not verify_otp(payload.otp):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired OTP",
            )

        # Upsert user
        user = await self._user_repo.get_by_phone(payload.country_code, payload.phone_number)
        is_new_user = user is None
        if is_new_user:
            user = User(
                country_code=payload.country_code,
                phone_number=payload.phone_number,
                is_active=True,
                is_profile_complete=False,
            )
            await self._user_repo.create(user)
            log.info("New user registered", country_code=payload.country_code, phone_number=payload.phone_number)
        elif not user.is_active:
            log.warning("Login blocked — account is deactivated", user_id=str(user.id))
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is deactivated",
            )
        else:
            log.info("User logged in", user_id=str(user.id))

        return await self._issue_tokens(user, device_hint=payload.device_hint, is_new_user=is_new_user)

    async def refresh_access_token(self, raw_token: str) -> TokenResponse:
        """Validate a refresh token and issue a new access token + rotated refresh token."""
        db_token = await self._token_repo.get_by_token(raw_token)

        if db_token is None or not db_token.is_valid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token is invalid or expired",
            )

        user = await self._user_repo.get_by_id(db_token.user_id)
        if user is None or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive",
            )

        # Rotate: revoke old token and issue a new pair
        await self._token_repo.revoke(db_token)
        log.info("Access token refreshed", user_id=str(user.id))
        return await self._issue_tokens(user, device_hint=db_token.device_hint)

    async def logout(self, raw_token: str) -> None:
        """Revoke a specific refresh token (logout from one device)."""
        db_token = await self._token_repo.get_by_token(raw_token)
        if db_token:
            log.info("User logged out", user_id=str(db_token.user_id))
            await self._token_repo.delete(db_token)

    async def logout_all(self, user_id: UUID) -> None:
        """Revoke all refresh tokens for a user (logout from every device)."""
        await self._token_repo.revoke_all_for_user(user_id)
        log.info("User logged out from all devices", user_id=str(user_id))

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    async def _issue_tokens(self, user: User, *, device_hint: str | None = None, is_new_user: bool = False) -> TokenResponse:
        access_token = create_access_token(subject=user.id)
        raw_refresh = secrets.token_urlsafe(64)

        refresh_token_obj = RefreshToken(
            token=hash_token(raw_refresh),  # only the hash is stored
            user_id=user.id,
            device_hint=device_hint,
        )
        await self._token_repo.create(refresh_token_obj)

        return TokenResponse(
            access_token=access_token,
            refresh_token=raw_refresh,
            is_new_user=is_new_user,
            user=UserRead.model_validate(user),
        )
