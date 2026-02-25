from pydantic import BaseModel, EmailStr, Field

from app.schemas.user import UserRead


class RequestOTPRequest(BaseModel):
    email: EmailStr = Field(
        ...,
        examples=["user@example.com"],
        description="Email address to send the OTP to",
    )


class RequestOTPResponse(BaseModel):
    email: str
    message: str = "OTP sent successfully"


class VerifyOTPRequest(BaseModel):
    email: EmailStr = Field(..., description="Email address used to request the OTP")
    otp: str = Field(..., min_length=6, max_length=6)
    device_hint: str | None = Field(
        default=None,
        max_length=255,
        description="Optional device description, e.g. 'iPhone 14 / iOS 17'",
    )


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    is_new_user: bool = False
    """True when the user was created for the first time during this verification."""
    user: UserRead


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    refresh_token: str
