from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Request, status
from fastapi.security import OAuth2PasswordRequestForm

from models.auth import (
    User,
    verify_password,
    get_password_hash,
    create_access_token,
    get_current_user,
)
from services.email_service import send_otp
from limiter import limiter
from logger import get_logger
from error import (
    AppException,
    UnauthorizedException,
    NotFoundException,
    ConflictException,
    BadRequestException,
)
from schema.response import (
    COMMON_ERROR_RESPONSES,
    BadRequestResponse,
    ConflictResponse,
    NotFoundResponse,
)
from schema.schemas import (
    SignupRequest,
    SignupResponse,
    LoginResponse,
    SendOTPRequest,
    SendOTPResponse,
    VerifyOTPRequest,
    VerifyOTPResponse,
    SetPasswordRequest,
    SetPasswordResponse,
    UpdateProfileRequest,
    UpdateProfileResponse,
    ProfileResponse,
    UserProfile,
)

logger = get_logger(__name__)

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


# ==================== HELPER ====================


def _build_user_profile(user: User) -> UserProfile:
    """Build a UserProfile Pydantic model from a User instance."""
    return UserProfile(
        user_id=str(user.user_id),
        full_name=user.full_name,
        email=user.email,
        phone_number=user.phone_number,
        avatar_url=user.avatar_url,
        is_verified=user.is_verified,
        created_at=user.created_at.isoformat() if user.created_at else None,
        updated_at=user.updated_at.isoformat() if user.updated_at else None,
        last_login_at=user.last_login_at.isoformat() if user.last_login_at else None,
    )


# ==================== ENDPOINTS ====================


@router.post(
    "/signup",
    response_model=SignupResponse,
    status_code=status.HTTP_201_CREATED,
    summary="User signup",
    responses={
        **COMMON_ERROR_RESPONSES,
        201: {"model": SignupResponse, "description": "Signup successful"},
        400: {"model": BadRequestResponse, "description": "Invalid input data"},
        409: {"model": ConflictResponse, "description": "Email already registered"},
    },
)
@limiter.limit("30/minute")
async def signup(request: Request, signup_data: SignupRequest) -> SignupResponse:
    """
    Register a new user account.

    - **full_name** (str, required): User's full name (2-255 chars)
    - **email** (str, required): Unique email address
    - **password** (str, required): Password (min 8 characters)
    - **phone_number** (str, optional): Phone number (max 20 chars)
    - **avatar_url** (str, optional): URL to avatar image
    - Returns access token and user profile data
    """
    try:
        user = await User.find_by_email(signup_data.email)

        if user and user.is_registered():
            raise ConflictException("Email already registered. Please login.")

        password_hash = get_password_hash(signup_data.password)

        if user:
            # Complete registration for existing temp user (from OTP flow)
            user.full_name = signup_data.full_name
            if signup_data.phone_number:
                user.phone_number = signup_data.phone_number
            if signup_data.avatar_url:
                user.avatar_url = signup_data.avatar_url
            await user.save()
            await user.set_password(password_hash)
            await user.clear_otp()
        else:
            # Create new user directly
            user = await User.create(
                full_name=signup_data.full_name,
                email=signup_data.email,
                password_hash=password_hash,
            )
            if not user:
                raise HTTPException(status_code=500, detail="Failed to create user")
            if signup_data.phone_number:
                user.phone_number = signup_data.phone_number
            if signup_data.avatar_url:
                user.avatar_url = signup_data.avatar_url
            await user.save()

        await user.update_last_login()
        access_token = create_access_token(data={"sub": user.email})

        return SignupResponse(
            success=True,
            message="Signup successful",
            access_token=access_token,
            token_type="bearer",
            user=_build_user_profile(user),
        )

    except (HTTPException, AppException):
        raise
    except Exception as e:
        logger.error(f"Signup error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post(
    "/login",
    response_model=LoginResponse,
    summary="User login",
    responses={
        **COMMON_ERROR_RESPONSES,
        200: {"model": LoginResponse, "description": "Login successful, returns JWT token"},
        400: {"model": BadRequestResponse, "description": "Invalid credentials"},
    },
)
@limiter.limit("30/minute")
async def login(request: Request, form_data: OAuth2PasswordRequestForm = Depends()) -> LoginResponse:
    """
    Authenticate user with email and password.

    Uses OAuth2 form login (Swagger Authorize button compatible).
    - **username**: User's email address
    - **password**: User's password
    """
    try:
        user = await User.find_by_email(form_data.username)
        if not user:
            raise UnauthorizedException("Invalid email or password")

        if not verify_password(form_data.password, user.password_hash):
            raise UnauthorizedException("Invalid email or password")

        await user.update_last_login()
        access_token = create_access_token(data={"sub": user.email})

        return LoginResponse(
            success=True,
            message="Login successful",
            access_token=access_token,
            token_type="bearer",
            user=_build_user_profile(user),
        )

    except (HTTPException, AppException):
        raise
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post(
    "/send-otp",
    response_model=SendOTPResponse,
    summary="Send OTP",
    responses={
        **COMMON_ERROR_RESPONSES,
        200: {"model": SendOTPResponse, "description": "OTP sent successfully"},
        404: {"model": NotFoundResponse, "description": "User not found"},
    },
)
@limiter.limit("30/minute")
async def send_otp_endpoint(
    request: Request,
    otp_data: SendOTPRequest,
    background_tasks: BackgroundTasks,
) -> SendOTPResponse:
    """
    Send OTP to user's email.

    - **email** (str, required): User's registered email address
    - Works for both forgot password and email verification
    """
    try:
        user = await User.find_by_email(otp_data.email)
        if not user:
            raise NotFoundException("User not found")

        otp = User.generate_otp()
        await user.set_otp(otp)

        background_tasks.add_task(send_otp, otp_data.email, otp)

        return SendOTPResponse(success=True, message="OTP sent successfully")

    except (HTTPException, AppException):
        raise
    except Exception as e:
        logger.error(f"Send OTP error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post(
    "/verify-otp",
    response_model=VerifyOTPResponse,
    summary="Verify OTP",
    responses={
        **COMMON_ERROR_RESPONSES,
        200: {"model": VerifyOTPResponse, "description": "OTP verified successfully"},
    },
)
@limiter.limit("30/minute")
async def verify_otp(request: Request, verify_data: VerifyOTPRequest) -> VerifyOTPResponse:
    """
    Verify OTP sent to user's email.

    - **email** (str, required): User's email address
    - **otp** (str, required): 6-digit OTP code
    """
    try:
        user = await User.find_by_email(verify_data.email)
        if not user:
            raise UnauthorizedException("Invalid email or OTP")

        if not user.otp:
            raise UnauthorizedException("Invalid email or OTP")

        if await user.is_otp_expired():
            raise UnauthorizedException("OTP has expired")

        if user.otp != verify_data.otp:
            raise UnauthorizedException("Invalid email or OTP")

        await user.set_otp_verified()

        return VerifyOTPResponse(success=True, message="OTP verified successfully", is_verified=True)

    except (HTTPException, AppException):
        raise
    except Exception as e:
        logger.error(f"OTP verification error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post(
    "/set-password",
    response_model=SetPasswordResponse,
    summary="Set new password",
    responses={
        **COMMON_ERROR_RESPONSES,
        200: {"model": SetPasswordResponse, "description": "Password set successfully"},
        400: {"model": BadRequestResponse, "description": "Passwords do not match"},
    },
)
@limiter.limit("30/minute")
async def set_password(request: Request, password_data: SetPasswordRequest) -> SetPasswordResponse:
    """
    Set new password after OTP verification (forgot password flow).

    - **email** (str, required): User's email address
    - **new_password** (str, required): New password (min 8 characters)
    - **confirm_new_password** (str, required): Must match new_password
    - Note: Must call /verify-otp endpoint first
    """
    try:
        user = await User.find_by_email(password_data.email)
        if not user:
            raise NotFoundException("User not found")

        if password_data.new_password != password_data.confirm_new_password:
            raise BadRequestException("Passwords do not match")

        password_hash = get_password_hash(password_data.new_password)
        await user.set_password(password_hash)
        await user.clear_otp()

        return SetPasswordResponse(
            success=True,
            message="Password set successful. You can now login with your new password.",
        )

    except (HTTPException, AppException):
        raise
    except Exception as e:
        logger.error(f"Set password error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get(
    "/profile",
    response_model=ProfileResponse,
    summary="Get user profile",
    responses={
        **COMMON_ERROR_RESPONSES,
        200: {"model": ProfileResponse, "description": "User profile retrieved"},
    },
)
@limiter.limit("30/minute")
async def get_profile(request: Request, current_user: User = Depends(get_current_user)) -> ProfileResponse:
    """Get authenticated user's profile information."""
    return ProfileResponse(
        success=True,
        message="Profile retrieved successfully",
        user=_build_user_profile(current_user),
    )


@router.put(
    "/profile",
    response_model=UpdateProfileResponse,
    summary="Update user profile",
    responses={
        **COMMON_ERROR_RESPONSES,
        200: {"model": UpdateProfileResponse, "description": "Profile updated successfully"},
        400: {"model": BadRequestResponse, "description": "Invalid input data"},
    },
)
@limiter.limit("30/minute")
async def update_profile(
    request: Request,
    update_data: UpdateProfileRequest,
    current_user: User = Depends(get_current_user),
) -> UpdateProfileResponse:
    """
    Update authenticated user's profile.

    - **full_name** (str, optional): 2-255 characters
    - **phone_number** (str, optional): Up to 20 characters
    - **avatar_url** (str, optional): URL to avatar image
    """
    try:
        if update_data.full_name is not None:
            current_user.full_name = update_data.full_name
        if update_data.phone_number is not None:
            current_user.phone_number = update_data.phone_number
        if update_data.avatar_url is not None:
            current_user.avatar_url = update_data.avatar_url

        await current_user.save()

        return UpdateProfileResponse(
            success=True,
            message="Profile updated successfully",
            user=_build_user_profile(current_user),
        )

    except (HTTPException, AppException):
        raise
    except Exception as e:
        logger.error(f"Profile update error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
