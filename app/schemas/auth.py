from pydantic import BaseModel, Field

from app.schemas.user import UserRead


class RequestOTPRequest(BaseModel):
    country_code: str = Field(
        default="+91",
        min_length=2,
        max_length=10,
        pattern=r"^\+\d{1,3}$",
        examples=["+91"],
        description="E.164 country code, e.g. +91, +1",
    )
    phone_number: str = Field(
        ...,
        min_length=6,
        max_length=15,
        pattern=r"^\d{6,15}$",
        examples=["9876543210"],
        description="Local phone number without country code, digits only",
    )


class RequestOTPResponse(BaseModel):
    country_code: str
    phone_number: str
    message: str = "OTP sent successfully"


class VerifyOTPRequest(BaseModel):
    country_code: str = Field(
        default="+91",
        min_length=2,
        max_length=10,
        pattern=r"^\+\d{1,3}$",
    )
    phone_number: str = Field(..., min_length=6, max_length=15, pattern=r"^\d{6,15}$")
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
