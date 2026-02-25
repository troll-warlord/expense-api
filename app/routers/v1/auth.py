from fastapi import APIRouter, Depends, Request, status

from app.core.dependencies import CurrentUser, DBSession
from app.core.rate_limit import limiter
from app.schemas.auth import (
    LogoutRequest,
    RefreshTokenRequest,
    RequestOTPRequest,
    RequestOTPResponse,
    TokenResponse,
    VerifyOTPRequest,
)
from app.schemas.common import ResponseWrapper
from app.services.auth import AuthService

router = APIRouter(prefix="/auth", tags=["Auth"])


def _auth_service(db: DBSession) -> AuthService:
    return AuthService(db)


AuthServiceDep = Depends(_auth_service)


@router.post("/request-otp", response_model=ResponseWrapper[RequestOTPResponse], status_code=status.HTTP_200_OK)
@limiter.limit("5/minute")
async def request_otp(request: Request, payload: RequestOTPRequest, service: AuthService = AuthServiceDep):
    data = await service.request_otp(payload.email)
    return ResponseWrapper.ok(data=data, message="OTP sent successfully")


@router.post("/verify-otp", response_model=ResponseWrapper[TokenResponse], status_code=status.HTTP_200_OK)
async def verify_otp(payload: VerifyOTPRequest, service: AuthService = AuthServiceDep):
    data = await service.verify_otp_and_login(payload)
    return ResponseWrapper.ok(data=data, message="Login successful")


@router.post("/refresh", response_model=ResponseWrapper[TokenResponse], status_code=status.HTTP_200_OK)
async def refresh_token(payload: RefreshTokenRequest, service: AuthService = AuthServiceDep):
    data = await service.refresh_access_token(payload.refresh_token)
    return ResponseWrapper.ok(data=data, message="Token refreshed")


@router.post("/logout", response_model=ResponseWrapper[None], status_code=status.HTTP_200_OK)
async def logout(payload: LogoutRequest, service: AuthService = AuthServiceDep):
    await service.logout(payload.refresh_token)
    return ResponseWrapper.ok(message="Logged out successfully")


@router.delete(
    "/sessions",
    response_model=ResponseWrapper[None],
    status_code=status.HTTP_200_OK,
    summary="Logout from all devices",
    description="Revokes every active refresh token for the authenticated user.",
)
async def logout_all(current_user: CurrentUser, service: AuthService = AuthServiceDep):
    await service.logout_all(current_user.id)
    return ResponseWrapper.ok(message="Logged out from all devices")
