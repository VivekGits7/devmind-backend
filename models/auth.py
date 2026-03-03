import uuid
import secrets
import string
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext

from config import settings
from services.database import execute_query, execute_query_one, execute_command, execute_command_with_return

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme — tokenUrl MUST match the login endpoint path
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")


class User:
    """User model for authentication and profile management."""

    def __init__(self, **kwargs):
        self.user_id = kwargs.get("user_id")
        self.full_name = kwargs.get("full_name")
        self.email = kwargs.get("email")
        self.phone_number = kwargs.get("phone_number")
        self.avatar_url = kwargs.get("avatar_url")
        self.password_hash = kwargs.get("password_hash")
        # OTP fields
        self.otp = kwargs.get("otp")
        self.otp_created_at = kwargs.get("otp_created_at")
        self.is_verified = kwargs.get("is_verified", False)
        # Timestamps
        self.created_at = kwargs.get("created_at")
        self.updated_at = kwargs.get("updated_at")
        self.last_login_at = kwargs.get("last_login_at")

    # ==================== CLASS METHODS (FINDERS) ====================

    @classmethod
    async def find_by_id(cls, user_id: str) -> Optional["User"]:
        """Find user by ID."""
        query = "SELECT * FROM users WHERE user_id = $1"
        result = await execute_query_one(query, uuid.UUID(user_id))
        return cls(**dict(result)) if result else None

    @classmethod
    async def find_by_email(cls, email: str) -> Optional["User"]:
        """Find user by email (case-insensitive)."""
        query = "SELECT * FROM users WHERE LOWER(email) = LOWER($1)"
        result = await execute_query_one(query, email)
        return cls(**dict(result)) if result else None

    @classmethod
    async def create(
        cls,
        full_name: str,
        email: str,
        password_hash: str,
        phone_number: Optional[str] = None,
        avatar_url: Optional[str] = None,
    ) -> Optional["User"]:
        """Create a new user."""
        query = """
            INSERT INTO users (
                user_id, full_name, email, password_hash, phone_number,
                avatar_url, created_at, updated_at
            ) VALUES ($1, $2, $3, $4, $5, $6, NOW(), NOW())
            RETURNING *
        """
        result = await execute_command_with_return(
            query, uuid.uuid4(), full_name, email, password_hash, phone_number, avatar_url
        )
        return cls(**dict(result)) if result else None

    @classmethod
    def generate_otp(cls, length: int = 6) -> str:
        """Generate a numeric OTP."""
        return "".join(secrets.choice(string.digits) for _ in range(length))

    # ==================== INSTANCE METHODS ====================

    def is_registered(self) -> bool:
        """Check if user has completed signup (has a password set)."""
        return bool(self.password_hash and self.password_hash != "")

    async def save(self) -> bool:
        """Save/update user profile fields."""
        query = """
            UPDATE users SET
                full_name = $2, email = $3, phone_number = $4,
                avatar_url = $5, updated_at = NOW()
            WHERE user_id = $1
        """
        await execute_command(query, self.user_id, self.full_name, self.email, self.phone_number, self.avatar_url)
        return True

    async def set_password(self, password_hash: str) -> bool:
        """Update user password."""
        query = "UPDATE users SET password_hash = $2, updated_at = NOW() WHERE user_id = $1"
        await execute_command(query, self.user_id, password_hash)
        self.password_hash = password_hash
        return True

    async def set_otp(self, otp: str) -> bool:
        """Set OTP and reset verification status."""
        query = (
            "UPDATE users SET otp = $2, otp_created_at = NOW(), "
            "is_verified = FALSE, updated_at = NOW() WHERE user_id = $1"
        )
        await execute_command(query, self.user_id, otp)
        self.otp = otp
        self.is_verified = False
        return True

    async def clear_otp(self) -> bool:
        """Clear OTP after successful verification/signup."""
        query = (
            "UPDATE users SET otp = NULL, otp_created_at = NULL, "
            "is_verified = FALSE, updated_at = NOW() WHERE user_id = $1"
        )
        await execute_command(query, self.user_id)
        self.otp = None
        self.otp_created_at = None
        self.is_verified = False
        return True

    async def set_otp_verified(self) -> bool:
        """Mark OTP as verified."""
        query = "UPDATE users SET is_verified = TRUE, updated_at = NOW() WHERE user_id = $1"
        await execute_command(query, self.user_id)
        self.is_verified = True
        return True

    async def is_otp_expired(self, minutes: Optional[int] = None) -> bool:
        """Check if OTP has expired (calculated in database to avoid timezone issues)."""
        if minutes is None:
            minutes = settings.OTP_EXPIRE_MINUTES
        query = """
            SELECT CASE
                WHEN otp_created_at IS NULL THEN TRUE
                WHEN NOW() - otp_created_at > INTERVAL '1 minute' * $2 THEN TRUE
                ELSE FALSE
            END as expired
            FROM users WHERE user_id = $1
        """
        result = await execute_query_one(query, self.user_id, minutes)
        return result["expired"] if result else True

    async def update_last_login(self) -> bool:
        """Update last login timestamp."""
        query = "UPDATE users SET last_login_at = NOW(), updated_at = NOW() WHERE user_id = $1"
        await execute_command(query, self.user_id)
        self.last_login_at = datetime.now()
        return True

    async def delete(self) -> bool:
        """Delete the user record."""
        query = "DELETE FROM users WHERE user_id = $1"
        await execute_command(query, self.user_id)
        return True

    # ==================== SERIALIZATION ====================

    def to_dict(self) -> Dict[str, Any]:
        """Full user representation (internal use)."""
        return {
            "user_id": str(self.user_id) if self.user_id else None,
            "full_name": self.full_name,
            "email": self.email,
            "phone_number": self.phone_number,
            "avatar_url": self.avatar_url,
            "is_verified": self.is_verified,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "last_login_at": self.last_login_at.isoformat() if self.last_login_at else None,
        }

    def to_public_dict(self) -> Dict[str, Any]:
        """Public representation (no sensitive fields like password_hash, otp)."""
        return {
            "user_id": str(self.user_id) if self.user_id else None,
            "full_name": self.full_name,
            "email": self.email,
            "phone_number": self.phone_number,
            "avatar_url": self.avatar_url,
            "is_verified": self.is_verified,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


# ==================== AUTHENTICATION HELPERS ====================


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    if len(plain_password.encode("utf-8")) > 72:
        while len(plain_password.encode("utf-8")) > 72:
            plain_password = plain_password[:-1]
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password (truncates to 72 bytes for bcrypt compatibility)."""
    password_bytes = password.encode("utf-8")[:72]
    password = password_bytes.decode("utf-8", errors="ignore")
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    expire = datetime.now() + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    """FastAPI dependency — get current user from JWT token."""
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        email = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = await User.find_by_email(email)
    if user is None:
        raise credentials_exception
    return user
