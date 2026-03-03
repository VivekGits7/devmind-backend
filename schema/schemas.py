from pydantic import BaseModel, Field, ConfigDict, field_validator, EmailStr
from typing import Optional

from schema.response import BaseResponse


# ==================== AUTH REQUEST SCHEMAS ====================


class SendOTPRequest(BaseModel):
    """Request body for sending OTP."""
    email: EmailStr = Field(
        ...,
        description="User's email address",
        examples=["john@example.com"],
    )


class VerifyOTPRequest(BaseModel):
    """Request body for verifying OTP."""
    email: EmailStr = Field(
        ...,
        description="User's email address",
        examples=["john@example.com"],
    )
    otp: str = Field(
        ...,
        min_length=6,
        max_length=6,
        description="6-digit OTP code",
        examples=["123456"],
    )


class SignupRequest(BaseModel):
    """Request body for user signup."""
    full_name: str = Field(
        ...,
        min_length=2,
        max_length=255,
        description="User's full name",
        examples=["John Doe"],
    )
    email: EmailStr = Field(
        ...,
        description="User's email address",
        examples=["john@example.com"],
    )
    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="Password (min 8 characters)",
        examples=["SecureP@ss123"],
    )
    phone_number: Optional[str] = Field(
        None,
        max_length=20,
        description="User's phone number",
        examples=["+1234567890"],
    )
    avatar_url: Optional[str] = Field(
        None,
        description="URL to user's avatar image",
        examples=["https://example.com/avatar.jpg"],
    )

    @field_validator("full_name")
    @classmethod
    def validate_full_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Name cannot be empty")
        return v


class SetPasswordRequest(BaseModel):
    """Request body for setting new password (forgot password flow)."""
    email: EmailStr = Field(
        ...,
        description="User's email address",
        examples=["john@example.com"],
    )
    new_password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="New password (min 8 characters)",
        examples=["NewSecureP@ss123"],
    )
    confirm_new_password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="Confirm new password (must match new_password)",
        examples=["NewSecureP@ss123"],
    )


class UpdateProfileRequest(BaseModel):
    """Request body for updating user profile."""
    full_name: Optional[str] = Field(
        None,
        min_length=2,
        max_length=255,
        description="Updated full name",
        examples=["John Doe"],
    )
    phone_number: Optional[str] = Field(
        None,
        max_length=20,
        description="Updated phone number",
        examples=["+1234567890"],
    )
    avatar_url: Optional[str] = Field(
        None,
        description="Updated avatar URL",
        examples=["https://example.com/avatar.jpg"],
    )


# ==================== AUTH RESPONSE DATA MODELS ====================


class UserProfile(BaseModel):
    """Typed user profile data model."""
    user_id: str = Field(
        ...,
        description="Unique UUID of the user",
        examples=["c9636f46-1080-4729-8f88-d2acd16fcfe7"],
    )
    full_name: str = Field(
        ...,
        description="User's full name",
        examples=["John Doe"],
    )
    email: str = Field(
        ...,
        description="User's email address",
        examples=["john@example.com"],
    )
    phone_number: Optional[str] = Field(
        None,
        description="User's phone number",
        examples=["+1234567890"],
    )
    avatar_url: Optional[str] = Field(
        None,
        description="URL to user's avatar image",
        examples=["https://example.com/avatar.jpg"],
    )
    is_verified: bool = Field(
        ...,
        description="Whether the user's email is verified",
        examples=[True],
    )
    created_at: Optional[str] = Field(
        None,
        description="ISO 8601 timestamp of account creation",
        examples=["2025-01-15T10:30:00"],
    )
    updated_at: Optional[str] = Field(
        None,
        description="ISO 8601 timestamp of last update",
        examples=["2025-01-15T10:30:00"],
    )
    last_login_at: Optional[str] = Field(
        None,
        description="ISO 8601 timestamp of last login",
        examples=["2025-01-15T10:30:00"],
    )


# ==================== AUTH RESPONSE SCHEMAS ====================


class SendOTPResponse(BaseResponse):
    """Response returned after sending OTP."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": True,
                "message": "OTP sent successfully",
            }
        }
    )


class VerifyOTPResponse(BaseResponse):
    """Response returned after verifying OTP."""
    is_verified: bool = Field(
        ...,
        description="Whether the OTP was verified successfully",
        examples=[True],
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": True,
                "message": "OTP verified successfully",
                "is_verified": True,
            }
        }
    )


class SignupResponse(BaseModel):
    """Response returned after successful signup."""
    success: bool = Field(default=True, description="Whether signup was successful")
    message: str = Field(..., description="Signup result message", examples=["Signup successful"])
    access_token: str = Field(..., description="JWT access token", examples=["eyJhbGciOiJIUzI1NiIs..."])
    token_type: str = Field(default="bearer", description="Token type", examples=["bearer"])
    user: UserProfile = Field(..., description="User profile data")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": True,
                "message": "Signup successful",
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "user": {
                    "user_id": "c9636f46-1080-4729-8f88-d2acd16fcfe7",
                    "full_name": "John Doe",
                    "email": "john@example.com",
                    "phone_number": "+1234567890",
                    "avatar_url": None,
                    "is_verified": True,
                    "created_at": "2025-01-15T10:30:00",
                    "updated_at": "2025-01-15T10:30:00",
                    "last_login_at": "2025-01-15T10:30:00",
                },
            }
        }
    )


class LoginResponse(BaseModel):
    """Response returned after successful login."""
    success: bool = Field(default=True, description="Whether login was successful")
    message: str = Field(..., description="Login result message", examples=["Login successful"])
    access_token: str = Field(..., description="JWT access token", examples=["eyJhbGciOiJIUzI1NiIs..."])
    token_type: str = Field(default="bearer", description="Token type", examples=["bearer"])
    user: UserProfile = Field(..., description="User profile data")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": True,
                "message": "Login successful",
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "user": {
                    "user_id": "c9636f46-1080-4729-8f88-d2acd16fcfe7",
                    "full_name": "John Doe",
                    "email": "john@example.com",
                    "phone_number": "+1234567890",
                    "avatar_url": None,
                    "is_verified": True,
                    "created_at": "2025-01-15T10:30:00",
                    "updated_at": "2025-01-15T10:30:00",
                    "last_login_at": "2025-01-15T10:30:00",
                },
            }
        }
    )


class SetPasswordResponse(BaseResponse):
    """Response returned after setting new password."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": True,
                "message": "Password set successful. You can now login with your new password.",
            }
        }
    )


class ProfileResponse(BaseResponse):
    """Response returned for user profile retrieval."""
    user: UserProfile = Field(..., description="User profile data")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": True,
                "message": "Profile retrieved successfully",
                "user": {
                    "user_id": "c9636f46-1080-4729-8f88-d2acd16fcfe7",
                    "full_name": "John Doe",
                    "email": "john@example.com",
                    "phone_number": "+1234567890",
                    "avatar_url": None,
                    "is_verified": True,
                    "created_at": "2025-01-15T10:30:00",
                    "updated_at": "2025-01-15T10:30:00",
                    "last_login_at": "2025-01-15T10:30:00",
                },
            }
        }
    )


class UpdateProfileResponse(BaseResponse):
    """Response returned after updating user profile."""
    user: UserProfile = Field(..., description="Updated user profile data")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": True,
                "message": "Profile updated successfully",
                "user": {
                    "user_id": "c9636f46-1080-4729-8f88-d2acd16fcfe7",
                    "full_name": "John Doe",
                    "email": "john@example.com",
                    "phone_number": "+1234567890",
                    "avatar_url": "https://example.com/avatar.jpg",
                    "is_verified": True,
                    "created_at": "2025-01-15T10:30:00",
                    "updated_at": "2025-01-15T11:00:00",
                    "last_login_at": "2025-01-15T10:30:00",
                },
            }
        }
    )
